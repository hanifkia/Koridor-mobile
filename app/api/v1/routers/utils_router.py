from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional

from app.api.v1.schemas.utils_schemas import (
    CountrySchema,
    CountryDetailSchema,
    StateSchema,
    CitySchema,
    TimezoneResponseSchema,
    CurrencyResponseSchema,
)
from countrystatecity_countries import (
    get_countries,
    get_country_by_code,
    get_country_by_id,
    search_countries,
    get_countries_by_region,
    get_countries_by_subregion,
    get_states_of_country,
    get_state_by_code,
    search_states,
    get_cities_of_state,
    get_cities_of_country,
    search_cities,
)

from app.config.security import get_current_user

router = APIRouter(prefix="/api/v1/utils", tags=["Utils"])


# ============================================================================
# COUNTRIES ENDPOINTS
# ============================================================================


@router.get("/countries", response_model=List[CountrySchema])
async def list_countries(
    current_user: dict = Depends(get_current_user),
) -> List[CountrySchema]:
    """
    Get all countries with basic metadata.

    **Returns:** List of all countries with id, name, ISO codes, emoji, and region info
    """
    countries = get_countries()
    return [
        CountrySchema(
            id=country.id,
            name=country.name,
            iso2=country.iso2,
            iso3=country.iso3,
            emoji=country.emoji,
            region=country.region,
            subregion=country.subregion,
            phone_code=country.phone_code,
            capital=country.capital,
        )
        for country in countries
    ]


@router.get("/countries/search", response_model=List[CountrySchema])
async def search_countries_endpoint(
    query: str = Query(..., min_length=1, description="Search term for country name"),
    current_user: dict = Depends(get_current_user),
) -> List[dict]:
    """
    Search countries by name (case-insensitive).

    **Parameters:**
    - `query`: Search term (e.g., 'united', 'india', 'france')

    **Returns:** List of matching countries

    **Example:** `/countries/search?query=united`
    """
    results = search_countries(query)

    if not results:
        raise HTTPException(
            status_code=404, detail=f"No countries found matching '{query}'"
        )

    return [
        CountrySchema(
            id=country.id,
            name=country.name,
            iso2=country.iso2,
            iso3=country.iso3,
            emoji=country.emoji,
            region=country.region,
            subregion=country.subregion,
            phone_code=country.phone_code,
            capital=country.capital,
        )
        for country in results
    ]


@router.get("/countries/{country_code}", response_model=CountryDetailSchema)
async def get_country(
    country_code: str, current_user: dict = Depends(get_current_user)
) -> CountryDetailSchema:
    """
    Get detailed information about a specific country.

    **Parameters:**
    - `country_code`: ISO2 code (e.g., 'US') or ISO3 code (e.g., 'USA')

    **Returns:** Detailed country information including currency, timezones, coordinates

    **Example:** `/countries/US`
    """
    country = get_country_by_code(country_code.upper())

    if not country:
        raise HTTPException(
            status_code=404, detail=f"Country with code '{country_code}' not found"
        )

    return CountryDetailSchema(
        id=country.id,
        name=country.name,
        iso2=country.iso2,
        iso3=country.iso3,
        numeric_code=country.numeric_code,
        phone_code=country.phone_code,
        capital=country.capital,
        emoji=country.emoji,
        currency=country.currency,
        currency_name=country.currency_name,
        currency_symbol=country.currency_symbol,
        tld=country.tld,
        native=country.native,
        region=country.region,
        subregion=country.subregion,
        latitude=country.latitude,
        longitude=country.longitude,
        timezones=country.timezones,
        translations=country.translations,
    )


@router.get("/countries/by-id/{country_id}", response_model=CountryDetailSchema)
async def get_country_by_id_endpoint(
    country_id: int, current_user: dict = Depends(get_current_user)
) -> CountryDetailSchema:
    """
    Get country by numeric ID.

    **Parameters:**
    - `country_id`: Numeric country ID (e.g., 1 for Afghanistan)

    **Returns:** Country details

    **Example:** `/countries/by-id/233` (USA)
    """
    country = get_country_by_id(country_id)

    if not country:
        raise HTTPException(
            status_code=404, detail=f"Country with ID '{country_id}' not found"
        )

    return CountryDetailSchema(
        id=country.id,
        name=country.name,
        iso2=country.iso2,
        iso3=country.iso3,
        emoji=country.emoji,
        capital=country.capital,
        currency_symbol=country.currency_symbol,
        region=country.region,
    )


