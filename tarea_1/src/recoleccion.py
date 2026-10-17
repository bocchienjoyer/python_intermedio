"""Recolección pausada, comprobable y reanudable de La República."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
import gzip
import hashlib
import json
from pathlib import Path
import random
import re
import time
import unicodedata
from urllib.parse import urljoin, urlsplit, urlunsplit
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
import pandas as pd
from protego import Protego
import requests

ROOT = Path(__file__).resolve().parents[1]
PERU = timezone(timedelta(hours=-5))
BASE = "https://larepublica.pe"
USER_AGENT = "QLAB-Noticias-Student/1.0 (+https://github.com/bocchienjoyer/python_intermedio)"
COLUMNS = ["titular", "bajada", "medio", "seccion_original", "url", "fecha", "etiqueta"]
SECTION_MAP = {
    "politica": "politica",
    "economia": "economia",
    "deportes": "deportes",
    "ciencia": "ciencia_tecnologia",
    "tecnologia": "ciencia_tecnologia",
}
CATEGORIES = list(dict.fromkeys(SECTION_MAP.values()))


def now() -> str:
    return datetime.now(PERU).isoformat(timespec="seconds")


def clean_text(value) -> str:
    return " ".join(BeautifulSoup(str(value or ""), "html.parser").get_text(" ").split())


def canonical(url: str) -> str:
    parts = urlsplit(urljoin(BASE, url.strip()))
    return urlunsplit(("https", parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def section_key(url: str) -> str:
    return urlsplit(url).path.strip("/").split("/")[0]


def title_key(title: str) -> str:
    return re.sub(r"[^\w\s]", "", unicodedata.normalize("NFKC", title).casefold()).strip()


class PoliteClient:
    """Una solicitud a la vez, caché local y robots RFC 9309 con comodines."""

    def __init__(self, root: Path = ROOT, offline: bool = False):
        self.raw = root / "datos" / "raw"
        self.raw.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.offline = offline
        self.last_request = 0.0
        self.robots = None
        self.events = []
        self.manifest = self.raw / "solicitudes.jsonl"
        robots = self.get(BASE + "/robots.txt", bootstrap=True)
        self.robots = Protego.parse(robots.decode("utf-8", errors="replace"))

    def log(self, event):
        self.events.append(event)
        with self.manifest.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")

    def get(self, url: str, bootstrap: bool = False, _redirects: int = 0) -> bytes:
        if _redirects > 5:
            raise ValueError("Demasiadas redirecciones")
        url = canonical(url)
        if urlsplit(url).netloc != "larepublica.pe":
            raise ValueError("Fuera del dominio autorizado: " + url)
        if not bootstrap and not self.robots.can_fetch(url, USER_AGENT):
            self.log({"fecha_descarga": now(), "url": url, "estado": "robots_denegado"})
            raise PermissionError("robots.txt no permite: " + url)
        digest = hashlib.sha256(url.encode()).hexdigest()[:24]
        suffix = ".html.gz" if not url.endswith((".xml", ".txt")) else Path(urlsplit(url).path).suffix
        cache = self.raw / (digest + suffix)
        meta_path = self.raw / (digest + ".meta.json")
        if cache.exists() and meta_path.exists():
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            if metadata.get("status") == 200:
                return gzip.decompress(cache.read_bytes()) if suffix.endswith(".gz") else cache.read_bytes()
        if self.offline:
            raise FileNotFoundError("Sin caché, modo offline: " + url)
        for attempt in range(2):  # una solicitud inicial y como máximo un reintento
            pause = max(1.5, self.robots.crawl_delay(USER_AGENT) or 0) if self.robots else 1.5
            time.sleep(max(0, self.last_request + pause + random.uniform(0, 0.5) - time.monotonic()))
            self.last_request = time.monotonic()
            try:
                response = self.session.get(url, timeout=(15, 35), allow_redirects=False)
                event = {"fecha_descarga": now(), "url": url, "status": response.status_code,
                         "intento": attempt + 1, "archivo": cache.name,
                         "content_type": response.headers.get("Content-Type", "")}
                self.log(event)
                if response.is_redirect:
                    target = canonical(urljoin(url, response.headers["Location"]))
                    if target == url:
                        raise ValueError("Redirección circular")
                    return self.get(target, bootstrap=bootstrap, _redirects=_redirects + 1)
                response.raise_for_status()
                cache.write_bytes(gzip.compress(response.content) if suffix.endswith(".gz") else response.content)
                meta_path.write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8")
                return response.content
            except requests.RequestException as error:
                if isinstance(error, requests.HTTPError) and response.status_code not in (429, 500, 502, 503, 504):
                    raise
                if attempt:
                    raise
                # Respetar Retry-After cuando sea numérico, además de la pausa ordinaria.
                wait = response.headers.get("Retry-After", "") if "response" in locals() else ""
                if wait.isdigit():
                    time.sleep(min(int(wait), 60))
        raise RuntimeError("Solicitud no completada")


def rss_items(content: bytes) -> list[dict]:
    items = []
    for item in ET.fromstring(content).findall(".//item"):
        url = canonical(item.findtext("link", ""))
        section = section_key(url)
        if section not in SECTION_MAP:
            continue
        categories = [c for c in item.findall("category") if "/tag/" not in c.get("domain", "")]
        label = clean_text(categories[0].text) if categories else section
        date = parsedate_to_datetime(item.findtext("pubDate", "")).astimezone(PERU).date().isoformat()
        items.append({"titular": clean_text(item.findtext("title")),
                      "bajada": clean_text(item.findtext("description")), "medio": "La Republica",
                      "seccion_original": label, "url": url, "fecha": date,
                      "etiqueta": SECTION_MAP[section], "origen": "rss"})
    return items


def sitemap_items(content: bytes) -> list[str]:
    root = ET.fromstring(content)
    return [canonical(node.text) for node in root.findall("{*}url/{*}loc") if node.text]


def article_links(content: bytes) -> list[str]:
    """Enlaces públicos reales, sin construir paginación ni endpoints internos."""
    links = []
    for anchor in BeautifulSoup(content, "html.parser").find_all("a", href=True):
        link = canonical(anchor["href"])
        if (urlsplit(link).netloc == "larepublica.pe" and section_key(link) in SECTION_MAP
                and re.search(r"/20\d{2}/\d{2}/\d{2}/", link) and link not in links):
            links.append(link)
    return links


def article_metadata(content: bytes, url: str) -> dict:
    soup = BeautifulSoup(content, "html.parser")
    objects = []
    def walk(value):
        if isinstance(value, dict):
            objects.append(value)
            for child in value.values():
                if isinstance(child, (dict, list)):
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            walk(json.loads(script.string or script.get_text()))
        except (ValueError, TypeError):
            continue
    articles = [obj for obj in objects if any(t in str(obj.get("@type", "")) for t in ("NewsArticle", "Article", "Reportage"))]
    article = max(articles, key=lambda x: bool(x.get("headline")) + bool(x.get("datePublished")), default={})
    def meta(*names):
        for name in names:
            tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
            if tag and tag.get("content"):
                return tag["content"]
        return ""
    heading = soup.find("h1")
    title = clean_text(article.get("headline") or meta("og:title") or (heading.get_text() if heading else ""))
    summary = clean_text(article.get("description") or meta("og:description", "description"))
    date = article.get("datePublished") or meta("article:published_time", "datePublished")
    if not date:
        match = re.search(r"/(20\d{2})/(\d{2})/(\d{2})/", url)
        date = "-".join(match.groups()) if match else ""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(date)):
        date = pd.to_datetime(date, errors="coerce", utc=True)
        date = date.tz_convert(PERU).date().isoformat() if not pd.isna(date) else ""
    section = article.get("articleSection") or meta("article:section") or section_key(url)
    if isinstance(section, list):
        section = section[0] if section else section_key(url)
    return {"titular": title, "bajada": summary, "medio": "La Republica",
            "seccion_original": clean_text(section), "url": canonical(url), "fecha": date,
            "etiqueta": SECTION_MAP.get(section_key(url), ""), "origen": "html_metadata"}


def discover(client: PoliteClient) -> tuple[list[dict], dict]:
    candidates = {}
    sources = {}
    discovery_discards = []
    for section in ("politica", "economia", "deportes", "ciencia"):
        url = f"{BASE}/rss/{section}.xml"
        rows = rss_items(client.get(url))
        sources[url] = len(rows)
        for row in rows:
            if row["url"] in candidates:
                discovery_discards.append({"url": row["url"], "fuente": url, "motivo": "url_repetida_descubrimiento"})
            candidates[row["url"]] = row
        # Los sitemaps sirven solo para descubrir enlaces, sin rutas de paginación restringidas.
        url = f"{BASE}/sitemap/{section}.xml"
        links = sitemap_items(client.get(url))
        sources[url] = len(links)
        print(json.dumps({"seccion": section, "rss": len(rows), "sitemap": len(links)}, ensure_ascii=False), flush=True)
        for link in links:
            if section_key(link) in SECTION_MAP:
                if link in candidates:
                    discovery_discards.append({"url": link, "fuente": url, "motivo": "url_repetida_descubrimiento"})
                candidates.setdefault(link, {"url": link, "etiqueta": SECTION_MAP[section_key(link)], "origen": "sitemap"})
            else:
                discovery_discards.append({"url": link, "fuente": url, "motivo": "seccion_fuera_de_alcance"})
    for section in SECTION_MAP:
        url = f"{BASE}/{section}"
        links = article_links(client.get(url))
        sources[url] = len(links)
        for link in links:
            candidates.setdefault(link, {"url": link, "etiqueta": SECTION_MAP[section_key(link)],
                                         "origen": "seccion_html", "descubierto_en": url})
    pd.DataFrame(discovery_discards, columns=["url", "fuente", "motivo"]).to_csv(
        ROOT / "datos" / "descartes_descubrimiento.csv", index=False, encoding="utf-8")
    return list(candidates.values()), sources


def collect(per_category: int = 100, offline: bool = False, pilot: bool = False):
    client = PoliteClient(offline=offline)
    candidates, sources = discover(client)
    out = ROOT / "datos"
    pd.DataFrame(candidates).to_csv(out / "candidatos.csv", index=False, encoding="utf-8")
    counts = Counter()
    rows, discarded, keys, mapping = [], [], [], set()
    known_urls = {row["url"] for row in candidates}
    processed = 0
    for candidate in candidates:
        category = candidate["etiqueta"]
        if counts[category] >= per_category:
            continue
        url = candidate["url"]
        processed += 1
        if processed > 1000:
            break
        try:
            # Incluso en RSS se comprueba el enlace y se respalda su HTML.
            content = client.get(url)
            # Ampliar el período con noticias relacionadas enlazadas por el propio medio.
            # Cada enlace se comprueba con robots antes de solicitarlo; límite global de 1.000 páginas.
            for link in article_links(content):
                if link not in known_urls and len(candidates) < 5000:
                    known_urls.add(link)
                    candidates.append({"url": link, "etiqueta": SECTION_MAP[section_key(link)],
                                       "origen": "enlace_relacionado", "descubierto_en": url})
            row = candidate if candidate.get("titular") and candidate.get("bajada") else article_metadata(content, url)
            if not row.get("titular"):
                raise ValueError("titular_vacio")
            if not row.get("bajada"):
                raise ValueError("bajada_ausente")
            if not row.get("fecha"):
                raise ValueError("fecha_ausente")
            if row["etiqueta"] not in CATEGORIES:
                raise ValueError("fuera_de_categorias")
            if row["fecha"] > datetime.now(PERU).date().isoformat():
                raise ValueError("fecha_futura")
            key = title_key(row["titular"])
            if key in keys:
                raise ValueError("titular_duplicado")
            if any(SequenceMatcher(None, key, other, autojunk=False).ratio() >= 0.95 for other in keys):
                raise ValueError("titular_casi_duplicado_095")
            mapping.add((section_key(url), row["seccion_original"], row["etiqueta"]))
            rows.append({column: row[column] for column in COLUMNS})
            keys.append(key)
            counts[category] += 1
            if counts[category] % 10 == 0:
                print(json.dumps({"categoria": category, "validas": counts[category], "total": len(rows)}, ensure_ascii=False), flush=True)
        except (requests.RequestException, ValueError, PermissionError, FileNotFoundError) as error:
            discarded.append({"url": url, "titular": candidate.get("titular", ""), "motivo": str(error)})
        if all(counts[c] >= per_category for c in CATEGORIES):
            break
    df = pd.DataFrame(rows, columns=COLUMNS).sort_values(["etiqueta", "fecha", "url"], ascending=[True, False, True])
    filename = "piloto.csv" if pilot else "noticias.csv"
    df.to_csv(out / filename, index=False, encoding="utf-8")
    pd.DataFrame(candidates).to_csv(out / "candidatos.csv", index=False, encoding="utf-8")
    pd.DataFrame(discarded, columns=["url", "titular", "motivo"]).to_csv(out / "descartes.csv", index=False, encoding="utf-8")
    pd.DataFrame(sorted(mapping), columns=["ruta_seccion", "seccion_original", "etiqueta"]).to_csv(out / "mapeo_secciones.csv", index=False, encoding="utf-8")
    summary = {"fecha_descarga": now(), "medio": "La Republica", "opcion": "A", "piloto": pilot,
               "objetivo_por_categoria": per_category, "filas": len(df), "columnas": COLUMNS,
               "por_categoria": dict(counts), "candidatos_unicos": len(candidates), "fuentes": sources,
               "descartes": dict(Counter(x["motivo"] for x in discarded)),
               "fecha_min": str(df.fecha.min()), "fecha_max": str(df.fecha.max()),
               "url_verificadas_http_200": len(df), "user_agent": USER_AGENT,
               "pausa_segundos": [1.5, 2.0], "max_reintentos": 1,
               "criterio_muestra": "RSS, sitemaps, secciones y enlaces públicos relacionados; cuota por categoría; no es muestra aleatoria del medio."}
    (out / ("resumen_piloto.json" if pilot else "resumen_recoleccion.json")).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    if any(counts[c] < per_category for c in CATEGORIES):
        raise RuntimeError("Cobertura insuficiente; revisar fuentes y descartes antes de dar por terminada la recolección.")
    return df, summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--por-categoria", type=int, default=100)
    parser.add_argument("--piloto", action="store_true")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    collect(args.por_categoria, args.offline, args.piloto)
