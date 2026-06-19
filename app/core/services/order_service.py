"""
Order service implementation
"""

import logging
from uuid import UUID, uuid4
from datetime import datetime, date, time
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.entities import (
    Order,
    OrderStatusTypes,
    Recipient,
    TimeWindow,
    User,
    UserStatus,
    Role,
    RoleType,
)
from app.core.interfaces import (
    IOrderRepository,
    IRecipientRepository,
    ICourierRepository,
    IHubRepository,
    IHubShiftRepository,
    IUserRepository,
    IRoleRepository,
    IOrderService,
    IAuthService,
)
from app.api.v1.schemas.order_schemas import (
    CreateOrderRequest,
    UpdateOrderRequest,
    PostponeOrdersRequest,
)
from app.adapters.filters.order_filter import OrderFilter

logger = logging.getLogger(__name__)


class OrderService(IOrderService):
    """Order service implementation"""

    def __init__(
        self,
        order_repo: IOrderRepository,
        recipient_repo: IRecipientRepository,
        courier_repo: ICourierRepository,
        hub_repo: IHubRepository,
        hub_shift_repo: IHubShiftRepository,
        user_repo: IUserRepository,
        role_repo: IRoleRepository,
        auth_service: IAuthService,
        session: AsyncSession,
    ):
        self.order_repo = order_repo
        self.recipient_repo = recipient_repo
        self.courier_repo = courier_repo
        self.hub_repo = hub_repo
        self.hub_shift_repo = hub_shift_repo
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.auth_service = auth_service
        self.session = session

    async def create_order(
        self,
        user_id: UUID,
        terminal_id: UUID,
        shift_id: UUID,
        order_request: CreateOrderRequest,
    ) -> Order:
        """
        Create a new order

        Args:
            user_id: Current user (courier) ID
            terminal_id: Hub UUID
            shift_id: Shift UUID
            order_request: Order creation request

        Returns:
            Created order

        Raises:
            ValueError: If validation fails
            HTTPException: If entity not found
        """
        try:
            logger.info(f"🔄 Creating order with barcode: {order_request.barcode}")

            # Step 1: Retrieve courier
            courier = await self.courier_repo.get_by_user_id(user_id)
            if not courier:
                logger.error(f"❌ Courier not found for user: {user_id}")
                raise ValueError(f"Courier not found for user {user_id}")

            # Step 2: Retrieve and validate hub
            hub = await self.hub_repo.get_by_id(terminal_id)
            if not hub:
                logger.error(f"❌ Hub not found: {terminal_id}")
                raise ValueError(f"Hub not found: {terminal_id}")

            # Step 3: Retrieve and validate shift
            shift = await self.hub_shift_repo.get_by_id(shift_id)
            if not shift:
                logger.error(f"❌ Shift not found: {shift_id}")
                raise ValueError(f"Shift not found: {shift_id}")

            # Step 4: Validate shift belongs to hub
            if shift.terminal_id != terminal_id:
                logger.error(
                    f"❌ Shift {shift_id} does not belong to hub {terminal_id}"
                )
                raise ValueError(
                    f"Shift {shift_id} does not belong to hub {terminal_id}"
                )

            # Step 5: Check barcode uniqueness
            if await self.order_repo.barcode_exists(order_request.barcode):
                logger.error(f"❌ Barcode already exists: {order_request.barcode}")
                raise ValueError(
                    f"Order with barcode {order_request.barcode} already exists"
                )

            # Step 6: Build time window from shift
            if not order_request.expected_delivery_date:
                order_request.expected_delivery_date = datetime.utcnow().date()

            if order_request.time_window:
                time_window = TimeWindow(
                    earliest=datetime.combine(
                        order_request.expected_delivery_date,
                        order_request.time_window.earliest,
                    ),
                    latest=datetime.combine(
                        order_request.expected_delivery_date,
                        order_request.time_window.latest,
                    ),
                )
            else:
                time_window = TimeWindow(
                    earliest=datetime.combine(
                        order_request.expected_delivery_date, shift.start_time
                    ),
                    latest=datetime.combine(
                        order_request.expected_delivery_date, shift.finish_time
                    ),
                )

            # Step 7: Get or create recipient user
            try:
                recipient_user = await self.user_repo.get_by_phone(
                    order_request.recipient.phone_number
                )

                if not recipient_user:
                    logger.info(
                        f"🔄 check email: {order_request.recipient.phone_number}"
                    )

                    recipient_user = await self.user_repo.get_by_email(
                        order_request.recipient.email
                    )
                    if not recipient_user:
                        logger.info(
                            f"🔄 Creating new user for recipient: {order_request.recipient.phone_number}"
                        )
                        # Get recipient role
                        recipient_role = await self.role_repo.get_by_name(
                            RoleType.RECIPIENT
                        )
                        if not recipient_role:
                            logger.error("❌ Recipient role not found")
                            raise ValueError("Recipient role not found in system")

                        # Hash password with phone number as default
                        hashed_password = await self.auth_service.hash_password(
                            order_request.recipient.phone_number
                        )

                        # Create new user
                        recipient_user = User(
                            id=uuid4(),
                            username=order_request.recipient.phone_number,
                            password_hash=hashed_password,
                            status=UserStatus.ACTIVE,
                            email=order_request.recipient.email,
                            first_name=order_request.recipient.name,
                            last_name="",
                            phone_number=order_request.recipient.phone_number,
                            role=recipient_role,
                            timezone="UTC",
                            currency="USD",
                        )

                        recipient_user = await self.user_repo.create(recipient_user)
                        await self.session.commit()
                        logger.info(f"✅ Recipient user created: {recipient_user.id}")

            except Exception as e:
                await self.session.rollback()
                logger.error(f"❌ Error creating/retrieving recipient user: {str(e)}")
                raise

            # Step 8: Get or create/update recipient
            try:
                recipient = await self.recipient_repo.get_by_user_id(recipient_user.id)

                if not recipient:
                    logger.info(
                        f"🔄 Creating new recipient for user: {recipient_user.id}"
                    )

                    new_recipient = Recipient(
                        id=uuid4(),
                        user_id=recipient_user.id,
                        location=order_request.recipient.location,
                        address=order_request.recipient.address,
                    )

                    recipient = await self.recipient_repo.create(new_recipient)
                    logger.info(f"✅ Recipient created: {recipient.id}")

                else:
                    logger.info(f"🔄 Updating existing recipient: {recipient.id}")

                    # Update recipient with new location and address
                    recipient.location = order_request.recipient.location
                    recipient.address = order_request.recipient.address

                    recipient = await self.recipient_repo.update(
                        recipient.id, recipient
                    )
                    logger.info(f"✅ Recipient updated: {recipient.id}")

                await self.session.commit()

            except Exception as e:
                await self.session.rollback()
                logger.error(f"❌ Error creating/updating recipient: {str(e)}")
                raise

            # Step 9: Create order
            try:
                logger.info(f"🔄 Creating order entity: {order_request.barcode}")

                order = Order(
                    id=uuid4(),
                    terminal_id=hub.id,
                    shift_id=shift.id,
                    courier_id=courier.id,
                    recipient_id=recipient.id,
                    name=order_request.name,
                    barcode=order_request.barcode,
                    status=OrderStatusTypes.REGISTERED,
                    time_window=time_window,
                    weight_occupation=order_request.weight_occupation,
                    volume_occupation=order_request.volume_occupation,
                    expected_delivery_date=order_request.expected_delivery_date,
                    is_return=order_request.is_return,
                )

                created_order = await self.order_repo.create(order, commit=False)
                await self.session.commit()

                # Fetch complete order with all relationships
                complete_order = await self.order_repo.get_by_id(created_order.id)

                logger.info(f"✅ Order created successfully: {created_order.id}")
                return complete_order

            except Exception as e:
                await self.session.rollback()
                logger.error(f"❌ Error creating order: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"❌ Error in create_order service: {str(e)}", exc_info=True)
            raise

    async def get_order_by_id(self, order_id: UUID) -> Optional[Order]:
        """
        Get order by ID

        Args:
            order_id: Order UUID

        Returns:
            Order or None if not found
        """
        try:
            logger.info(f"🔄 Getting order by ID: {order_id}")
            order = await self.order_repo.get_by_id(order_id)

            if not order:
                logger.debug(f"Order not found: {order_id}")
                return None

            recipient = await self.recipient_repo.get_by_id(order.recipient_id)
            if not recipient:
                logger.error(f"❌ Recipient not found for order: {order_id}")
                raise ValueError(f"Recipient not found for order: {order_id}")

            user = await self.user_repo.get_by_id(recipient.user_id)
            if not user:
                logger.error(f"❌ User not found for recipient: {recipient.id}")
                raise ValueError(f"User not found for recipient: {recipient.id}")

            logger.info(f"✅ Order retrieved: {order_id}")
            return order, recipient, user

        except Exception as e:
            logger.error(f"❌ Error getting order: {str(e)}", exc_info=True)
            raise

    async def get_courier_orders(
        self, user_id: UUID, skip: int = 0, limit: int = 10
    ) -> List[Order]:
        """
        Get all orders for a courier

        Args:
            courier_id: Courier UUID
            skip: Pagination skip
            limit: Pagination limit

        Returns:
            List of orders
        """
        try:

            courier = await self.courier_repo.get_by_user_id(user_id)
            if not courier:
                logger.error(f"❌ Courier not found for user: {user_id}")
                raise ValueError(f"Courier not found for user: {user_id}")

            courier_id = courier.id
            logger.info(
                f"🔄 Getting orders for courier: {courier_id} "
                f"(skip={skip}, limit={limit})"
            )

            orders = await self.order_repo.get_by_courier_id(
                courier_id, skip=skip, limit=limit
            )
            recipients = [
                await self.recipient_repo.get_by_id(order.recipient_id)
                for order in orders
            ]
            users = [
                await self.user_repo.get_by_id(recipient.user_id)
                for recipient in recipients
            ]
            total_count = await self.order_repo.count_by_courier_id(courier_id)

            logger.info(f"✅ Retrieved {len(orders)} orders for courier")
            return orders, recipients, users, total_count

        except Exception as e:
            logger.error(f"❌ Error getting courier orders: {str(e)}", exc_info=True)
            raise

    async def get_unassigned_orders(
        self, user_id: UUID, skip: int = 0, limit: int = 10
    ) -> List[Order]:
        """
        Get unassigned orders for a courier

        Args:
            courier_id: Courier UUID
            skip: Pagination skip
            limit: Pagination limit

        Returns:
            List of unassigned orders
        """
        try:

            courier = await self.courier_repo.get_by_user_id(user_id)
            if not courier:
                logger.error(f"❌ Courier not found for user: {user_id}")
                raise ValueError(f"Courier not found for user: {user_id}")

            courier_id = courier.id
            logger.info(f"🔄 Getting unassigned orders for courier: {courier_id}")

            orders = await self.order_repo.get_by_courier_and_status(
                skip=skip,
                limit=limit,
                courier_id=courier_id,
                status=OrderStatusTypes.UNASSIGNED,
            )

            total_count = await self.order_repo.count_by_courier_id_and_status(
                courier_id=courier_id, status=OrderStatusTypes.UNASSIGNED
            )

            logger.info(f"✅ Retrieved {len(orders)} unassigned orders")
            return orders, total_count

        except Exception as e:
            logger.error(f"❌ Error getting unassigned orders: {str(e)}", exc_info=True)
            raise

    async def filter_orders(
        self,
        filter_params: OrderFilter,
        skip: int = 0,
        limit: int = 10,
    ) -> Tuple[List[Order], int]:
        """
        Filter orders with params

        Args:
            filter_params: Filter parameters
            skip: Pagination skip
            limit: Pagination limit

        Returns:
            Tuple of (orders list, total count)
        """
        try:
            logger.info(
                f"🔄 Filtering orders with params " f"(skip={skip}, limit={limit})"
            )

            orders, total_count = await self.order_repo.filter_orders(
                filter_params, skip=skip, limit=limit
            )

            recipients = [
                await self.recipient_repo.get_by_id(order.recipient_id)
                for order in orders
            ]
            users = [
                await self.user_repo.get_by_id(recipient.user_id)
                for recipient in recipients
            ]

            logger.info(f"✅ Retrieved {len(orders)} filtered orders")
            return orders, recipients, users, total_count

        except Exception as e:
            logger.error(f"❌ Error filtering orders: {str(e)}", exc_info=True)
            raise

    async def update_order(
        self,
        order_id: UUID,
        order_request: UpdateOrderRequest,
        user_id: UUID,
    ) -> Order:
        """
        Update an order

        Args:
            order_id: Order UUID
            order_request: Update request
            user_id: Current user ID for authorization

        Returns:
            Updated order

        Raises:
            ValueError: If order not found or invalid state
        """
        try:
            logger.info(f"🔄 Updating order: {order_id}")

            # Get current order
            current_order = await self.order_repo.get_by_id(order_id)
            if not current_order:
                logger.error(f"❌ Order not found: {order_id}")
                raise ValueError(f"Order not found: {order_id}")

            # Get recipient and validate authorization
            recipient = await self.recipient_repo.get_by_id(current_order.recipient_id)
            if not recipient:
                logger.error(f"❌ Recipient not found: {current_order.recipient_id}")
                raise ValueError(f"Recipient not found: {current_order.recipient_id}")

            courier = await self.courier_repo.get_by_user_id(user_id)
            if courier and courier.id != current_order.courier_id:
                logger.warning(
                    f"❌ User {user_id} not authorized to update order {order_id}"
                )
                raise ValueError(
                    f"User {user_id} not authorized to update order {order_id}"
                )

            # Check order status allows update
            if current_order.status not in [
                OrderStatusTypes.REGISTERED,
                OrderStatusTypes.POSTPONED,
            ]:
                logger.error(
                    f"❌ Cannot update order with status: {current_order.status}"
                )
                raise ValueError(
                    f"Cannot update order with status: {current_order.status.value}"
                )

            # Update order fields
            try:
                if order_request.name:
                    current_order.name = order_request.name
                if order_request.barcode:
                    # Check barcode uniqueness if changing
                    if order_request.barcode != current_order.barcode:
                        if await self.order_repo.barcode_exists(order_request.barcode):
                            logger.error(
                                f"❌ Barcode already exists: {order_request.barcode}"
                            )
                            raise ValueError(
                                f"Barcode already exists: {order_request.barcode}"
                            )
                    current_order.barcode = order_request.barcode

                if order_request.weight_occupation is not None:
                    current_order.weight_occupation = order_request.weight_occupation
                if order_request.volume_occupation is not None:
                    current_order.volume_occupation = order_request.volume_occupation
                if order_request.expected_delivery_date:
                    current_order.expected_delivery_date = (
                        order_request.expected_delivery_date
                    )
                if order_request.is_return is not None:
                    current_order.is_return = order_request.is_return

                # Update order
                updated_order = await self.order_repo.update(
                    order_id, current_order, commit=False
                )

                # Update recipient if location/address provided
                if order_request.recipient and order_request.recipient.location:
                    recipient.location = order_request.recipient.location

                if order_request.recipient and order_request.recipient.address:
                    recipient.address = order_request.recipient.address

                await self.recipient_repo.update(recipient.id, recipient, commit=False)

                await self.session.commit()

                logger.info(f"✅ Order updated: {order_id}")
                return updated_order

            except Exception as e:
                await self.session.rollback()
                logger.error(f"❌ Error updating order: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"❌ Error in update_order service: {str(e)}", exc_info=True)
            raise

    async def delete_order(self, order_id: UUID, user_id: UUID) -> bool:
        """
        Delete an order

        Args:
            order_id: Order UUID
            user_id: Current user ID for authorization

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If order not found or invalid state
        """
        try:
            logger.info(f"🔄 Deleting order: {order_id}")

            order = await self.order_repo.get_by_id(order_id)
            if not order:
                logger.error(f"❌ Order not found: {order_id}")
                raise ValueError(f"Order not found: {order_id}")

            # Get recipient for authorization check
            recipient = await self.recipient_repo.get_by_id(order.recipient_id)
            if not recipient or recipient.user_id != user_id:
                logger.warning(
                    f"❌ User {user_id} not authorized to delete order {order_id}"
                )
                raise ValueError(f"User not authorized to delete this order")

            # Check order status allows deletion
            if order.status == OrderStatusTypes.REGISTERED:
                # Hard delete for registered orders
                logger.info(f"🔄 Hard deleting order (status: REGISTERED): {order_id}")
                try:
                    deleted = await self.order_repo.delete(order_id, commit=False)
                    await self.session.commit()

                    if deleted:
                        logger.info(f"✅ Order hard deleted: {order_id}")
                        return True
                    else:
                        logger.error(f"❌ Failed to delete order: {order_id}")
                        return False

                except Exception as e:
                    await self.session.rollback()
                    logger.error(f"❌ Error hard deleting order: {str(e)}")
                    raise

            elif order.status in [
                OrderStatusTypes.POSTPONED,
                OrderStatusTypes.UNASSIGNED,
            ]:
                # Soft delete by cancelling
                logger.info(f"🔄 Soft deleting order by cancelling: {order_id}")
                try:
                    order.cancel()
                    updated_order = await self.order_repo.update(
                        order_id, order, commit=False
                    )
                    await self.session.commit()

                    logger.info(f"✅ Order cancelled (soft deleted): {order_id}")
                    return True

                except Exception as e:
                    await self.session.rollback()
                    logger.error(f"❌ Error cancelling order: {str(e)}")
                    raise

            else:
                logger.error(f"❌ Cannot delete order with status: {order.status}")
                raise ValueError(
                    f"Cannot delete order with status: {order.status.value}"
                )

        except Exception as e:
            logger.error(f"❌ Error in delete_order service: {str(e)}", exc_info=True)
            raise

    async def postpone_orders(
        self,
        request: PostponeOrdersRequest,
        user_id: UUID,
    ) -> List[Order]:
        """
        Postpone multiple orders

        Args:
            request: Postpone request with order IDs and new delivery date
            user_id: Current user ID for authorization

        Returns:
            List of postponed orders

        Raises:
            ValueError: If validation fails
        """
        try:
            logger.info(
                f"🔄 Postponing {len(request.order_ids)} orders to "
                f"{request.new_delivery_date}"
            )

            current_time = datetime.utcnow()
            current_date = current_time.date()

            # Step 1: Validate postpone date
            if request.new_delivery_date < current_date:
                logger.error(
                    f"❌ Postpone date has passed: {request.new_delivery_date}"
                )
                raise ValueError(
                    f"Postpone date has passed: {request.new_delivery_date}"
                )

            # Step 2: Get and validate hub
            hub = await self.hub_repo.get_by_id(request.terminal_id)
            if not hub:
                logger.error(f"❌ Hub not found: {request.terminal_id}")
                raise ValueError(f"Hub not found: {request.terminal_id}")

            # Step 3: Get and validate shift
            hub_shift = await self.hub_shift_repo.get_by_id(request.shift_id)
            if not hub_shift:
                logger.error(f"❌ Shift not found: {request.shift_id}")
                raise ValueError(f"Shift not found: {request.shift_id}")

            # Step 4: Validate shift belongs to hub
            if hub_shift.terminal_id != hub.id:
                logger.error(
                    f"❌ Shift {request.shift_id} does not belong to hub {request.terminal_id}"
                )
                raise ValueError(f"Shift does not belong to specified hub")

            # Step 5: Validate shift time if postponing to today
            if request.new_delivery_date == current_date:
                if current_time.time() >= hub_shift.finish_time:
                    logger.error(f"❌ Shift time has passed for today")
                    raise ValueError(f"Shift time has passed for today")

            # Step 6: Postpone orders
            try:
                postponed_orders = await self.order_repo.postpone_orders(
                    order_ids=request.order_ids,
                    terminal_id=hub.id,
                    shift_id=hub_shift.id,
                    delivery_date=request.new_delivery_date,
                    commit=False,
                )

                await self.session.commit()

                logger.info(f"✅ Postponed {len(postponed_orders)} orders")
                return postponed_orders

            except Exception as e:
                await self.session.rollback()
                logger.error(f"❌ Error postponing orders: {str(e)}")
                raise

        except Exception as e:
            logger.error(
                f"❌ Error in postpone_orders service: {str(e)}", exc_info=True
            )
            raise

    async def mark_delivered(self, order_id: UUID) -> Order:
        """
        Mark order as delivered

        Args:
            order_id: Order UUID

        Returns:
            Updated order

        Raises:
            ValueError: If order not found or invalid state
        """
        try:
            logger.info(f"🔄 Marking order as delivered: {order_id}")

            order = await self.order_repo.get_by_id(order_id)
            if not order:
                logger.error(f"❌ Order not found: {order_id}")
                raise ValueError(f"Order not found: {order_id}")

            if order.status == OrderStatusTypes.DELIVERED:
                logger.error(f"❌ Order already delivered: {order_id}")
                raise ValueError(f"Order already delivered")

            try:
                order.status = OrderStatusTypes.DELIVERED
                order.actual_delivery_date = datetime.utcnow().date()

                updated_order = await self.order_repo.update(
                    order_id, order, commit=False
                )
                await self.session.commit()

                logger.info(f"✅ Order marked as delivered: {order_id}")
                return updated_order

            except Exception as e:
                await self.session.rollback()
                logger.error(f"❌ Error marking order as delivered: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"❌ Error in mark_delivered service: {str(e)}", exc_info=True)
            raise

    async def mark_returned(self, order_id: UUID) -> Order:
        """
        Mark order as returned

        Args:
            order_id: Order UUID

        Returns:
            Updated order

        Raises:
            ValueError: If order not found or invalid state
        """
        try:
            logger.info(f"🔄 Marking order as returned: {order_id}")

            order = await self.order_repo.get_by_id(order_id)
            if not order:
                logger.error(f"❌ Order not found: {order_id}")
                raise ValueError(f"Order not found: {order_id}")

            if order.is_return:
                logger.error(f"❌ Order already marked as return: {order_id}")
                raise ValueError(f"Order already marked as return")

            try:
                order.is_return = True
                order.status = OrderStatusTypes.RETURNED

                updated_order = await self.order_repo.update(
                    order_id, order, commit=False
                )
                await self.session.commit()

                logger.info(f"✅ Order marked as returned: {order_id}")
                return updated_order

            except Exception as e:
                await self.session.rollback()
                logger.error(f"❌ Error marking order as returned: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"❌ Error in mark_returned service: {str(e)}", exc_info=True)
            raise

    async def mark_cancelled(self, order_id: UUID) -> Order:
        """
        Mark order as cancelled

        Args:
            order_id: Order UUID

        Returns:
            Updated order

        Raises:
            ValueError: If order not found or invalid state
        """
        try:
            logger.info(f"🔄 Marking order as cancelled: {order_id}")

            order = await self.order_repo.get_by_id(order_id)
            if not order:
                logger.error(f"❌ Order not found: {order_id}")
                raise ValueError(f"Order not found: {order_id}")

            if order.status == OrderStatusTypes.CANCELLED:
                logger.error(f"❌ Order already cancelled: {order_id}")
                raise ValueError(f"Order already cancelled")

            try:
                order.cancel()

                updated_order = await self.order_repo.update(
                    order_id, order, commit=False
                )
                await self.session.commit()

                logger.info(f"✅ Order marked as cancelled: {order_id}")
                return updated_order

            except Exception as e:
                await self.session.rollback()
                logger.error(f"❌ Error marking order as cancelled: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"❌ Error in mark_cancelled service: {str(e)}", exc_info=True)
            raise