@router.get("/countries/region/{region}", response_model=List[CountrySchema])
async def get_countries_by_region_endpoint(
    region: str, current_user: dict = Depends(get_current_user)
) -> List[CountrySchema]:
    """
    Get all countries in a specific region.

    **Parameters:**
    - `region`: Region name (e.g., 'Asia', 'Europe', 'Africa', 'Americas', 'Oceania')

    **Returns:** List of countries in the region

    **Example:** `/countries/region/Asia`
    """
    countries = get_countries_by_region(region)

    if not countries:
        raise HTTPException(
            status_code=404, detail=f"No countries found in region '{region}'"
        )

    return [
        CountrySchema(
            id=country.id,
            name=country.name,
            iso2=country.iso2,
            emoji=country.emoji,
            capital=country.capital,
        )
        for country in countries
    ]


@router.get("/countries/subregion/{subregion}", response_model=List[CountrySchema])
async def get_countries_by_subregion_endpoint(
    subregion: str, current_user: dict = Depends(get_current_user)
) -> List[CountrySchema]:
    """
    Get all countries in a specific subregion.

    **Parameters:**
    - `subregion`: Subregion name (e.g., 'Southern Asia', 'Western Europe')

    **Returns:** List of countries in the subregion

    **Example:** `/countries/subregion/Southern%20Asia`
    """
    countries = get_countries_by_subregion(subregion)

    if not countries:
        raise HTTPException(
            status_code=404, detail=f"No countries found in subregion '{subregion}'"
        )

    return [
        CountrySchema(
            id=country.id,
            name=country.name,
            iso2=country.iso2,
            emoji=country.emoji,
            capital=country.capital,
        )
        for country in countries
    ]


# ============================================================================
# STATES ENDPOINTS
# ============================================================================


@router.get("/countries/{country_code}/states", response_model=List[StateSchema])
async def list_states(
    country_code: str, current_user: dict = Depends(get_current_user)
) -> List[StateSchema]:
    """
    Get all states/provinces for a country.

    **Parameters:**
    - `country_code`: ISO2 country code (e.g., 'US', 'IN', 'CA')

    **Returns:** List of states with id, name, state code, and coordinates

    **Example:** `/countries/US/states`
    """
    try:
        states = get_states_of_country(country_code.upper())
    except Exception:
        raise HTTPException(
            status_code=404, detail=f"Country with code '{country_code}' not found"
        )

    if not states:
        raise HTTPException(
            status_code=404, detail=f"No states found for country '{country_code}'"
        )

    return [
        StateSchema(
            id=state.id,
            name=state.name,
            country_code=state.country_code,
            state_code=state.state_code,
            type=state.type,
            latitude=state.latitude,
            longitude=state.longitude,
        )
        for state in states
    ]


@router.get("/countries/{country_code}/states/search", response_model=List[StateSchema])
async def search_states_endpoint(
    country_code: str,
    query: str = Query(..., min_length=1, description="Search term for state name"),
    current_user: dict = Depends(get_current_user),
) -> List[StateSchema]:
    """
    Search states within a country.

    **Parameters:**
    - `country_code`: ISO2 country code (e.g., 'US')
    - `query`: Search term (e.g., 'New', 'California')

    **Returns:** List of matching states

    **Example:** `/countries/US/states/search?query=New`
    """
    results = search_states(country_code.upper(), query)

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No states found in '{country_code}' matching '{query}'",
        )

    return [
        StateSchema(
            id=state.id,
            name=state.name,
            country_code=state.country_code,
            state_code=state.state_code,
            type=state.type,
            latitude=state.latitude,
            longitude=state.longitude,
        )
        for state in results
    ]


@router.get("/countries/{country_code}/states/{state_code}", response_model=StateSchema)
async def get_state(
    country_code: str, state_code: str, current_user: dict = Depends(get_current_user)
) -> StateSchema:
    """
    Get detailed information about a specific state.

    **Parameters:**
    - `country_code`: ISO2 country code (e.g., 'US')
    - `state_code`: State code (e.g., 'CA', 'NY')

    **Returns:** State details with coordinates

    **Example:** `/countries/US/states/CA`
    """
    state = get_state_by_code(country_code.upper(), state_code.upper())

    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"State '{state_code}' not found in '{country_code}'",
        )

    return StateSchema(
        id=state.id,
        name=state.name,
        country_code=state.country_code,
        state_code=state.state_code,
        type=state.type,
        latitude=state.latitude,
        longitude=state.longitude,
    )


# ============================================================================
# CITIES ENDPOINTS
# ============================================================================


@router.get(
    "/countries/{country_code}/states/{state_code}/cities",
    response_model=List[CitySchema],
)
async def list_cities(
    country_code: str, state_code: str, current_user: dict = Depends(get_current_user)
) -> List[CitySchema]:
    """
    Get all cities in a state.

    **Parameters:**
    - `country_code`: ISO2 country code (e.g., 'US')
    - `state_code`: State code (e.g., 'CA')

    **Returns:** List of cities with coordinates

    **Example:** `/countries/US/states/CA/cities`
    """
    try:
        cities = get_cities_of_state(country_code.upper(), state_code.upper())
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Invalid country code '{country_code}' or state code '{state_code}'",
        )

    if not cities:
        raise HTTPException(
            status_code=404, detail=f"No cities found for {country_code}/{state_code}"
        )

    return [
        CitySchema(
            id=city.id,
            name=city.name,
            state_code=city.state_code,
            country_code=city.country_code,
            latitude=city.latitude,
            longitude=city.longitude,
        )
        for city in cities
    ]


