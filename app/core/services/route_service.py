from typing import List, Optional, Tuple
from uuid import UUID
import logging
from datetime import time, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.core.interfaces.services.solver_service_interface import ISolverService
from app.core.interfaces import (
    IOrderRepository,
    IRouteRepository,
    IHubRepository,
    IVehicleRepository,
    IHubShiftRepository,
    IUserRepository,
    ICourierRepository,
    IMissionRepository,
    IRecipientRepository,
    IHubShiftRepository,
)

from app.core.entities import (
    Order,
    Route,
    Hub,
    Vehicle,
    HubShifts,
    User,
    Courier,
    OrderStatusTypes,
    Mission,
    MissionStatusType,
    RouteStatesType,
    RouteCreatedType,
    Coordinates,
)

logger = logging.getLogger(__name__)


class RouteServiceError(Exception):
    """Base exception for RouteService errors"""

    pass


class RouteGenerationError(RouteServiceError):
    """Raised when route generation fails"""

    pass


class ValidationError(RouteServiceError):
    """Raised when validation fails"""

    pass


class RouteService:
    """Service for managing route generation and optimization"""

    def __init__(
        self,
        solver_service: ISolverService,
        order_repo: IOrderRepository,
        route_repo: IRouteRepository,
        hub_repo: IHubRepository,
        vehicle_repo: IVehicleRepository,
        shift_repo: IHubShiftRepository,
        user_repo: IUserRepository,
        courier_repo: ICourierRepository,
        mission_repo: IMissionRepository,
        recipient_repo: IRecipientRepository,
        hubshift_repo: IHubShiftRepository,
        billing_service,  # ← Add billing service dependency
        session: AsyncSession,
    ):
        self._solver_service = solver_service
        self._order_repo = order_repo
        self._route_repo = route_repo
        self._hub_repo = hub_repo
        self._vehicle_repo = vehicle_repo
        self._shift_repo = shift_repo
        self._user_repo = user_repo
        self._courier_repo = courier_repo
        self._mission_repo = mission_repo
        self._recipient_repo = recipient_repo
        self._hubshift_repo = hubshift_repo
        self._billing_service = billing_service  # ← Store billing service
        self._session = session
        self._logger = logger

    # ==================== Fetch Methods ====================

    async def _fetch_orders(self, order_ids: list[UUID]) -> List[Order]:
        """
        Fetch orders by their IDs

        Args:
            order_ids: List of order UUIDs

        Returns:
            List of Order entities

        Raises:
            ValidationError: If orders not found
        """
        try:
            orders = await self._order_repo.get_by_list_of_order_ids(order_ids)
            if not orders:
                self._logger.warning(f"No orders found for IDs: {order_ids}")
                raise ValidationError(f"Orders not found for IDs: {order_ids}")

            self._logger.info(f"Fetched {len(orders)} orders")
            return orders

        except ValidationError:
            raise
        except Exception as e:
            self._logger.error(f"Error fetching orders: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to fetch orders: {str(e)}")

    async def _fetch_hub(self, terminal_id: UUID) -> Hub:
        """
        Fetch hub by ID

        Args:
            terminal_id: Hub UUID

        Returns:
            Hub entity

        Raises:
            ValidationError: If hub not found
        """
        try:
            hub = await self._hub_repo.get_by_id(terminal_id)
            if not hub:
                self._logger.warning(f"Hub not found: {terminal_id}")
                raise ValidationError(f"Hub not found with ID: {terminal_id}")

            self._logger.info(f"Fetched hub: {hub.name} ({terminal_id})")
            return hub

        except ValidationError:
            raise
        except Exception as e:
            self._logger.error(f"Error fetching hub: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to fetch hub: {str(e)}")

    async def _fetch_vehicle(self, courier_id: UUID) -> Vehicle:
        """
        Fetch vehicle by ID

        Args:
            vehicle_id: Vehicle UUID

        Returns:
            Vehicle entity

        Raises:
            ValidationError: If vehicle not found
        """
        try:
            vehicle = await self._vehicle_repo.get_by_courier_id(courier_id)
            if not vehicle:
                self._logger.warning(f"Vehicle not found: {courier_id}")
                raise ValidationError(
                    f"Vehicle not found with Courier ID: {courier_id}"
                )

            vehicle = vehicle[0]  # assume there is only one vehicle
            self._logger.info(f"Fetched vehicle: {vehicle.id}")
            return vehicle

        except ValidationError:
            raise
        except Exception as e:
            self._logger.error(f"Error fetching vehicle: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to fetch vehicle: {str(e)}")

    async def _fetch_shift(self, shift_id: UUID) -> HubShifts:
        """
        Fetch hub shift by ID

        Args:
            shift_id: Shift UUID

        Returns:
            HubShifts entity

        Raises:
            ValidationError: If shift not found
        """
        try:
            shift = await self._shift_repo.get_by_id(shift_id)
            if not shift:
                self._logger.warning(f"Shift not found: {shift_id}")
                raise ValidationError(f"Shift not found with ID: {shift_id}")

            self._logger.info(f"Fetched shift: {shift_id}")
            return shift

        except ValidationError:
            raise
        except Exception as e:
            self._logger.error(f"Error fetching shift: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to fetch shift: {str(e)}")

    async def _fetch_courier(self, user_id: UUID) -> Courier:
        """
        Fetch courier by user ID

        Args:
            user_id: User UUID

        Returns:
            Courier entity

        Raises:
            ValidationError: If courier not found
        """
        try:
            courier = await self._courier_repo.get_by_user_id(user_id)
            if not courier:
                self._logger.warning(f"Courier not found for user: {user_id}")
                raise ValidationError(f"Courier not found for user ID: {user_id}")

            self._logger.info(f"Fetched courier: {courier.id}")
            return courier

        except ValidationError:
            raise
        except Exception as e:
            self._logger.error(f"Error fetching courier: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to fetch courier: {str(e)}")

    async def _fetch_recipient_and_attach_to_order(self, order: Order) -> Order:
        recipient = await self._recipient_repo.get_by_id(order.recipient_id)
        if not recipient:
            self._logger.warning(f"Recipient not found for order: {order.id}")
            raise ValidationError(f"Recipient not found for order ID: {order.id}")

        order.recipient = recipient
        return order

    # ==================== Validation Methods ====================

    async def _validate_orders(
        self,
        orders: List[Order],
        courier_id: UUID,
        terminal_id: UUID,
        shift_id: UUID,
    ) -> None:
        """
        Validate that all orders meet requirements for route generation

        Args:
            orders: List of Order entities
            courier_id: Expected courier ID
            terminal_id: Expected hub ID
            shift_id: Expected shift ID

        Raises:
            ValidationError: If any validation fails
        """
        if not orders:
            raise ValidationError("No orders provided for validation")

        errors = []

        for order in orders:
            # Check order status
            if order.status not in [
                OrderStatusTypes.REGISTERED,
                OrderStatusTypes.UNASSIGNED,
                OrderStatusTypes.SCHEDULED,
            ]:
                errors.append(
                    f"Order {order.id} has status {order.status.value}, expected REGISTERED (or UNASSIGNED or SCHEDULED)"
                )

            # Check courier assignment
            if order.courier_id != courier_id:
                errors.append(
                    f"Order {order.id} is assigned to courier {order.courier_id}, "
                    f"not {courier_id}"
                )

            # Check hub assignment
            if order.terminal_id != terminal_id:
                errors.append(
                    f"Order {order.id} is assigned to hub {order.terminal_id}, not {terminal_id}"
                )

            # Check shift assignment
            if order.shift_id != shift_id:
                errors.append(
                    f"Order {order.id} is assigned to shift {order.shift_id}, not {shift_id}"
                )

        if errors:
            error_msg = "; ".join(errors)
            self._logger.warning(f"Order validation failed: {error_msg}")
            raise ValidationError(f"Order validation failed: {error_msg}")

        self._logger.info(f"Validated {len(orders)} orders successfully")

    async def _validate_vehicle_capacity(
        self, orders: List[Order], vehicle: Vehicle
    ) -> None:
        """
        Validate that vehicle can potentially handle all orders

        Args:
            orders: List of Order entities
            vehicle: Vehicle entity

        Raises:
            ValidationError: If total capacity is insufficient
        """
        total_weight = sum(order.weight_occupation for order in orders)
        total_volume = sum(order.volume_occupation for order in orders)

        if total_weight > vehicle.weight_capacity:
            self._logger.warning(
                f"Total weight {total_weight} exceeds capacity {vehicle.weight_capacity}"
            )
            raise ValidationError(
                f"Total order weight ({total_weight}) exceeds vehicle capacity "
                f"({vehicle.weight_capacity})"
            )

        if total_volume > vehicle.volume_capacity:
            self._logger.warning(
                f"Total volume {total_volume} exceeds capacity {vehicle.volume_capacity}"
            )
            raise ValidationError(
                f"Total order volume ({total_volume}) exceeds vehicle capacity "
                f"({vehicle.volume_capacity})"
            )

        self._logger.info(
            f"Vehicle capacity validated - Weight: {total_weight}/{vehicle.weight_capacity}, "
            f"Volume: {total_volume}/{vehicle.volume_capacity}"
        )

    # ==================== Mission Conversion Methods ====================

    async def _orders_to_missions(
        self,
        orders: List[Order],
        route: Route,
    ) -> List[Mission]:
        """
        Convert orders to missions for the generated route

        Args:
            orders: List of Order entities
            route: Generated Route entity

        Returns:
            List of Mission entities
        """
        missions = []

        try:
            for order in orders:
                # Get recipient location if available
                location = None
                if order.recipient and order.recipient.location:
                    location = order.recipient.location
                elif order.recipient and order.recipient.address:
                    # Use hub location as fallback
                    location = Coordinates(lat=order.hub.lat, lon=order.hub.lon)

                mission = Mission(
                    route_id=route.id,
                    order_id=order.id,
                    terminal_id=route.terminal_id,
                    shift_id=route.shift_id,
                    courier_id=route.courier_id,
                    is_return=order.is_return,
                    location=location,
                    address=order.recipient.address if order.recipient else None,
                    status=MissionStatusType.SCHEDULED.value,
                )
                missions.append(mission)

            self._logger.info(f"Converted {len(orders)} orders to missions")
            return missions

        except Exception as e:
            self._logger.error(
                f"Error converting orders to missions: {str(e)}", exc_info=True
            )
            raise RouteGenerationError(
                f"Failed to convert orders to missions: {str(e)}"
            )

    # ==================== Route Generation Methods ====================

    async def generate_route(
        self,
        order_ids: list[UUID],
        user_id: UUID,
        terminal_id: UUID,
        shift_id: UUID,
    ) -> Optional[Route]:  # ✅ Change return type to Optional
        """
        Generate optimized routes for given orders

        Returns None if no routes could be generated
        """
        self._logger.info(
            f"🚀 Starting route generation for {len(order_ids)} orders "
            f"(user: {user_id}, hub: {terminal_id})"
        )

        try:
            # Handle routes that are still ongoing but their shift time has passed
            await self.handle_routes_with_passed_time_shift()

            # ============ VALIDATE Subscription LIMIT ============
            if not await self._billing_service.can_generate_route(
                user_id, len(order_ids)
            ):
                self._logger.warning(
                    f"User {user_id} has reached route generation limit"
                )
                raise RouteGenerationError(
                    "Route generation limit reached for your subscription plan"
                )

            # ============ CHECK CURRENT ROUTES ============
            self._logger.info("📥 Checking current routes...")
            current_routes: List[Route] = await self._route_repo.get_by_terminal_id(
                terminal_id
            )
            self._logger.info(f"  ✅ Checked {len(current_routes)} current routes")
            active_route = None
            if current_routes:
                for route in current_routes:
                    if route.status in [
                        RouteStatesType.ONGOING,
                        RouteStatesType.LOADING,
                        RouteStatesType.RETURNTOHUB,
                    ]:
                        raise RouteGenerationError(
                            "Cannot generate route while another route is active"
                        )
                    if route.status == RouteStatesType.SCHEDULED:
                        active_route = route

            # ============ FETCH ENTITIES ============
            self._logger.info("📥 Fetching entities...")
            try:
                orders: List[Order] = await self._fetch_orders(order_ids)
                self._logger.info(f"  ✅ Fetched {len(orders)} orders")

                hub: Hub = await self._fetch_hub(terminal_id)
                self._logger.info(f"  ✅ Fetched hub: {hub.name}")

                shift: HubShifts = await self._fetch_shift(shift_id)
                self._logger.info(f"  ✅ Fetched shift: {shift_id}")

                courier: Courier = await self._fetch_courier(user_id)
                self._logger.info(f"  ✅ Fetched courier: {courier.id}")

                vehicle: Vehicle = await self._fetch_vehicle(courier.id)
                self._logger.info(f"  ✅ Fetched vehicle: {vehicle.id}")
            except Exception as e:
                self._logger.error(
                    f"  ❌ Failed to fetch entities: {str(e)}", exc_info=True
                )
                raise

            # ============ VALIDATE ORDERS ============
            self._logger.info("🔍 Validating orders...")
            try:
                await self._validate_orders(orders, courier.id, terminal_id, shift_id)
                self._logger.info("  ✅ Orders validation passed")
            except Exception as e:
                self._logger.error(
                    f"  ❌ Orders validation failed: {str(e)}", exc_info=True
                )
                raise

            # ============ FETCH RECIPIENTS ============
            self._logger.info("👤 Fetching recipients and attaching to orders...")
            try:
                orders = [
                    await self._fetch_recipient_and_attach_to_order(order)
                    for order in orders
                ]
                self._logger.info(f"  ✅ Attached recipients to {len(orders)} orders")
            except Exception as e:
                self._logger.error(
                    f"  ❌ Failed to fetch recipients: {str(e)}", exc_info=True
                )
                raise

            # ============ MAP TO SOLVER INPUT ============
            self._logger.info("📍 Mapping to solver input...")
            try:
                solver_input, metadata = await self._solver_service.map_to_solver_input(
                    orders=orders,
                    hub=hub,
                    vehicle=vehicle,
                    params={
                        "start_time": shift.start_time,
                        "finish_time": shift.finish_time,
                        "terminal_id": terminal_id,
                        "shift_id": shift_id,
                        "courier_id": courier.id,
                        "must_return": hub.return_to_hub,
                    },
                )
                self._logger.info(
                    f"  ✅ Solver input mapped (keys: {list(solver_input.keys())})"
                )
            except Exception as e:
                self._logger.error(
                    f"  ❌ Failed to map solver input: {str(e)}", exc_info=True
                )
                raise

            # ============ STORE METADATA SEPARATELY ============
            self._logger.info("📎 Preparing metadata...")
            try:
                metadata = {
                    "terminal_id": str(terminal_id),
                    "shift_id": str(shift_id),
                    "courier_id": str(courier.id),
                    "start_time": shift.start_time.isoformat(),
                    "finish_time": shift.finish_time.isoformat(),
                    "must_return": hub.return_to_hub,
                }
                self._logger.info("  ✅ Metadata prepared")
            except Exception as e:
                self._logger.error(
                    f"  ❌ Failed to prepare metadata: {str(e)}", exc_info=True
                )
                raise

            # ============ SOLVE OPTIMIZATION ============
            self._logger.info("⚙️  Submitting optimization request to solver...")
            try:
                logger.info(f"DEBUG: Solver input: {solver_input}")
                solver_output = await self._solver_service.solve(solver_input)

                if solver_output is None:
                    self._logger.error("  ❌ Solver returned None")
                    raise RouteGenerationError(
                        "Route optimization failed - solver returned None"
                    )

                self._logger.info(f"  ✅ Solver completed successfully")
            except RouteGenerationError:
                raise
            except Exception as e:
                self._logger.error(f"  ❌ Solver failed: {str(e)}", exc_info=True)
                raise RouteGenerationError(f"Solver optimization failed: {str(e)}")

            # ============ ADD METADATA ============
            self._logger.info("📎 Adding metadata to solver output...")
            try:
                # Store metadata for map_solver_output
                solver_input["_metadata"] = metadata
                self._logger.info("  ✅ Metadata prepared")
            except Exception as e:
                self._logger.error(
                    f"  ❌ Failed to prepare metadata: {str(e)}", exc_info=True
                )
                raise

            # ============ MAP SOLVER OUTPUT ============
            self._logger.info("🔄 Mapping solver output...")
            try:
                route, all_unassigned_ids, missions = (
                    await self._solver_service.map_solver_output(
                        solver_response=solver_output,
                        metadata=solver_input["_metadata"],
                    )
                )

                # ✅ Handle case where no routes were generated - THIS IS NOT AN ERROR
                if route is None:
                    self._logger.warning(
                        f"⚠️  No routes generated by solver - "
                        f"all {len(all_unassigned_ids)} orders remain unassigned"
                    )

                    # Update all orders to UNASSIGNED status
                    try:
                        for order in orders:
                            order.status = OrderStatusTypes.UNASSIGNED
                            await self._order_repo.update(order.id, order)

                        await self._session.commit()
                        self._logger.info(
                            f"✅ Marked all {len(orders)} orders as UNASSIGNED"
                        )
                    except Exception as e:
                        await self._session.rollback()
                        self._logger.error(
                            f"Failed to update orders to UNASSIGNED: {str(e)}"
                        )
                        raise RouteGenerationError(f"Failed to update orders: {str(e)}")

                    # ✅ RETURN None - NOT AN ERROR, THIS IS EXPECTED
                    self._logger.info(
                        f"✅ Route generation completed (no routes generated for unsupported location)"
                    )
                    return None

                self._logger.info(
                    f"  ✅ Route mapped: {route.id}, "
                    f"Missions: {route.number_of_missions}, "
                    f"Unassigned: {len(all_unassigned_ids)}"
                )
            except Exception as e:
                self._logger.error(
                    f"  ❌ Failed to map solver output: {str(e)}", exc_info=True
                )
                raise RouteGenerationError(f"Failed to map solver output: {str(e)}")

            # ============ PERSIST ROUTE AND MISSIONS ============
            self._logger.info(f"💾 Persisting route {route.id} and missions...")
            try:
                await self._persist_route_and_missions_and_orders(
                    route=route,
                    orders=orders,
                    missions=missions,
                    unassigned_order_ids=all_unassigned_ids,
                    active_route=active_route,
                )
                self._logger.info("  ✅ Route and missions persisted successfully")
            except RouteGenerationError:
                raise
            except Exception as e:
                self._logger.error(
                    f"  ❌ Failed to persist route: {str(e)}", exc_info=True
                )
                raise RouteGenerationError(f"Failed to persist route: {str(e)}")

            # ============ SUCCESS ============
            self._logger.info(
                f"✅ Route generation completed successfully! "
                f"Route ID: {route.id}, Missions: {route.number_of_missions}, "
                f"Unassigned orders: {len(all_unassigned_ids)}"
            )

            return route

        except (ValidationError, RouteGenerationError):
            self._logger.error(f"🛑 Route generation failed with known error")
            raise
        except Exception as e:
            self._logger.error(
                f"🛑 Unexpected error during route generation: {str(e)}",
                exc_info=True,
            )
            raise RouteGenerationError(f"Route generation failed: {str(e)}")

    async def _persist_route_and_missions_and_orders(
        self,
        route: Route,
        orders: List[Order],
        missions: List[Mission],
        unassigned_order_ids: List[UUID],
        active_route: Route = None,
    ) -> None:
        """
        Persist route and missions to database

        Args:
            route: Route entity to persist
            orders: Original orders
            unassigned_order_ids: List of unassigned order IDs
            active_route: The currently active route

        Raises:
            RouteGenerationError: If persistence fails
        """
        try:
            self._logger.info("💾 Starting persistence of route and missions...")

            # ============ CREATE or Update ROUTE ============
            if active_route:
                route.id = active_route.id  # Update existing route
                await self._route_repo.update(route.id, route)
                self._logger.info(
                    f"✅ Updated existing route: {route.id} ({route.route_name})"
                )
            else:
                await self._route_repo.create(route)
                self._logger.info(f"✅ Route created: {route.id} ({route.route_name})")

            # ============ UPDATE ORDER STATUSES ============
            assigned_count = 0
            unassigned_count = 0

            for order in orders:
                if order.id in unassigned_order_ids:
                    order.status = OrderStatusTypes.UNASSIGNED
                    unassigned_count += 1
                else:
                    order.status = OrderStatusTypes.SCHEDULED
                    assigned_count += 1

                await self._order_repo.update(order.id, order)

            self._logger.info(
                f"✅ Updated order statuses: {assigned_count} assigned, "
                f"{unassigned_count} unassigned"
            )

            # ============ CREATE MISSIONS ============
            # Missions are already created and attached to route during map_solver_output
            if not missions:
                self._logger.warning("⚠️  No missions found in route")
                await self._session.commit()
                return

            for position, mission in enumerate(missions, start=1):
                # Set the position if not already set
                if mission.position_in_route is None:
                    mission.position_in_route = position

                # Ensure status is set
                if mission.status is None:
                    mission.status = MissionStatusType.SCHEDULED.value

                # Create or update the mission
                exist_mission = await self._mission_repo.get_by_order_id(
                    mission.order_id
                )
                if not exist_mission:
                    await self._mission_repo.create(mission)
                    self._logger.debug(
                        f"✅ Created mission {mission.id} for order {mission.order_id} "
                        f"at position {mission.position_in_route}"
                    )
                else:
                    await self._mission_repo.update(exist_mission.id, mission)
                    self._logger.debug(
                        f"✅ Updated mission {exist_mission.id} for order {exist_mission.order_id} "
                        f"at position {mission.position_in_route}"
                    )

            self._logger.info(f"✅ Created {len(missions)} missions")

            # ============ COMMIT TRANSACTION ============
            await self._session.commit()
            self._logger.info(
                f"✅ Successfully persisted route {route.route_name} with "
                f"{len(missions)} missions"
            )

        except Exception as e:
            await self._session.rollback()
            self._logger.error(
                f"❌ Error persisting route and missions: {str(e)}",
                exc_info=True,
            )
            raise RouteGenerationError(
                f"Failed to persist route and missions: {str(e)}"
            )

    async def get_route(self, route_id: UUID) -> Optional[Route]:
        """
        Retrieve a route by ID

        Args:
            route_id: Route UUID

        Returns:
            Route entity or None if not found
        """
        try:
            # Handle routes that are still ongoing but their shift time has passed
            await self.handle_routes_with_passed_time_shift()

            route = await self._route_repo.get_by_id(route_id)
            if route:
                self._logger.info(f"Retrieved route: {route_id}")
            else:
                self._logger.warning(f"Route not found: {route_id}")
            return route
        except Exception as e:
            self._logger.error(f"Error retrieving route: {str(e)}", exc_info=True)
            raise RouteServiceError(f"Failed to retrieve route: {str(e)}")

    async def get_route_missions(self, route_id: UUID) -> List[Mission]:
        """
        Retrieve all missions for a route

        Args:
            route_id: Route UUID

        Returns:
            List of Mission entities
        """
        try:

            # Handle routes that are still ongoing but their shift time has passed
            await self.handle_routes_with_passed_time_shift()

            missions = await self._mission_repo.get_by_route_id(route_id)
            self._logger.info(
                f"Retrieved {len(missions)} missions for route {route_id}"
            )
            return missions
        except Exception as e:
            self._logger.error(f"Error retrieving missions: {str(e)}", exc_info=True)
            raise RouteServiceError(f"Failed to retrieve missions: {str(e)}")

    async def cancel_route(self, route_id: UUID) -> None:
        """
        Cancel a route

        Args:
            route_id: Route UUID

        Raises:
            RouteServiceError: If cancellation fails
        """
        try:
            route = await self._route_repo.get_by_id(route_id)
            if not route:
                raise ValidationError(f"Route not found: {route_id}")

            # Update route status
            route.status = RouteStatesType.CANCELLED
            await self._route_repo.update(route.id, route)

            # Update missions status
            missions = await self._mission_repo.get_by_route_id(route_id)
            for mission in missions:
                mission.status = MissionStatusType.CANCELLED.value
                await self._mission_repo.update(mission.id, mission)

            # Update orders status
            for mission in missions:
                order = await self._order_repo.get_by_id(mission.order_id)
                order.status = OrderStatusTypes.UNASSIGNED
                await self._order_repo.update(order.id, order)

            await self._session.commit()
            self._logger.info(
                f"Route {route_id} and its {len(missions)} missions cancelled"
            )

        except ValidationError:
            raise
        except Exception as e:
            await self._session.rollback()
            self._logger.error(f"Error cancelling route: {str(e)}", exc_info=True)
            raise RouteServiceError(f"Failed to cancel route: {str(e)}")

    async def get_courier_all_routes(
        self, user_id: UUID, limit: int, skip: int
    ) -> List[Route]:
        """
        Retrieve all routes for a courier

        Args:
            user_id: User ID UUID

        Returns:
            List of Route entities
        """
        try:
            # Handle routes that are still ongoing but their shift time has passed
            await self.handle_routes_with_passed_time_shift()

            courier = await self._courier_repo.get_by_user_id(user_id)
            if not courier:
                self._logger.warning(f"Courier not found for user: {user_id}")
                raise RouteServiceError(f"Courier not found for user: {user_id}")

            courier_id = courier.id
            routes = await self._route_repo.get_by_courier_id(
                courier_id, skip=skip, limit=limit
            )
            self._logger.info(
                f"Retrieved {len(routes)} routes for courier {courier_id}"
            )

            total_counts = await self._route_repo.count_routes_by_courier_id(courier_id)
            self._logger.info(f"Total routes for courier {courier_id}: {total_counts}")

            return routes, total_counts
        except Exception as e:
            self._logger.error(f"Error retrieving routes: {str(e)}", exc_info=True)
            raise RouteServiceError(f"Failed to retrieve routes: {str(e)}")

    async def get_current_route(
        self, user_id: UUID, terminal_id: UUID
    ) -> Optional[Route]:
        try:
            # Handle routes that are still ongoing but their shift time has passed
            await self.handle_routes_with_passed_time_shift()

            courier: Courier = await self._courier_repo.get_by_user_id(user_id)
            if not courier:
                self._logger.warning(f"Courier not found for user: {user_id}")
                raise RouteServiceError(f"Courier not found for user: {user_id}")

            hub: Hub = await self._hub_repo.get_by_id(terminal_id)
            if not hub:
                self._logger.warning(f"Hub not found for user: {terminal_id}")
                raise RouteServiceError(f"Hub not found for user: {terminal_id}")

            courier_shifts: list[HubShifts] = (
                await self._hubshift_repo.get_by_terminal_id(hub.id)
            )  # ← Should be list
            if not courier_shifts:
                self._logger.warning(f"Courier shift not found for hub: {terminal_id}")
                raise RouteServiceError(
                    f"Courier shift not found for hub: {terminal_id}"
                )

            current_clock_shift: HubShifts = await self._get_the_current_clock_shift(
                courier_shifts
            )
            if not current_clock_shift:
                self._logger.warning("No current clock shift found")
                raise RouteServiceError("No current clock shift found")

            route: Route = await self._route_repo.get_assigned_route(
                courier.id, current_clock_shift.id
            )

            self._logger.info(f"DEBUG: route type: {type(route)}")
            self._logger.info(f"DEBUG: route is list? {isinstance(route, list)}")
            self._logger.info(f"DEBUG: route value: {route}")

            return route
        except Exception as e:
            self._logger.error(
                f"Error retrieving current route: {str(e)}", exc_info=True
            )
            raise RouteServiceError(f"Failed to retrieve current route: {str(e)}")

    async def _get_the_current_clock_shift(
        self, hub_shifts: list[HubShifts]
    ) -> Optional[HubShifts]:
        """Get the current active shift based on current time"""
        try:
            current_time = datetime.utcnow().time()  # ← Extract time only

            for hub_shift in hub_shifts:
                if hub_shift.start_time <= current_time <= hub_shift.finish_time:
                    logger.info(
                        f"✅ Current shift found: {hub_shift.id} "
                        f"({hub_shift.start_time} - {hub_shift.finish_time})"
                    )
                    return hub_shift

            logger.warning(f"❌ No active shift found for current time: {current_time}")
            return None

        except Exception as e:
            logger.error(
                f"❌ Error getting current clock shift: {str(e)}", exc_info=True
            )
            return None

    async def handle_routes_with_passed_time_shift(self) -> None:
        """Handle routes that are still ongoing but their shift time has passed"""
        try:
            logger.info("Checking for routes with passed shift time...")
            current_time = datetime.utcnow().time()
            routes = (
                await self._route_repo.get_not_finished_routes_with_passed_shift_time(
                    current_time
                )
            )

            for route in routes:
                route.status = RouteStatesType.CANCELLED

                # Update missions status
                missions = await self._mission_repo.get_by_route_id(route.id)
                for mission in missions:
                    if mission.status not in [
                        MissionStatusType.DELIVERED,
                    ]:
                        mission.status = MissionStatusType.CANCELLED.value
                        await self._mission_repo.update(mission.id, mission)

                    # Update orders status
                    order = await self._order_repo.get_by_id(mission.order_id)
                    order.status = OrderStatusTypes.UNASSIGNED
                    await self._order_repo.update(order.id, order)

                await self._route_repo.update(route.id, route)
                logger.info(
                    f"Updated route {route.id} to CANCELLED due to passed shift time"
                )
            logger.info(
                f"Checked and handled {len(routes)} routes for passed shift time"
            )
        except Exception as e:
            logger.error(
                f"Error handling routes with passed shift time: {str(e)}", exc_info=True
            )
