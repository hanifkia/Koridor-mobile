"""
Mission response mapper - converts Mission entities to response schemas
"""

from app.core.entities import Mission
from app.api.v1.schemas.mission_schemas import MissionResponse
from app.api.v1.schemas.order_schemas import AddressSchema, CoordinatesSchema


def map_mission_to_response(mission: Mission) -> MissionResponse:
    """
    Map Mission entity to MissionResponse schema

    Args:
        mission: Mission entity

    Returns:
        MissionResponse schema
    """
    return MissionResponse(
        # Required fields
        id=mission.id,
        route_id=mission.route_id,
        order_id=mission.order_id,
        terminal_id=mission.terminal_id,
        shift_id=mission.shift_id,
        courier_id=mission.courier_id,
        status=mission.status,
        is_return=mission.is_return,
        # Location information
        location=(
            CoordinatesSchema(
                lat=mission.location.lat,
                lon=mission.location.lon,
            )
            if mission.location is not None
            else None
        ),
        address=(
            AddressSchema(
                street=mission.address.street,
                city=mission.address.city,
                state=mission.address.state,
                country=mission.address.country,
                postal_code=mission.address.postal_code,
            )
            if mission.address is not None
            else None
        ),
        # Planned times and distances
        arrival_time=mission.arrival_time,
        cumulative_duration=mission.cumulative_duration,
        cumulative_distance=mission.cumulative_distance,
        service_time=mission.service_time,
        # Actual execution times and distances
        actual_arrival_time=mission.actual_arrival_time,
        actual_cumulative_duration=mission.actual_cumulative_duration,
        actual_cumulative_distance=mission.actual_cumulative_distance,
        actual_service_time=mission.actual_service_time,
        actual_mission_start_time=mission.actual_mission_start_time,
        actual_mission_finish_time=mission.actual_mission_finish_time,
        # Mission positioning and waiting times
        position_in_route=mission.position_in_route,
        waiting_time=mission.waiting_time,
        actual_waiting_time=mission.actual_waiting_time,
        # Parcel scanning
        loading_scan_parcel_time=mission.loading_scan_parcel_time,
        delivery_scan_parcel_time=mission.delivery_scan_parcel_time,
        delivery_scan_parcel_barcode=mission.delivery_scan_parcel_barcode,
        # Additional information
        courier_comment=mission.courier_comment,
        postponed=mission.postponed,
        # Audit
        created_at=mission.created_at,
        updated_at=mission.updated_at,
    )


def map_missions_to_responses(missions: list[Mission]) -> list[MissionResponse]:
    """
    Map multiple Mission entities to MissionResponse schemas

    Args:
        missions: List of Mission entities

    Returns:
        List of MissionResponse schemas
    """
    return [map_mission_to_response(mission) for mission in missions]