@router.get("/countries/{country_code}/cities", response_model=List[CitySchema])
async def list_all_cities_in_country(
    country_code: str, current_user: dict = Depends(get_current_user)
) -> List[CitySchema]:
    """
    Get all cities in a country.

    **⚠️ Warning:** This may return a very large list for countries with many cities.
    Consider using the state-specific endpoint instead.

    **Parameters:**
    - `country_code`: ISO2 country code (e.g., 'US')

    **Returns:** List of all cities in the country

    **Example:** `/countries/US/cities`
    """
    try:
        cities = get_cities_of_country(country_code.upper())
    except Exception:
        raise HTTPException(
            status_code=404, detail=f"Country '{country_code}' not found"
        )

    if not cities:
        raise HTTPException(
            status_code=404, detail=f"No cities found for '{country_code}'"
        )

    return [
        CitySchema(
            id=city.id,
            name=city.name,
            state_code=city.state_code,
            country_code=city.country_code,
            latitude=city.latitude,
            longitude=city.longitude,
        )
        for city in cities[:1000]  # Limit to first 1000 for API response
    ]


@router.get("/countries/{country_code}/cities/search", response_model=List[CitySchema])
async def search_cities_endpoint(
    country_code: str,
    state_code: Optional[str] = Query(
        None, description="Optional state code to limit search"
    ),
    query: str = Query(..., min_length=1, description="Search term for city name"),
    current_user: dict = Depends(get_current_user),
) -> List[CitySchema]:
    """
    Search cities by name.

    **Parameters:**
    - `country_code`: ISO2 country code (e.g., 'US')
    - `state_code`: Optional state code (e.g., 'CA') to limit search to a specific state
    - `query`: Search term (e.g., 'Los', 'New York')

    **Returns:** List of matching cities

    **Examples:**
    - `/countries/US/cities/search?query=Los` (search entire country)
    - `/countries/US/cities/search?state_code=CA&query=Los` (search within state)
    """
    results = search_cities(
        country_code.upper(), state_code.upper() if state_code else None, query
    )

    if not results:
        location = f"{country_code}/{state_code}" if state_code else country_code
        raise HTTPException(
            status_code=404,
            detail=f"No cities found in '{location}' matching '{query}'",
        )

    return [
        CitySchema(
            id=city.id,
            name=city.name,
            state_code=city.state_code,
            country_code=city.country_code,
            latitude=city.latitude,
            longitude=city.longitude,
        )
        for city in results
    ]


# ============================================================================
# TIMEZONE ENDPOINTS
# ============================================================================


@router.get(
    "/countries/{country_code}/timezones", response_model=List[TimezoneResponseSchema]
)
async def get_country_timezones(
    country_code: str, current_user: dict = Depends(get_current_user)
) -> List[TimezoneResponseSchema]:
    """
    Get timezones for a specific country.

    **Parameters:**
    - `country_code`: ISO2 country code (e.g., 'US')

    **Returns:** List of timezone objects with name and UTC offset

    **Example:** `/countries/US/timezones`
    """
    country = get_country_by_code(country_code.upper())

    if not country:
        raise HTTPException(
            status_code=404, detail=f"Country '{country_code}' not found"
        )

    if not country.timezones:
        raise HTTPException(
            status_code=404, detail=f"No timezones found for country '{country_code}'"
        )

    return [
        TimezoneResponseSchema(name=tz["zoneName"], utc_offset=tz["gmtOffsetName"])
        for tz in country.timezones
    ]


# ============================================================================
# CURRENCY ENDPOINTS
# ============================================================================


@router.get("/countries/{country_code}/currency", response_model=CurrencyResponseSchema)
async def get_country_currency(
    country_code: str, current_user: dict = Depends(get_current_user)
) -> CurrencyResponseSchema:
    """
    Get currency information for a specific country.

    **Parameters:**
    - `country_code`: ISO2 country code (e.g., 'US')

    **Returns:** Currency code, name, and symbol

    **Example:** `/countries/US/currency`
    """
    country = get_country_by_code(country_code.upper())

    if not country:
        raise HTTPException(
            status_code=404, detail=f"Country '{country_code}' not found"
        )

    if not country.currency:
        raise HTTPException(
            status_code=404,
            detail=f"No currency information available for '{country_code}'",
        )

    return CurrencyResponseSchema(
        code=country.currency,
        name=country.currency_name,
        symbol=country.currency_symbol,
    )
