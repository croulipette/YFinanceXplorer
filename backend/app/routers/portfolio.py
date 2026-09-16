from fastapi import APIRouter, File, HTTPException, UploadFile

from .. import schemas
from ..services import portfolio_service

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.post(
    "/analyze",
    response_model=schemas.PortfolioAnalysisResponse,
    summary="Analyse par lot (CSV isin/quantity/unit_value) : secteur/geographie/top holdings agreges",
)
async def analyze(file: UploadFile = File(...)):
    if file.filename and not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Le fichier doit etre un CSV (.csv).")

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Fichier vide.")

    try:
        return portfolio_service.analyze_portfolio(raw_bytes)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erreur lors de l'analyse du portefeuille : {exc}")
