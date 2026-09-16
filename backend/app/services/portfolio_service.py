"""Analyse par lot : a partir d'un CSV (isin, quantite, valeur de part), calcule
la valeur de chaque ligne, resout chaque ISIN, puis agrege secteur/geographie/
top holdings sur l'ensemble du portefeuille, pondere par le poids de chaque
ligne (position_value / total_value). Reutilise les memes fonctions que
l'exploration unitaire (yfinance_service, justetf_service) pour rester
coherent avec les autres cartes du dashboard."""

import csv
import io
import unicodedata
from typing import Optional

from . import justetf_service
from . import yfinance_service as yf_service

_ISIN_HEADERS = {"isin"}
_QUANTITY_HEADERS = {"quantity", "quantite", "qty", "parts", "nombre", "nb", "quantiteparts"}
_UNIT_VALUE_HEADERS = {
    "unitvalue",
    "valeur",
    "valeurpart",
    "valeurdepart",
    "prix",
    "prixunitaire",
    "nav",
    "cours",
    "price",
    "unitprice",
}


def _normalize_header(name: str) -> str:
    name = name.strip().lower()
    name = "".join(c for c in unicodedata.normalize("NFD", name) if unicodedata.category(c) != "Mn")
    return name.replace(" ", "").replace("_", "").replace("-", "")


def _parse_number(value) -> Optional[float]:
    if value is None:
        return None
    value = str(value).strip().replace(" ", "").replace(" ", "")
    if not value:
        return None

    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "," in value:
        value = value.replace(",", ".")

    try:
        return float(value)
    except ValueError:
        return None


def _detect_dialect(text: str) -> csv.Dialect:
    sample = text.splitlines()[0] if text.splitlines() else ""
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t")
    except Exception:
        dialect = csv.excel()
        dialect.delimiter = ";" if sample.count(";") > sample.count(",") else ","
        return dialect


def parse_csv(raw_bytes: bytes) -> dict:
    """Parse le CSV en detectant le delimiteur (, ; ou tab) et le format des
    nombres (1234.56 ou 1 234,56). Renvoie les lignes valides et une liste
    d'erreurs ligne par ligne (transparence sur ce qui a ete ignore)."""
    text = raw_bytes.decode("utf-8-sig", errors="replace")
    dialect = _detect_dialect(text)

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        return {"rows": [], "errors": [{"row": 0, "isin": None, "reason": "Fichier CSV vide ou illisible."}]}

    header_map = {}
    for original in reader.fieldnames:
        normalized = _normalize_header(original)
        if normalized in _ISIN_HEADERS:
            header_map["isin"] = original
        elif normalized in _QUANTITY_HEADERS:
            header_map["quantity"] = original
        elif normalized in _UNIT_VALUE_HEADERS:
            header_map["unit_value"] = original

    missing = [c for c in ("isin", "quantity", "unit_value") if c not in header_map]
    if missing:
        return {
            "rows": [],
            "errors": [
                {
                    "row": 0,
                    "isin": None,
                    "reason": (
                        "Colonnes manquantes : "
                        + ", ".join(missing)
                        + ". Attendu : isin, quantity (quantite), unit_value (valeur de part)."
                    ),
                }
            ],
        }

    rows = []
    errors = []
    for i, raw_row in enumerate(reader, start=2):  # ligne 1 = en-tete
        isin_raw = (raw_row.get(header_map["isin"]) or "").strip().upper()
        if not isin_raw:
            continue  # ligne vide, ignoree silencieusement

        if not yf_service.is_isin(isin_raw):
            errors.append({"row": i, "isin": isin_raw, "reason": "Format ISIN invalide."})
            continue

        quantity = _parse_number(raw_row.get(header_map["quantity"]))
        unit_value = _parse_number(raw_row.get(header_map["unit_value"]))
        if quantity is None or unit_value is None:
            errors.append({"row": i, "isin": isin_raw, "reason": "Quantite ou valeur de part illisible."})
            continue

        rows.append({"row": i, "isin": isin_raw, "quantity": quantity, "unit_value": unit_value})

    return {"rows": rows, "errors": errors}


def _empty_result(total_lines: int, errors: list) -> dict:
    return {
        "total_lines": total_lines,
        "resolved_lines": 0,
        "total_value": 0.0,
        "lines": [],
        "errors": errors,
        "sector_breakdown": {},
        "geography_breakdown": None,
        "geography_coverage": 0.0,
        "top_holdings": [],
        "holdings_coverage": 0.0,
    }


