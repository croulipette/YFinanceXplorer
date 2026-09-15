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
    "/{symbol}/profile",
    response_model=schemas.ProfileResponse,
    summary="Secteur d'activite et zone geographique",
)
def profile(symbol: str):
    try:
        return yf_service.get_profile(symbol)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erreur lors de la recuperation du profil : {exc}")


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
