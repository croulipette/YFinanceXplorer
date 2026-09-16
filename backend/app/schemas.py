from typing import Dict, List, Optional

from pydantic import BaseModel


class ResolveResponse(BaseModel):
    isin: str
    symbol: str
    shortname: Optional[str] = None
    exchange: Optional[str] = None
    quote_type: Optional[str] = None


class SearchResultItem(BaseModel):
    symbol: str
    shortname: Optional[str] = None
    exchange: Optional[str] = None
    quote_type: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]


class IsinLookupResponse(BaseModel):
    symbol: str
    isin: Optional[str] = None


class SectorResponse(BaseModel):
    symbol: str
    quote_type: Optional[str] = None
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    sector_weightings: Optional[Dict[str, float]] = None
    asset_classes: Optional[Dict[str, float]] = None
    long_business_summary: Optional[str] = None
    note: Optional[str] = None


class PriceResponse(BaseModel):
    symbol: str
    currency: Optional[str] = None
    last_price: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    as_of: str


class HistoryPoint(BaseModel):
    date: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None


class HistoryResponse(BaseModel):
    symbol: str
    period: str
    interval: str
    currency: Optional[str] = None
    points: List[HistoryPoint]


class GeographyResponse(BaseModel):
    isin: str
    source: str
    source_url: str
    countries: Optional[Dict[str, float]] = None
    note: Optional[str] = None


class FeesResponse(BaseModel):
    symbol: str
    quote_type: Optional[str] = None
    applicable: bool
    expense_ratio: Optional[float] = None
    expense_ratio_percent: Optional[float] = None
    category_average_percent: Optional[float] = None
    note: Optional[str] = None