def analyze_portfolio(raw_bytes: bytes) -> dict:
    parsed = parse_csv(raw_bytes)
    rows = parsed["rows"]
    errors = list(parsed["errors"])

    if not rows:
        return _empty_result(0, errors)

    resolved_cache: dict = {}
    lines = []
    total_value = 0.0

    for row in rows:
        isin = row["isin"]
        position_value = row["quantity"] * row["unit_value"]
        total_value += position_value

        if isin not in resolved_cache:
            try:
                resolved_cache[isin] = yf_service.resolve_isin(isin)
            except Exception:
                resolved_cache[isin] = None
        resolved = resolved_cache[isin]

        if not resolved:
            errors.append({"row": row["row"], "isin": isin, "reason": "ISIN non resolu par Yahoo Finance."})

        lines.append(
            {
                "row": row["row"],
                "isin": isin,
                "symbol": resolved["symbol"] if resolved else None,
                "name": resolved.get("shortname") if resolved else None,
                "quote_type": resolved.get("quote_type") if resolved else None,
                "quantity": row["quantity"],
                "unit_value": row["unit_value"],
                "position_value": position_value,
                "weight": None,
            }
        )

    resolved_lines = sum(1 for l in lines if l["symbol"])

    if total_value <= 0:
        for line in lines:
            line["weight"] = 0.0
        result = _empty_result(len(rows), errors)
        result.update({"resolved_lines": resolved_lines, "total_value": total_value, "lines": lines})
        return result

    sector_agg: dict = {}
    geo_agg: dict = {}
    geo_covered_weight = 0.0
    holdings_agg: dict = {}
    holdings_covered_weight = 0.0

    sector_cache: dict = {}
    holdings_cache: dict = {}
    geo_cache: dict = {}

    for line in lines:
        line["weight"] = line["position_value"] / total_value
        weight = line["weight"]
        symbol = line["symbol"]
        quote_type = (line["quote_type"] or "").upper()

        if not symbol:
            continue

        if symbol not in sector_cache:
            try:
                sector_cache[symbol] = yf_service.get_sector(symbol)
            except Exception:
                sector_cache[symbol] = None
        sector_data = sector_cache[symbol]

        if sector_data and sector_data.get("sector_weightings"):
            for sector_name, sector_weight in sector_data["sector_weightings"].items():
                sector_agg[sector_name] = sector_agg.get(sector_name, 0.0) + weight * sector_weight
        elif sector_data and sector_data.get("sector"):
            sector_agg[sector_data["sector"]] = sector_agg.get(sector_data["sector"], 0.0) + weight
        else:
            sector_agg["Non classifie"] = sector_agg.get("Non classifie", 0.0) + weight

        if quote_type in yf_service.FUND_QUOTE_TYPES:
            if isin not in geo_cache:
                try:
                    geo_cache[line["isin"]] = justetf_service.get_country_breakdown(line["isin"])
                except Exception:
                    geo_cache[line["isin"]] = None
            geo_data = geo_cache[line["isin"]]
            if geo_data and geo_data.get("countries"):
                geo_covered_weight += weight
                for country, country_weight in geo_data["countries"].items():
                    geo_agg[country] = geo_agg.get(country, 0.0) + weight * country_weight

            if symbol not in holdings_cache:
                try:
                    holdings_cache[symbol] = yf_service.get_top_holdings(symbol, limit=10)
                except Exception:
                    holdings_cache[symbol] = None
            holdings_data = holdings_cache[symbol]
            if holdings_data and holdings_data.get("holdings"):
                holdings_covered_weight += weight
                for h in holdings_data["holdings"]:
                    entry = holdings_agg.setdefault(h["symbol"], {"name": h.get("name"), "weight": 0.0})
                    entry["weight"] += weight * (h.get("weight") or 0.0)
        else:
            entry = holdings_agg.setdefault(symbol, {"name": line["name"], "weight": 0.0})
            entry["weight"] += weight
            holdings_covered_weight += weight

    top_holdings = sorted(
        ({"symbol": s, "name": v["name"], "weight": v["weight"]} for s, v in holdings_agg.items()),
        key=lambda x: x["weight"],
        reverse=True,
    )[:10]

    return {
        "total_lines": len(rows),
        "resolved_lines": resolved_lines,
        "total_value": total_value,
        "lines": lines,
        "errors": errors,
        "sector_breakdown": sector_agg,
        "geography_breakdown": geo_agg or None,
        "geography_coverage": geo_covered_weight,
        "top_holdings": top_holdings,
        "holdings_coverage": holdings_covered_weight,
    }
