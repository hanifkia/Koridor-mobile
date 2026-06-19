# app/core/services/courier_state_service.py
"""
Courier state management service
"""
import logging
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Dict, Any

from app.core.entities import (
    CourierCurrentState,
    CourierStatesType,
    MissionStatusType,
    OrderStatusTypes,
    RouteStatesType,
)
from app.core.interfaces import (
    ICourierCurrentStateRepository,
    IRouteRepository,
    IMissionRepository,
    ICourierRepository,
    IOrderRepository,
)
from app.api.v1.schemas.states_schemas import SetCourierStateRequestSchema

logger = logging.getLogger(__name__)


class CourierStateService:
    """Service for managing courier state transitions and mission updates"""

    def __init__(
        self,
        current_state_repo: ICourierCurrentStateRepository,
        route_repo: IRouteRepository,
        mission_repo: IMissionRepository,
        courier_repo: ICourierRepository,
        order_repo: IOrderRepository,
        billing_service,
    ):
        self.current_state_repo = current_state_repo
        self.route_repo = route_repo
        self.mission_repo = mission_repo
        self.courier_repo = courier_repo
        self.order_repo = order_repo
        self.billing_service = billing_service

    async def set_courier_state(
        self,
        user_id: UUID,
        request: SetCourierStateRequestSchema,
    ) -> Dict[str, Any]:
        """
        Update courier state and handle mission status transitions.

        **State Transitions:**
        - ARRIVEDATHUB: Courier arrived at hub
        - STARTLOADING: Start loading packages
        - STARTROUTE: Start route with first mission
        - ARRIVEDATDELIVERY: Arrived at delivery location
        - DELIVERED: Order successfully delivered
        - UNDELIVERED: Order not delivered (requires undeliver_type)
        - STARTNEXTDELIVERY: Move to next mission
        - RETURNTOHUB: Return to hub
        - FINISHROUTE: Route completed

        **Validation:**
        1. Get and verify courier
        2. Get or create courier current state
        3. Validate route and courier-route assignment
        4. Validate order and mission if required
        5. Process state-specific logic
        6. Update all entities

        **Returns:**
        - Dictionary with operation result

        **Raises:**
        - ValueError: If validation fails
        - Exception: If state transition fails
        """
        logger.info(f"🔄 Setting courier state for user: {user_id}")

        # Get courier
        courier = await self._get_courier(user_id)

        # Get or create courier current state
        courier_current_state = await self._get_or_create_courier_state(
            courier.id, request
        )

        # Validate route
        route = await self._validate_route(request.route_id, courier.id)

        # Validate and get order/mission if required
        order, mission = await self._validate_order_and_mission(
            request.state, request.order_id, request.route_id
        )

        # Process state-specific logic
        logger.info(f"🔄 Processing state: {request.state.value}")
        await self._process_state_logic(
            request.state,
            route,
            mission,
            order,
            courier,
            request,
        )

        # Update route and courier state
        route = await self.route_repo.update(request.route_id, route)
        courier_current_state = await self.current_state_repo.update_state(
            courier.id, request.state
        )

        logger.info(
            f"✅ Courier state updated: courier={courier.id}, state={request.state.value}, "
            f"route={request.route_id}"
        )

        return {
            "status": "success",
            "message": f"Courier state updated to {request.state.value}",
            "courier_id": str(courier.id),
            "state": request.state.value,
            "route_id": str(request.route_id),
            "order_id": str(request.order_id) if request.order_id else None,
            "delivered_orders": [
                str(oid) for oid in courier_current_state.delivered_order_ids
            ],
            "current_mission_id": (
                str(route.current_mission_id) if route.current_mission_id else None
            ),
        }

    async def _get_courier(self, user_id: UUID):
        """Get courier by user ID with validation"""
        logger.info(f"🔍 Getting courier for user {user_id}")
        courier = await self.courier_repo.get_by_user_id(user_id)

        if not courier:
            logger.error(f"❌ Courier not found for user {user_id}")
            raise ValueError(f"Courier not found for user {user_id}")

        logger.info(f"✅ Courier found: {courier.id}")
        return courier

    async def _get_or_create_courier_state(
        self, courier_id: UUID, request: SetCourierStateRequestSchema
    ):
        """Get existing courier state or create new one"""
        logger.info(f"🔍 Getting current state for courier {courier_id}")
        courier_current_state = await self.current_state_repo.get_by_courier_id(
            courier_id
        )

        if not courier_current_state:
            logger.info(f"📝 Creating new courier state for courier {courier_id}")
            courier_current_state = CourierCurrentState(
                id=uuid4(),
                courier_id=courier_id,
                delivered_order_ids=[request.order_id] if request.order_id else [],
                state=request.state,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            courier_current_state = await self.current_state_repo.create(
                courier_current_state
            )
            logger.info(f"✅ Created new courier state: {courier_current_state.id}")
        elif courier_current_state.state == request.state:
            logger.info(
                f"ℹ️ Courier {courier_id} state already set to {request.state.value}"
            )

        return courier_current_state

    async def _validate_route(self, route_id: UUID, courier_id: UUID):
        """Validate route exists and is assigned to courier"""
        logger.info(f"🔍 Getting route {route_id}")
        route = await self.route_repo.get_by_id(route_id)

        if not route:
            logger.error(f"❌ Route not found: {route_id}")
            raise ValueError(f"Route {route_id} not found")

        logger.info(f"✅ Route found: {route.id}")

        if route.courier_id != courier_id:
            logger.error(f"❌ Route {route_id} not assigned to courier {courier_id}")
            raise ValueError(
                f"Route {route_id} is not assigned to courier {courier_id}"
            )

        logger.info(f"✅ Route correctly assigned to courier")
        return route

    async def _validate_order_and_mission(
        self,
        state: CourierStatesType,
        order_id: Optional[UUID],
        route_id: UUID,
    ):
        """Validate order and mission if required by state"""
        states_requiring_order = {
            CourierStatesType.STARTROUTE,
            CourierStatesType.ARRIVEDATDELIVERY,
            CourierStatesType.DELIVERED,
            CourierStatesType.UNDELIVERED,
            CourierStatesType.STARTNEXTDELIVERY,
            CourierStatesType.RETURNTOHUB,
        }

        if state not in states_requiring_order:
            return None, None

        if not order_id:
            logger.error(f"❌ order_id is required for state {state.value}")
            raise ValueError(f"order_id is required for state {state.value}")

        # Get order
        logger.info(f"🔍 Getting order {order_id}")
        order = await self.order_repo.get_by_id(order_id)

        if not order:
            logger.error(f"❌ Order not found: {order_id}")
            raise ValueError(f"Order {order_id} not found")

        logger.info(f"✅ Order found: {order.id}")

        # Get mission
        logger.info(f"🔍 Getting mission for order {order_id} in route {route_id}")
        mission = await self.mission_repo.get_by_order_id_and_route_id(
            order_id, route_id
        )

        if not mission:
            logger.error(
                f"❌ Mission not found for order {order_id} in route {route_id}"
            )
            raise ValueError(
                f"Mission not found for order {order_id} in route {route_id}"
            )

        logger.info(f"✅ Mission found: {mission.id}")
        return order, mission

    async def _process_state_logic(
        self,
        state: CourierStatesType,
        route,
        mission,
        order,
        courier,
        request: SetCourierStateRequestSchema,
    ):
        """Process state-specific business logic"""
        if state == CourierStatesType.ARRIVEDATHUB:
            await self._handle_arrived_at_hub(route)

        elif state == CourierStatesType.STARTLOADING:
            await self._handle_start_loading(route)

        elif state == CourierStatesType.STARTROUTE:
            await self._handle_start_route(route, mission)

        elif state == CourierStatesType.ARRIVEDATDELIVERY:
            await self._handle_arrived_at_delivery(mission, order)

        elif state == CourierStatesType.DELIVERED:
            await self._handle_delivered(mission, order, courier, request)

        elif state == CourierStatesType.UNDELIVERED:
            await self._handle_undelivered(mission, order, request)

        elif state == CourierStatesType.STARTNEXTDELIVERY:
            await self._handle_start_next_delivery(route, mission)

        elif state == CourierStatesType.RETURNTOHUB:
            await self._handle_return_to_hub(route, mission)

        elif state == CourierStatesType.FINISHROUTE:
            await self._handle_finish_route(route, courier, request.route_id)

    async def _handle_arrived_at_hub(self, route):
        """Handle ARRIVEDATHUB state"""
        route.arrived_at_hub_time = datetime.utcnow()
        logger.info(f"✅ Route {route.id}: Courier arrived at hub")

    async def _handle_start_loading(self, route):
        """Handle STARTLOADING state"""
        route.status = RouteStatesType.LOADING.value
        route.loading_time_start = datetime.utcnow()
        logger.info(f"✅ Route {route.id}: Loading started")

    async def _handle_start_route(self, route, mission):
        """Handle STARTROUTE state"""
        route.status = RouteStatesType.ONGOING.value
        route.actual_start_time = datetime.utcnow().time()
        route.current_mission_id = mission.id

        # Update all missions to ONGOING
        await self.mission_repo.update_missions_status_by_route(
            route.id, MissionStatusType.ONGOING.value
        )

        logger.info(f"✅ Route {route.id}: Route started with mission {mission.id}")

    async def _handle_arrived_at_delivery(self, mission, order):
        """Handle ARRIVEDATDELIVERY state"""
        mission.actual_arrival_time = datetime.utcnow().time()

        # Calculate waiting time
        if (
            order.time_window.earliest
            and mission.actual_arrival_time < order.time_window.earliest
        ):
            time_diff = datetime.combine(
                datetime.now().date(), order.time_window.earliest
            ) - datetime.combine(datetime.now().date(), mission.actual_arrival_time)
            mission.actual_waiting_time = int(time_diff.total_seconds() / 60)
        else:
            mission.actual_waiting_time = 0

        mission = await self.mission_repo.update(mission.id, mission)
        logger.info(
            f"✅ Mission {mission.id}: Arrived at delivery (waiting: {mission.actual_waiting_time}min)"
        )

    async def _handle_delivered(
        self, mission, order, courier, request: SetCourierStateRequestSchema
    ):
        """Handle DELIVERED state"""
        mission.status = MissionStatusType.DELIVERED.value
        mission.delivery_scan_parcel_time = datetime.utcnow()
        mission.courier_comment = request.comment

        # Check for delay
        if (
            order.time_window.latest
            and mission.delivery_scan_parcel_time.time() > order.time_window.latest
        ):
            mission.status = MissionStatusType.DELIVERED_WITH_DELAY.value

        order.status = OrderStatusTypes.DELIVERED
        order.actual_delivery_date = datetime.utcnow()

        mission = await self.mission_repo.update(mission.id, mission)
        order = await self.order_repo.update(order.id, order)

        # Add to delivered orders
        await self.current_state_repo.add_delivered_order(courier.id, request.order_id)

        logger.info(f"✅ Order {order.id}: Delivered (status: {mission.status})")
        await self.billing_service.record_delivery(courier.user_id)

    async def _handle_undelivered(
        self, mission, order, request: SetCourierStateRequestSchema
    ):
        """Handle UNDELIVERED state"""
        if not request.undeliver_type:
            logger.error("❌ undeliver_type is required for UNDELIVERED state")
            raise ValueError("undeliver_type is required for UNDELIVERED state")

        mission.status = request.undeliver_type.value
        mission.delivery_scan_parcel_time = datetime.utcnow()
        mission.courier_comment = request.comment
        mission.postponed = request.undeliver_type.value

        order.status = OrderStatusTypes.POSTPONED

        mission = await self.mission_repo.update(mission.id, mission)
        order = await self.order_repo.update(order.id, order)

        logger.info(
            f"✅ Order {order.id}: Undelivered (reason: {request.undeliver_type.value})"
        )

    async def _handle_start_next_delivery(self, route, mission):
        """Handle STARTNEXTDELIVERY state"""
        self._complete_mission(mission)
        mission = await self.mission_repo.update(mission.id, mission)

        # Get next mission
        next_mission = await self.mission_repo.get_next_by_position(
            route.id, (mission.position_in_route or 0) + 1
        )

        if next_mission:
            route.current_mission_id = next_mission.id
            # TODO: I think we need to update route here
            await self.route_repo.update(route.id, route)
            logger.info(f"✅ Moving to next mission: {next_mission.id}")
        else:
            logger.warning(
                f"⚠️ No next mission found after position {mission.position_in_route}"
            )

    async def _handle_return_to_hub(self, route, mission):
        """Handle RETURNTOHUB state"""
        route.status = RouteStatesType.RETURNTOHUB.value
        self._complete_mission(mission)
        mission = await self.mission_repo.update(mission.id, mission)
        logger.info(f"✅ Route {route.id}: Returning to hub")

    async def _handle_finish_route(self, route, courier, route_id: UUID):
        """Handle FINISHROUTE state"""
        # Complete current mission
        if route.current_mission_id:
            current_mission = await self.mission_repo.get_by_id(
                route.current_mission_id
            )
            if current_mission and not current_mission.actual_mission_finish_time:
                self._complete_mission(current_mission)
                await self.mission_repo.update(current_mission.id, current_mission)

        route.status = RouteStatesType.FINISHED.value
        route.actual_finish_time = datetime.utcnow().time()

        # Get total waiting time
        total_waiting_time = await self.mission_repo.get_total_waiting_time(route_id)
        route.total_actual_waiting_time = total_waiting_time

        # Reset courier state
        await self.current_state_repo.clear_delivered_orders(courier.id)
        await self.current_state_repo.update_state(courier.id, CourierStatesType.IDLE)

        logger.info(f"✅ Route completed (waiting: {total_waiting_time}min)")

    @staticmethod
    def _complete_mission(mission) -> None:
        """Mark mission as completed and calculate service time"""
        mission.actual_mission_finish_time = datetime.utcnow().time()

        if mission.actual_arrival_time:
            # Calculate service time
            arrival = datetime.combine(
                datetime.now().date(), mission.actual_arrival_time
            )
            finish = datetime.combine(
                datetime.now().date(), mission.actual_mission_finish_time
            )
            mission.actual_service_time = int((finish - arrival).total_seconds())

    async def set_parcel_loading(
        self,
        route_id: UUID,
        barcode: str,
    ) -> Dict[str, Any]:
        """
        Mark a parcel as loaded by scanning barcode.

        **Validation:**
        1. Verify route exists
        2. Find order by barcode (exclude cancelled orders)
        3. Find mission for order in route
        4. Mark mission as loaded
        5. Count remaining parcels to load

        **Returns:**
        - Dictionary with remaining parcels count

        **Raises:**
        - ValueError: If route, order, or mission not found
        """
        logger.info(
            f"🔄 Setting parcel loading for route: {route_id}, barcode: {barcode}"
        )

        # Validate route exists
        route = await self._validate_route_exists(route_id)

        # Find order by barcode
        order = await self._find_order_by_barcode(barcode)

        # Find mission for order in route
        mission = await self._find_mission_for_order_in_route(order.id, route_id)

        # Mark parcel as loaded
        mission.loading_scan_parcel_time = datetime.utcnow()
        mission = await self.mission_repo.update(mission.id, mission)
        logger.info(f"✅ Parcel loaded: mission={mission.id}, barcode={barcode}")

        # Count remaining parcels to load
        remaining_parcels = await self._get_remaining_parcels_to_load(route_id)

        logger.info(
            f"✅ Parcel loading recorded: {len(remaining_parcels)} parcels remaining"
        )

        return {"remaining_parcel_to_load": len(remaining_parcels)}

    async def _validate_route_exists(self, route_id: UUID):
        """Validate route exists"""
        logger.info(f"🔍 Validating route: {route_id}")
        route = await self.route_repo.get_by_id(route_id)

        if not route:
            logger.error(f"❌ Route not found: {route_id}")
            raise ValueError(f"Route {route_id} not found")

        logger.info(f"✅ Route validated: {route_id}")
        return route

    async def _find_order_by_barcode(self, barcode: str):
        """Find order by barcode (exclude cancelled orders)"""
        logger.info(f"🔍 Finding order with barcode: {barcode}")
        order = await self.order_repo.get_by_barcode(barcode)

        if not order:
            logger.error(f"❌ No order found for barcode: {barcode}")
            raise ValueError(f"No corresponding order is found for that barcode")

        if order.status == OrderStatusTypes.CANCELLED:
            logger.error(f"❌ Order is cancelled: {order.id}")
            raise ValueError(f"Order with barcode {barcode} is cancelled")

        logger.info(f"✅ Order found: {order.id}")
        return order

    async def _find_mission_for_order_in_route(self, order_id: UUID, route_id: UUID):
        """Find mission for order in specific route"""
        logger.info(f"🔍 Finding mission for order: {order_id} in route: {route_id}")
        mission = await self.mission_repo.get_by_order_id_and_route_id(
            order_id, route_id
        )

        if not mission:
            logger.error(
                f"❌ Mission not found for order: {order_id} in route: {route_id}"
            )
            raise ValueError("The mission is not in the current route")

        logger.info(f"✅ Mission found: {mission.id}")
        return mission

    async def _get_remaining_parcels_to_load(self, route_id: UUID):
        """Get list of parcels not yet loaded in route"""
        logger.info(f"🔍 Getting remaining parcels to load for route: {route_id}")
        remaining_missions = (
            await self.mission_repo.get_missions_by_route_without_loading_time(route_id)
        )

        logger.info(f"✅ Found {len(remaining_missions)} parcels remaining to load")
        return remaining_missions

    async def start_route_self_managed(
        self,
        user_id: UUID,
        route_id: UUID,
        sorted_order_ids: list[UUID],
    ) -> Dict[str, Any]:
        """
        Start route with self-managed loading (scan all parcels and start route).

        **Process:**
        1. Get all orders by IDs
        2. Validate orders exist
        3. Scan all parcels (mark as loaded)
        4. Set courier state to STARTROUTE

        **Returns:**
        - Dictionary with route start result

        **Raises:**
        - ValueError: If orders not found or state transition fails
        """
        logger.info(
            f"🔄 Starting self-managed route for user: {user_id}, route: {route_id}"
        )

        # Step 1: Get all orders and extract barcodes
        logger.info(f"🔍 Fetching {len(sorted_order_ids)} orders")
        orders = await self._get_orders_by_ids(sorted_order_ids)

        if not orders:
            logger.error(f"❌ No orders found for IDs: {sorted_order_ids}")
            raise ValueError("No orders found for the given route or order IDs")

        barcodes = [order.barcode for order in orders]
        logger.info(f"✅ Found {len(barcodes)} orders with barcodes")

        # Step 2: Scan all barcodes (mark parcels as loaded)
        logger.info(f"🔄 Loading all {len(barcodes)} parcels")
        for barcode in barcodes:
            try:
                await self.set_parcel_loading(route_id, barcode)
                logger.info(f"✅ Parcel loaded: {barcode}")
            except ValueError as e:
                logger.error(f"❌ Failed to load parcel {barcode}: {str(e)}")
                raise

        logger.info(f"✅ All parcels loaded successfully")

        # Step 3: Set courier state to STARTROUTE
        logger.info(f"🔄 Setting courier state to STARTROUTE")
        request = SetCourierStateRequestSchema(
            state=CourierStatesType.STARTROUTE,
            route_id=route_id,
            order_id=sorted_order_ids[0],  # First order for initial mission context
            comment=None,
            undeliver_type=None,
        )

        result = await self.set_courier_state(user_id, request)

        logger.info(f"✅ Self-managed route started successfully")
        return result

    async def _get_orders_by_ids(self, order_ids: list[UUID]):
        """Get multiple orders by IDs"""
        logger.info(f"🔍 Getting {len(order_ids)} orders")
        orders = await self.order_repo.get_by_list_of_order_ids(order_ids)

        if not orders:
            logger.error(f"❌ No orders found for IDs: {order_ids}")
            return None

        logger.info(f"✅ Found {len(orders)} orders")
        return orders
