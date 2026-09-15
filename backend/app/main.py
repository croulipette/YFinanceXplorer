from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import geography, securities

app = FastAPI(
    title="YFinance Explorer API",
    description=(
        "API interne : a partir d'un code ISIN, resout le symbole Yahoo Finance "
        "puis expose une route dediee par fonctionnalite (profil, prix, historique, frais)."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(securities.router)
app.include_router(geography.router)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
