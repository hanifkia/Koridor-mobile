from pydantic import BaseModel
from typing import Optional, List


class CountrySchema(BaseModel):
    id: int
    name: str
    iso2: str | None = None
    iso3: str | None = None
    emoji: str
    region: str | None = None
    subregion: Optional[str] = None
    phone_code: Optional[str] = None
    capital: Optional[str] = None


class CountryDetailSchema(CountrySchema):
    numeric_code: Optional[str] = None
    currency: Optional[str] = None
    currency_name: Optional[str] = None
    currency_symbol: Optional[str] = None
    tld: Optional[str] = None
    native: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezones: Optional[List[dict]] = None
    translations: Optional[dict] = None


class StateSchema(BaseModel):
    id: int
    name: str
    country_code: str
    state_code: Optional[str] = None
    type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CitySchema(BaseModel):
    id: int
    name: str
    country_code: str
    state_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class TimezoneResponseSchema(BaseModel):
    name: str
    utc_offset: str


class CurrencyResponseSchema(BaseModel):
    code: str
    name: str
    symbol: str
