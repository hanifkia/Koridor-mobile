from typing import List, Optional, Tuple
from uuid import UUID
import logging
from datetime import time, datetime
import json

from app.core.interfaces.services.solver_service_interface import ISolverService
from app.core.entities import (
    Order,
    Hub,
    Vehicle,
    Route,
    RouteStatesType,
    Mission,
    MissionStatusType,
    Coordinates,
    RouteCreatedType,
)
from app.adapters.clients.trendroute.trendroute_client import TrendRouteAsyncClient
from app.adapters.clients.trendroute.schemas import (
    TrendRouteOrderModel,
    TrendRouteHubModel,
    TrendRouteVehicleModel,
    TrendRouteOptimizationRequestModel,
    TrendRouteOptimizationResponseModel,
)

logger = logging.getLogger(__name__)


class RouteGenerationError(Exception):
    """Exception raised when route generation fails"""

    pass


class TrendRouteSolverService(ISolverService):
    """Implementation of ISolverService using TrendRoute optimization engine"""

    def __init__(self):
        self._client = TrendRouteAsyncClient()
        self._logger = logger

    async def solve(self, solver_input: dict) -> Optional[dict]:
        """
        Generate routes using TrendRoute optimization engine

        Args:
            solver_input: Dictionary with optimization parameters

        Returns:
            Dictionary with routes and unassigned orders, or None if failed
        """
        self._logger.info("Starting TrendRoute solver...")

        try:
            # Create request model
            self._logger.info("🔨 Creating request model...")
            request_model = TrendRouteOptimizationRequestModel(**solver_input)
            self._logger.info("✅ Request model created successfully")

            # Call API
            self._logger.info("📡 Calling TrendRoute API...")
            # with open("app/adapters/clients/trendroute/solver_input.json", "w") as f:
            #     json.dump(solver_input, f, indent=4)
            async with self._client as client:
                response_model = await client.solve_and_get_solution(request_model)

            if not response_model:
                self._logger.error("❌ Empty response from API")
                return None

            # Convert Pydantic model to dict for consistency
            response_dict = response_model.model_dump()
            print("*********************** RESPONSE DICT ************************")
            print(response_dict)
            print("****************************************************************")
            self._logger.info("✅ TrendRoute solver completed successfully")
            return response_dict

        except Exception as e:
            self._logger.error(f"❌ TrendRoute solve failed: {str(e)}", exc_info=True)
            return None

    async def map_to_solver_input(
        self, orders: list[Order], hub: Hub, vehicle: Vehicle, params: dict
    ) -> Tuple[dict, dict]:
        """
        Map domain entities to TrendRoute optimization request format

        Args:
            orders: List of Order entities
            hub: Hub entity
            vehicle: Vehicle entity
            params: Dictionary with additional parameters

        Returns:
            Tuple of (solver_input dict, metadata dict)
        """
        try:
            self._logger.info(
                f"🔄 Starting map_to_solver_input with {len(orders)} orders"
            )

            # Map orders
            self._logger.info("📦 Mapping orders...")
            trend_orders = [
                TrendRouteOrderModel(
                    id=str(order.id),
                    stop_id=int(hash(order.recipient_id) % 10000),
                    longitude=(
                        float(order.recipient.location.lon)
                        if order.recipient and order.recipient.location
                        else float(hub.lon)
                    ),
                    latitude=(
                        float(order.recipient.location.lat)
                        if order.recipient and order.recipient.location
                        else float(hub.lat)
                    ),
                    service_time=120,
                    time_windows=(
                        self._map_time_windows(order.time_window)
                        if order.time_window
                        else None
                    ),
                    weight=int(order.weight_occupation or 0),
                    volume=int(order.volume_occupation or 0),
                    is_pickup=bool(order.is_return or False),
                    pickup_id=str(order.moved_as) if order.moved_as else None,
                )
                for order in orders
            ]
            self._logger.info(f"✅ Mapped {len(trend_orders)} orders")

            # Map hub
            self._logger.info("🏢 Mapping hub...")
            trend_hub = TrendRouteHubModel(
                id=str(hub.id),
                longitude=float(hub.lon),
                latitude=float(hub.lat),
                is_return_hub=bool(hub.return_to_hub or False),
            )
            self._logger.info("✅ Hub mapped successfully")

            # Map vehicle
            self._logger.info("🚗 Mapping vehicle...")
            trend_vehicle = TrendRouteVehicleModel(
                id=str(vehicle.id),
                time_window=self._map_vehicle_time_window(
                    params.get("start_time"), params.get("finish_time")
                ),
                weight_capacity=(
                    int(vehicle.weight_capacity) if vehicle.weight_capacity else 999999
                ),
                volume_capacity=(
                    int(vehicle.volume_capacity) if vehicle.volume_capacity else 999999
                ),
                max_distance=int(vehicle.max_distance or 999999),
                max_duration=int(
                    vehicle.max_duration.total_seconds()
                    if vehicle.max_duration
                    else 86400
                ),
                max_number_orders=int(vehicle.max_tasks or 999),
                type=str(vehicle.vehicle_type.value),
                ignore_oneway=False,
            )
            self._logger.info("✅ Vehicle mapped successfully")

            # Convert start_time to seconds
            start_time_value = params.get("start_time", 0)
            if isinstance(start_time_value, time):
                start_time_seconds = int(
                    start_time_value.hour * 3600 + start_time_value.minute * 60
                )
            else:
                start_time_seconds = int(start_time_value) if start_time_value else 0

            # **FIX: Convert Pydantic models to JSON-serializable dicts**
            self._logger.info("🔨 Building solver input...")

            # Use json.loads(model_dump_json()) for proper serialization
            orders_json = [
                json.loads(order.model_dump_json()) for order in trend_orders
            ]
            hub_json = json.loads(trend_hub.model_dump_json())
            vehicles_json = [json.loads(trend_vehicle.model_dump_json())]

            solver_input = {
                "region_id": str(params.get("region_id", "default_region")),
                "orders": orders_json,
                "hub": hub_json,
                "vehicles": vehicles_json,
                "start_time": start_time_seconds,
                "max_duration": int(
                    vehicle.max_duration.total_seconds()
                    if vehicle.max_duration
                    else 86400
                ),
            }

            # Debug: Log the actual payload
            self._logger.debug(
                f"Solver input payload: {json.dumps(solver_input, indent=2, default=str)}"
            )

            # Store metadata separately
            metadata = {
                "terminal_id": str(params.get("terminal_id", "")),
                "shift_id": str(params.get("shift_id", "")),
                "courier_id": str(params.get("courier_id", "")),
                "start_time": (
                    params.get("start_time").isoformat()
                    if isinstance(params.get("start_time"), time)
                    else str(params.get("start_time"))
                ),
                "finish_time": (
                    params.get("finish_time").isoformat()
                    if isinstance(params.get("finish_time"), time)
                    else str(params.get("finish_time"))
                ),
                "must_return": params.get("must_return", True),
            }

            self._logger.info("✅ Solver input built successfully")

            return solver_input, metadata

        except Exception as e:
            self._logger.error(
                f"❌ map_to_solver_input failed: {str(e)}", exc_info=True
            )
            raise

    async def map_solver_output(
        self,
        solver_response: dict | TrendRouteOptimizationResponseModel,
        metadata: dict,
    ) -> Tuple[Route | None, List[UUID]]:
        """
        Map TrendRoute solver output to Route domain model

        Args:
            solver_response: Response from TrendRoute solver (dict or Pydantic model)
            metadata: Metadata from the optimization request

        Returns:
            Tuple of (Route object or None, list of unassigned order UUIDs)
        """
        self._logger.info("🔄 Starting map_solver_output...")

        try:
            # Convert Pydantic model to dict if needed
            if isinstance(solver_response, TrendRouteOptimizationResponseModel):
                self._logger.debug(
                    "Converting TrendRouteOptimizationResponseModel to dict"
                )
                solver_response = solver_response.model_dump()

            routes = solver_response.get("routes", [])
            unassigned_order_ids = solver_response.get("unassigned_order_ids", [])

            self._logger.info(
                f"📊 Solver output summary: {len(routes)} routes, "
                f"{len(unassigned_order_ids)} unassigned orders"
            )

            # Check if no routes were generated
            if not routes:
                self._logger.warning(
                    f"⚠️  No routes generated - all {len(unassigned_order_ids)} orders unassigned"
                )
                unassigned_uuids = [UUID(oid) for oid in unassigned_order_ids]
                return None, unassigned_uuids, None

            # Map the first (and typically only) route
            solver_route = routes[0]
            self._logger.info(f"🗺️  Mapping route {solver_route.get('id')}...")

            # Extract route details from metadata
            # ✅ FIX: Use UUID() with no argument to generate a NEW random UUID, not UUID(int=0)
            route_id = (
                UUID(metadata.get("route_id"))
                if metadata.get("route_id")
                else UUID(int=0)
            )
            # Actually, let's generate a proper new UUID
            try:
                route_id = UUID(metadata.get("route_id"))
            except (ValueError, TypeError):
                from uuid import uuid4

                route_id = uuid4()

            courier_id = UUID(metadata.get("courier_id"))
            terminal_id = UUID(metadata.get("terminal_id"))
            shift_id = UUID(metadata.get("shift_id"))

            # Parse start and finish times from metadata
            start_time_str = metadata.get("start_time", "09:00:00")
            finish_time_str = metadata.get("finish_time", "17:00:00")

            # Convert ISO format string to time object
            if isinstance(start_time_str, str):
                start_time = time.fromisoformat(start_time_str)
            else:
                start_time = start_time_str

            if isinstance(finish_time_str, str):
                finish_time = time.fromisoformat(finish_time_str)
            else:
                finish_time = finish_time_str

            # Map missions from steps (filter out START and END)
            missions = []
            step_order = 0

            for step in solver_route.get("steps", []):
                step_type = step.get("type", "")

                # Handle both string and enum types
                if isinstance(step_type, str):
                    step_type_lower = step_type.lower()
                else:
                    step_type_lower = str(step_type).lower()

                # Skip start and end steps, only process visit steps
                if "visit" not in step_type_lower:
                    self._logger.debug(f"Skipping step type: {step_type_lower}")
                    continue

                step_order += 1

                try:
                    # ✅ IMPORTANT: Use step.get("id") as order_id, not as mission_id
                    order_id_str = step.get("id")
                    if not order_id_str:
                        self._logger.warning("Step has no ID, skipping")
                        continue

                    order_id = UUID(order_id_str)

                    # ✅ Generate a UNIQUE mission ID for each mission
                    from uuid import uuid4

                    mission_id = uuid4()

                    # Convert arrival time from seconds to time object
                    arrival_seconds = step.get("time_of_arrival", 0)
                    arrival_datetime = datetime.fromtimestamp(arrival_seconds)
                    arrival_time = arrival_datetime.time()

                    mission = Mission(
                        # Required fields
                        route_id=route_id,
                        order_id=order_id,  # ✅ This is the order ID from solver
                        terminal_id=terminal_id,
                        shift_id=shift_id,
                        courier_id=courier_id,
                        is_return=False,
                        # Optional fields
                        id=mission_id,  # ✅ Generate unique mission ID, not use order ID
                        location=Coordinates(
                            lat=float(step.get("latitude", 0.0)),
                            lon=float(step.get("longitude", 0.0)),
                        ),
                        address=None,
                        # Planned times and distances
                        arrival_time=arrival_time,
                        cumulative_duration=int(
                            step.get("cummulated_traveled_time", 0)
                        ),
                        cumulative_distance=int(
                            step.get("cummulated_traveled_distance", 0)
                        ),
                        service_time=int(step.get("service_time", 0)),
                        # Actual times (not available from solver)
                        actual_arrival_time=None,
                        actual_cumulative_duration=None,
                        actual_cumulative_distance=None,
                        actual_service_time=None,
                        actual_mission_start_time=None,
                        actual_mission_finish_time=None,
                        # Mission status
                        status=MissionStatusType.SCHEDULED.value,
                        postponed=False,
                        # Route positioning
                        position_in_route=step_order,
                        # Waiting times
                        waiting_time=int(step.get("waiting_time", 0)),
                        actual_waiting_time=None,
                        # Parcel scanning
                        loading_scan_parcel_time=None,
                        delivery_scan_parcel_time=None,
                        delivery_scan_parcel_barcode=None,
                        # Additional information
                        courier_comment=None,
                        # Audit
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    missions.append(mission)
                    self._logger.debug(
                        f"✅ Mapped mission {mission_id} for order {order_id} - "
                        f"Position: {step_order}, Arrival: {arrival_time}"
                    )

                except ValueError as e:
                    self._logger.warning(
                        f"⚠️  Failed to convert UUID for step {step.get('id')}: {str(e)}"
                    )
                    continue
                except Exception as e:
                    self._logger.warning(
                        f"⚠️  Failed to map mission from step {step.get('id')}: {str(e)}",
                        exc_info=True,
                    )
                    continue

            if not missions:
                self._logger.error("❌ No missions extracted from route steps")
                unassigned_uuids = [UUID(oid) for oid in unassigned_order_ids]
                return None, unassigned_uuids, None

            # Generate route name
            route_name = (
                f"Route-{courier_id.hex[:8].upper()}-{route_id.hex[:8].upper()}"
            )

            # Generate a color for visualization
            route_color = self._generate_route_color()

            # Create Route domain object with ALL required fields
            route = Route(
                # ✅ REQUIRED FIELDS FIRST
                terminal_id=terminal_id,
                shift_id=shift_id,
                courier_id=courier_id,
                vehicle_id=UUID(solver_route.get("vehicle_id")),
                route_name=route_name,
                start_time=start_time,
                finish_time=finish_time,
                status=RouteStatesType.SCHEDULED,
                color=route_color,
                must_return=bool(metadata.get("must_return", True)),
                number_of_missions=len(missions),
                # ✅ OPTIONAL/DEFAULT FIELDS
                id=route_id,  # ✅ Use generated route_id, not null UUID
                # Actual execution times (not available from solver)
                actual_start_time=None,
                actual_finish_time=None,
                # Route metrics
                cost=None,
                duration=int(solver_route.get("total_duration", 0))
                // 60,  # Convert to minutes
                distance=int(solver_route.get("total_traveled_distance", 0)),
                # Current state
                current_mission_id=None,
                # Mission aggregates
                total_waiting_time=int(solver_route.get("total_waiting_time", 0)) // 60,
                total_actual_waiting_time=None,
                total_number_of_orders=int(
                    solver_route.get("total_number_of_orders", len(missions))
                ),
                total_number_of_stops=int(
                    solver_route.get("total_number_of_stops", len(missions))
                ),
                # Hub interaction
                loading_time_start=None,
                arrived_at_hub_time=None,
                # Route metadata
                lock=False,
                created_type=RouteCreatedType.TRENDROUTE,
                modification_time=None,
                courier_score=None,
                # Audit
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            self._logger.info(
                f"✅ Route mapped successfully: {route.id}, "
                f"Name: {route.route_name}, "
                f"Missions: {len(missions)}, "
                f"Distance: {route.distance}m, "
                f"Duration: {route.duration}min, "
                f"Unassigned: {len(unassigned_order_ids)}"
            )

            # Convert unassigned order IDs from strings to UUIDs
            unassigned_uuids = [UUID(oid) for oid in unassigned_order_ids]

            return route, unassigned_uuids, missions

        except Exception as e:
            self._logger.error(
                f"❌ Failed to map solver output: {str(e)}", exc_info=True
            )
            raise RouteGenerationError(f"Failed to map solver output: {str(e)}")

    # ==================== Helper Methods ====================

    def _map_time_windows(self, time_window) -> Optional[List[List[int]]]:
        """
        Convert TimeWindow entity to TrendRoute format (seconds from start)

        Args:
            time_window: TimeWindow entity with earliest and latest times

        Returns:
            List of [start_seconds, end_seconds] or None
        """
        if not time_window:
            return None

        try:
            earliest_seconds = int(
                time_window.earliest.hour * 3600 + time_window.earliest.minute * 60
            )
            latest_seconds = int(
                time_window.latest.hour * 3600 + time_window.latest.minute * 60
            )
            return [[earliest_seconds, latest_seconds]]
        except Exception as e:
            self._logger.warning(f"Could not map time window: {str(e)}")
            return None

    def _map_vehicle_time_window(
        self, start_time: Optional[time | str], finish_time: Optional[time | str]
    ) -> Optional[List[int]]:
        """
        Convert vehicle shift times to TrendRoute format (seconds from midnight)

        Args:
            start_time: Start time as time object or ISO string
            finish_time: Finish time as time object or ISO string

        Returns:
            List [start_seconds, finish_seconds] or None
        """
        if not start_time or not finish_time:
            return None

        try:
            # Handle both time objects and strings
            if isinstance(start_time, time):
                start = start_time
            else:
                start = time.fromisoformat(str(start_time))

            if isinstance(finish_time, time):
                finish = finish_time
            else:
                finish = time.fromisoformat(str(finish_time))

            start_seconds = int(start.hour * 3600 + start.minute * 60)
            finish_seconds = int(finish.hour * 3600 + finish.minute * 60)

            return [start_seconds, finish_seconds]
        except (ValueError, TypeError, AttributeError) as e:
            self._logger.warning(
                f"⚠️  Could not parse vehicle time window: {start_time} - {finish_time}: {e}"
            )
            return None

    @staticmethod
    def _generate_route_color() -> str:
        """Generate a random color for route visualization"""
        import random

        colors = [
            "#FF6B6B",
            "#4ECDC4",
            "#45B7D1",
            "#FFA07A",
            "#98D8C8",
            "#F7DC6F",
            "#BB8FCE",
        ]
        return random.choice(colors)
