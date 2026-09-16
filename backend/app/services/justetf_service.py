"""Scraping "propre" de justETF.com pour la repartition geographique (par pays)
des ETF/fonds, donnee que Yahoo Finance/yfinance n'expose pas (voir profile.py).

Justetf n'a pas d'API publique documentee, mais la page profil (server-side,
Apache Wicket) contient un lien "Show more" qui declenche un appel AJAX
renvoyant un fragment HTML avec des attributs data-testid stables. On reproduit
ces deux requetes HTTP (pas de navigateur headless, pas d'execution JS) :

  1. GET /en/etf-profile.html?isin=... -> page HTML + chemin de l'appel AJAX
  2. GET <chemin AJAX>                 -> fragment HTML avec la table pays complete

Autorise par robots.txt (seuls /servlet/, /link/ et les recherches/watchlist
avec _wicket sont interdits ; etf-profile.html n'est pas concerne).
"""

import re
import time
from typing import Optional

from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests

_PROFILE_URL = "https://www.justetf.com/en/etf-profile.html"
_AJAX_PATH_RE = re.compile(r'"u":"(/en/etf-profile\.html\?[^"]*loadMoreCountries[^"]*)"')


def _extract_table_html(text: str, testid: str) -> Optional[str]:
    """Isole le `<table>...</table>` portant ce data-testid.

    La reponse AJAX Wicket est une enveloppe XML avec plusieurs fragments
    HTML encapsules dans des blocs CDATA imbriques ; un decoupage naif par
    regex sur "<![CDATA[ ... ]]>" capture le mauvais bloc des qu'il y a
    plusieurs composants. On isole donc directement la balise <table> via
    ses bornes textuelles, ce qui produit un HTML propre a parser.
    """
    marker = f'data-testid="{testid}"'
    idx = text.find(marker)
    if idx == -1:
        return None
    start = text.rfind("<table", 0, idx)
    end = text.find("</table>", idx)
    if start == -1 or end == -1:
        return None
    return text[start : end + len("</table>")]

_CACHE_TTL_SECONDS = 6 * 3600
_cache: dict[str, tuple[float, dict]] = {}


def _parse_country_table(html_fragment: str) -> dict:
    soup = BeautifulSoup(html_fragment, "html.parser")
    countries: dict[str, float] = {}

    for row in soup.select('[data-testid="etf-holdings_countries_row"]'):
        name_el = row.select_one('[data-testid="tl_etf-holdings_countries_value_name"]')
        pct_el = row.select_one('[data-testid="tl_etf-holdings_countries_value_percentage"]')
        if not name_el or not pct_el:
            continue

        name = name_el.get_text(strip=True)
        try:
            pct = float(pct_el.get_text(strip=True).replace("%", "").replace(",", ".")) / 100
        except ValueError:
            continue
        countries[name] = pct

    return countries


def _fetch_country_breakdown(isin: str) -> dict:
    source_url = f"{_PROFILE_URL}?isin={isin}"
    session = curl_requests.Session(impersonate="chrome")

    page = session.get(source_url, timeout=20)

    if page.status_code == 404:
        return {
            "isin": isin,
            "source": "justETF",
            "source_url": source_url,
            "countries": None,
            "note": "ETF introuvable sur justETF pour cet ISIN.",
        }
    page.raise_for_status()

    soup = BeautifulSoup(page.text, "html.parser")
    countries_table = soup.select_one('[data-testid="etf-holdings_countries_table"]')

    if countries_table is None:
        return {
            "isin": isin,
            "source": "justETF",
            "source_url": source_url,
            "countries": None,
            "note": (
                "Aucune repartition par pays publiee par justETF pour cet ISIN "
                "(couverture limitee aux ETF/fonds)."
            ),
        }

    countries = _parse_country_table(str(countries_table))

    # La table par defaut est tronquee (top ~4 pays + "Other") : on suit le
    # lien "Show more" (appel AJAX Wicket) pour recuperer la liste complete.
    match = _AJAX_PATH_RE.search(page.text)
    if match:
        ajax_path = match.group(1).replace("\\/", "/")
        try:
            ajax_response = session.get(
                f"https://www.justetf.com{ajax_path}",
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Wicket-Ajax": "true",
                    "Wicket-Ajax-BaseURL": f"en/etf-profile.html?isin={isin}",
                    "Referer": source_url,
                },
                timeout=20,
            )
            if ajax_response.ok:
                table_html = _extract_table_html(ajax_response.text, "etf-holdings_countries_table")
                if table_html:
                    expanded = _parse_country_table(table_html)
                    if expanded:
                        countries = expanded
        except Exception:
            pass  # on garde la table par defaut (top pays + "Other") si l'AJAX echoue

    return {
        "isin": isin,
        "source": "justETF",
        "source_url": source_url,
        "countries": countries or None,
        "note": None if countries else "Repartition par pays vide ou non disponible.",
    }


def get_country_breakdown(isin: str) -> dict:
    isin = isin.strip().upper()

    cached = _cache.get(isin)
    if cached and (time.time() - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    result = _fetch_country_breakdown(isin)
    _cache[isin] = (time.time(), result)
    return result
