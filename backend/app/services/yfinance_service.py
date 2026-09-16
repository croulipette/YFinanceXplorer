"""Encapsule tous les appels a yfinance et formate les resultats pour le front."""

import re
from datetime import datetime, timezone
from typing import Optional

import yfinance as yf

ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")

FUND_QUOTE_TYPES = {"ETF", "MUTUALFUND"}


def is_isin(value: str) -> bool:
    return bool(ISIN_PATTERN.match(value.strip().upper()))


def _safe_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return f


def _fast_info_value(fast_info, key: str):
    try:
        value = fast_info[key]
        if value is not None:
            return value
    except Exception:
        pass
    return getattr(fast_info, key, None)


def resolve_isin(isin: str) -> Optional[dict]:
    """Resout un ISIN en symbole Yahoo Finance via l'endpoint de recherche."""
    isin = isin.strip().upper()
    search = yf.Search(isin, max_results=1, raise_errors=False)
    quotes = search.quotes or []
    if not quotes:
        return None

    quote = quotes[0]
    symbol = quote.get("symbol")
    if not symbol:
        return None

    return {
        "isin": isin,
        "symbol": symbol,
        "shortname": quote.get("shortname") or quote.get("longname"),
        "exchange": quote.get("exchDisp") or quote.get("exchange"),
        "quote_type": quote.get("quoteType") or quote.get("typeDisp"),
    }


def search_symbols(query: str, max_results: int = 8) -> list:
    """Recherche libre par nom/symbole (ex: 'Msci World') via l'endpoint de
    recherche Yahoo. A la difference de resolve_isin, renvoie plusieurs
    candidats a choisir cote front (une recherche par nom est ambigue :
    plusieurs emetteurs proposent un ETF 'MSCI World')."""
    query = query.strip()
    search = yf.Search(query, max_results=max_results, raise_errors=False)
    quotes = search.quotes or []

    results = []
    for quote in quotes:
        symbol = quote.get("symbol")
        if not symbol:
            continue
        results.append(
            {
                "symbol": symbol,
                "shortname": quote.get("shortname") or quote.get("longname"),
                "exchange": quote.get("exchDisp") or quote.get("exchange"),
                "quote_type": quote.get("quoteType") or quote.get("typeDisp"),
            }
        )
    return results


def get_isin_for_symbol(symbol: str) -> Optional[str]:
    """Cherche l'ISIN d'un symbole deja connu (recherche par nom -> pas
    d'ISIN dans les resultats). Best-effort : yfinance scrape la page de
    cotation Yahoo, renvoie None si absent ou introuvable."""
    try:
        isin = yf.Ticker(symbol).isin
    except Exception:
        return None
    if not isin or isin == "-":
        return None
    return isin


def get_sector(symbol: str) -> dict:
    """Secteur d'activite uniquement (yfinance). La zone geographique est
    une fonctionnalite distincte, servie par justETF (voir justetf_service),
    volontairement pas melangee ici."""
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}
    quote_type = (info.get("quoteType") or "").upper()

    result = {
        "symbol": symbol,
        "quote_type": quote_type or None,
        "name": info.get("longName") or info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "sector_weightings": None,
        "asset_classes": None,
        "long_business_summary": info.get("longBusinessSummary"),
        "note": None,
    }

    if quote_type in FUND_QUOTE_TYPES:
        try:
            funds_data = ticker.funds_data
            weightings = funds_data.sector_weightings
            result["sector_weightings"] = weightings or None
            result["asset_classes"] = funds_data.asset_classes or None
            if not weightings:
                result["note"] = (
                    "Repartition sectorielle non fournie par Yahoo Finance pour ce fonds."
                )
        except Exception:
            result["note"] = "Impossible de recuperer les donnees sectorielles du fonds."

    if not result["sector"] and not result["sector_weightings"] and result["note"] is None:
        result["note"] = "Secteur d'activite non disponible pour ce titre."

    return result


def get_price(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    fast_info = ticker.fast_info

    last_price = _safe_float(_fast_info_value(fast_info, "last_price"))
    previous_close = _safe_float(_fast_info_value(fast_info, "previous_close"))
    currency = _fast_info_value(fast_info, "currency")

    change = None
    change_percent = None
    if last_price is not None and previous_close:
        change = last_price - previous_close
        change_percent = (change / previous_close) * 100

    return {
        "symbol": symbol,
        "currency": currency,
        "last_price": last_price,
        "previous_close": previous_close,
        "change": change,
        "change_percent": change_percent,
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def get_history(symbol: str, period: str = "1y", interval: str = "1d") -> dict:
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval=interval, auto_adjust=True)

    points = []
    for ts, row in hist.iterrows():
        points.append(
            {
                "date": ts.isoformat(),
                "open": _safe_float(row.get("Open")),
                "high": _safe_float(row.get("High")),
                "low": _safe_float(row.get("Low")),
                "close": _safe_float(row.get("Close")),
                "volume": _safe_float(row.get("Volume")),
            }
        )

    currency = _fast_info_value(ticker.fast_info, "currency")

    return {
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "currency": currency,
        "points": points,
    }


def get_top_holdings(symbol: str, limit: int = 10) -> dict:
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}
    quote_type = (info.get("quoteType") or "").upper()

    result = {
        "symbol": symbol,
        "quote_type": quote_type or None,
        "applicable": quote_type in FUND_QUOTE_TYPES,
        "holdings": None,
        "note": None,
    }

    if not result["applicable"]:
        result["note"] = "Top holdings non applicable : ce titre n'est pas un ETF ou un fonds."
        return result

    try:
        df = ticker.funds_data.top_holdings
        if df is None or df.empty:
            result["note"] = "Top holdings non fournis par Yahoo Finance pour ce fonds."
            return result

        holdings = []
        for holding_symbol, row in df.head(limit).iterrows():
            holdings.append(
                {
                    "symbol": holding_symbol,
                    "name": row.get("Name"),
                    "weight": _safe_float(row.get("Holding Percent")),
                }
            )
        result["holdings"] = holdings
    except Exception:
        result["note"] = "Top holdings indisponibles (donnee non fournie par Yahoo Finance)."

    return result


def get_fees(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}
    quote_type = (info.get("quoteType") or "").upper()

    result = {
        "symbol": symbol,
        "quote_type": quote_type or None,
        "applicable": quote_type in FUND_QUOTE_TYPES,
        "expense_ratio": None,
        "expense_ratio_percent": None,
        "category_average_percent": None,
        "note": None,
    }

    if not result["applicable"]:
        result["note"] = "Frais de gestion non applicables : ce titre n'est pas un ETF ou un fonds."
        return result

    try:
        ops = ticker.funds_data.fund_operations
        row = ops.loc["Annual Report Expense Ratio"]

        expense_ratio = _safe_float(row.get(symbol))
        category_average = _safe_float(row.get("Category Average"))

        result["expense_ratio"] = expense_ratio
        result["expense_ratio_percent"] = expense_ratio * 100 if expense_ratio is not None else None
        result["category_average_percent"] = (
            category_average * 100 if category_average is not None else None
        )

        if expense_ratio is None:
            result["note"] = "Frais de gestion non fournis par Yahoo Finance pour ce fonds."
    except Exception:
        result["note"] = "Frais de gestion indisponibles (donnee non fournie par Yahoo Finance)."

    return result
