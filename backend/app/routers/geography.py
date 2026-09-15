from fastapi import APIRouter, HTTPException, Query

from .. import schemas
from ..services import justetf_service
from ..services import yfinance_service as yf_service

router = APIRouter(prefix="/api/geography", tags=["geography"])


@router.get(
    "/countries",
    response_model=schemas.GeographyResponse,
    summary="Repartition geographique par pays (source : justETF, hors yfinance)",
)
def countries(
    isin: str = Query(
        ...,
        min_length=12,
        max_length=12,
        description="Code ISIN (12 caracteres) de l'ETF/fonds, ex: IE00B4L5Y983",
    )
):
    isin = isin.strip().upper()
    if not yf_service.is_isin(isin):
        raise HTTPException(
            status_code=400,
            detail="Format ISIN invalide (attendu : 2 lettres + 9 caracteres alphanumeriques + 1 chiffre).",
        )

    try:
        return justetf_service.get_country_breakdown(isin)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Erreur lors de la recuperation des donnees justETF : {exc}",
        )
