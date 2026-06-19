from pydantic import BaseModel


class TrendRouteGeoLocationInput(BaseModel):
    id: str
    longitude: float
    latitude: float


class TrendRouteGeoSpatialDirectionsRequest(BaseModel):
    geolocations: list[TrendRouteGeoLocationInput]
    ignore_oneway: bool = False
    only_polyline: bool = False


class TrendRouteGeoLocationOutput(BaseModel):
    longitude: float
    latitude: float


class TrendRouteWaypoint(BaseModel):
    geolocation: TrendRouteGeoLocationOutput
    is_original: bool


class TrendRouteGeoSpatialDirectionsResponse(BaseModel):
    distance: int
    duration: int
    polyline: str
    waypoints: list[TrendRouteWaypoint]
