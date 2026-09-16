from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from .. import schemas
from ..services import yfinance_service as yf_service

router = APIRouter(prefix="/api/securities", tags=["securities"])


@router.get(
    "/resolve",
    response_model=schemas.ResolveResponse,
    summary="Resout un code ISIN en symbole Yahoo Finance",
)
def resolve(
    isin: str = Query(
        ...,
        min_length=12,
        max_length=12,
        description="Code ISIN (12 caracteres), ex: FR0000120271",
    )
):
    isin = isin.strip().upper()
    if not yf_service.is_isin(isin):
        raise HTTPException(
            status_code=400,
            detail="Format ISIN invalide (attendu : 2 lettres + 9 caracteres alphanumeriques + 1 chiffre).",
        )

    resolved = yf_service.resolve_isin(isin)
    if not resolved:
        raise HTTPException(
            status_code=404,
            detail=f"Aucun titre Yahoo Finance trouve pour l'ISIN {isin}.",
        )
    return resolved


@router.get(
    "/search",
    response_model=schemas.SearchResponse,
    summary="Recherche libre par nom/symbole (ex: 'Msci World')",
)
def search(
    query: str = Query(..., min_length=2, description="Nom ou symbole a rechercher, ex: 'Msci World'"),
    max_results: int = Query(8, ge=1, le=20),
):
    results = yf_service.search_symbols(query, max_results=max_results)
    return {"query": query, "results": results}


@router.get(
    "/{symbol}/isin",
    response_model=schemas.IsinLookupResponse,
    summary="ISIN d'un symbole deja connu (best-effort, pour la carte geographie)",
)
def isin_for_symbol(symbol: str):
    return {"symbol": symbol, "isin": yf_service.get_isin_for_symbol(symbol)}


@router.get(
    "/{symbol}/sector",
    response_model=schemas.SectorResponse,
    summary="Secteur d'activite (hors zone geographique, voir /api/geography)",
)
def sector(symbol: str):
    try:
        return yf_service.get_sector(symbol)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erreur lors de la recuperation du secteur : {exc}")


@router.get(
    "/{symbol}/price",
    response_model=schemas.PriceResponse,
    summary="Valeur courante",
)
def price(symbol: str):
    try:
        return yf_service.get_price(symbol)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erreur lors de la recuperation du prix : {exc}")


@router.get(
    "/{symbol}/history",
    response_model=schemas.HistoryResponse,
    summary="Historique des valeurs (pour tracer une courbe)",
)
def history(
    symbol: str,
    period: Literal["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"] = "1y",
    interval: Literal["1d", "1wk", "1mo"] = "1d",
):
    try:
        return yf_service.get_history(symbol, period=period, interval=interval)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erreur lors de la recuperation de l'historique : {exc}")


@router.get(
    "/{symbol}/fees",
    response_model=schemas.FeesResponse,
    summary="Frais de gestion (ETF / fonds uniquement)",
)
def fees(symbol: str):
    try:
        return yf_service.get_fees(symbol)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erreur lors de la recuperation des frais : {exc}")
