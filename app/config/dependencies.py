# app/config/dependencies.py
"""
Dependency injection configuration with proper service layer
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi import Depends
import logging

from app.config.settings import settings

# ============ IMPORTS: REPOSITORIES ============
from app.adapters.repositories.user_repository import UserRepositoryImp
from app.adapters.repositories.role_repository import RoleRepositoryImp
from app.adapters.repositories.permission_repository import PermissionRepositoryImp
from app.adapters.repositories.refresh_token_repository import RefreshTokenRepositoryImp
from app.adapters.repositories.password_reset_repository import (
    PasswordResetRepositoryImp,
)
from app.adapters.repositories.courier_repository import CourierRepositoryImp
from app.adapters.repositories.hub_repository import HubRepositoryImp
from app.adapters.repositories.hub_shift_repository import HubShiftRepositoryImp
from app.adapters.repositories.vehicle_repository import VehicleRepositoryImp
from app.adapters.repositories.order_repository import OrderRepositoryImp
from app.adapters.repositories.recipient_repository import RecipientRepositoryImp
from app.adapters.repositories.mission_repository import MissionRepositoryImp
from app.adapters.repositories.route_repository import RouteRepositoryImp
from app.adapters.repositories.courier_current_state_repository import (
    CourierCurrentStateRepositoryImp,
)
from app.adapters.repositories.avatar_repository import AvatarRepositoryImp
from app.adapters.services.langchain.openAi import OpenAILLMRepository
from app.adapters.repositories.billing_customer_repository import (
    BillingCustomerRepositoryImp,
)
from app.adapters.repositories.plan_repository import PlanRepositoryImp
from app.adapters.repositories.plan_price_repository import PlanPriceRepositoryImp
from app.adapters.repositories.subscription_repository import SubscriptionRepositoryImp
from app.adapters.repositories.usage_record_repository import UsageRecordRepositoryImp
from app.adapters.repositories.payment_repository import PaymentRepositoryImp
from app.adapters.repositories.invoice_repository import InvoiceRepositoryImp
from app.adapters.repositories.verification_token import VerificationTokenRepositoryImp

# ============ IMPORTS: SERVICES ============
from app.core.services.auth_service_impl import AuthServiceImp
from app.core.services.authorization_service_impl import AuthorizationServiceImp
from app.core.services.terminal_service import TerminalService
from app.core.services.courier_service import CourierService
from app.core.services.shift_service import ShiftService
from app.core.services.vehicle_service import VehicleService
from app.core.services.order_service import OrderService
from app.adapters.services.trend_route_solver_service import TrendRouteSolverService
from app.core.services.route_service import RouteService
from app.core.services.courier_state_service import CourierStateService
from app.core.services.avatar_service import AvatarService
from app.core.services.user_service import UserService
from app.core.services.role_service import RoleService
from app.core.services.mission_service import MissionService
from app.core.services.scan_service import ScanService
from app.adapters.clients.stripe.stripe_client import StripeAsyncClient
from app.core.services.billing_service import BillingService
from app.core.services.verification_token_service import VerificationTokenService


logger = logging.getLogger(__name__)

# ============ DATABASE SETUP ============

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.SQLALCHEMY_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session

    Yields:
        AsyncSession instance

    Raises:
        Exception: Re-raises any exception during request
    """
    async with async_session_maker() as session:
        try:
            logger.debug("📊 Database session created")
            yield session
        except Exception as e:
            logger.warning(f"⚠️  Exception during request: {type(e).__name__}: {str(e)}")
            await session.rollback()
            raise
        finally:
            logger.debug("🔚 Closing database session")
            await session.close()


# ============ REPOSITORY FACTORIES ============


def _create_repository(repo_class):
    """
    Factory for creating repository dependencies

    Args:
        repo_class: Repository class to instantiate

    Returns:
        Dependency function that creates repository instances
    """

    def get_repo(session: AsyncSession = Depends(get_db_session)):
        logger.debug(f"📦 Creating repository instance: {repo_class.__name__}")
        return repo_class(session)

    return get_repo


# Repository dependency getters
get_user_repository = _create_repository(UserRepositoryImp)
get_role_repository = _create_repository(RoleRepositoryImp)
get_permission_repository = _create_repository(PermissionRepositoryImp)
get_refresh_token_repository = _create_repository(RefreshTokenRepositoryImp)
get_password_reset_repository = _create_repository(PasswordResetRepositoryImp)
get_courier_repository = _create_repository(CourierRepositoryImp)
get_hub_repository = _create_repository(HubRepositoryImp)
get_hub_shift_repository = _create_repository(HubShiftRepositoryImp)
get_vehicle_repository = _create_repository(VehicleRepositoryImp)
get_order_repository = _create_repository(OrderRepositoryImp)
get_recipient_repository = _create_repository(RecipientRepositoryImp)
get_verification_token_repository = _create_repository(VerificationTokenRepositoryImp)
get_mission_repository = _create_repository(MissionRepositoryImp)
get_route_repository = _create_repository(RouteRepositoryImp)
get_courier_current_state_repository = _create_repository(
    CourierCurrentStateRepositoryImp
)
get_avatar_repository = _create_repository(AvatarRepositoryImp)
get_billing_customer_repository = _create_repository(BillingCustomerRepositoryImp)
get_plan_repository = _create_repository(PlanRepositoryImp)
get_plan_price_repository = _create_repository(PlanPriceRepositoryImp)
get_subscription_repository = _create_repository(SubscriptionRepositoryImp)
get_usage_record_repository = _create_repository(UsageRecordRepositoryImp)
get_payment_repository = _create_repository(PaymentRepositoryImp)
get_invoice_repository = _create_repository(InvoiceRepositoryImp)

# ============ SERVICE DEPENDENCIES ============

# Stripe client (singleton)
_stripe_client = StripeAsyncClient()


def get_stripe_client() -> StripeAsyncClient:
    return _stripe_client


def get_auth_service(
    user_repo: UserRepositoryImp = Depends(get_user_repository),
    refresh_token_repo: RefreshTokenRepositoryImp = Depends(
        get_refresh_token_repository
    ),
    password_reset_repo: PasswordResetRepositoryImp = Depends(
        get_password_reset_repository
    ),
) -> AuthServiceImp:
    """
    Get auth service instance

    Args:
        user_repo: User repository
        refresh_token_repo: Refresh token repository
        password_reset_repo: Password reset repository

    Returns:
        AuthServiceImp instance
    """
    logger.debug("📦 Creating AuthServiceImp instance")
    return AuthServiceImp(user_repo, refresh_token_repo, password_reset_repo)


def get_authorization_service(
    permission_repo: PermissionRepositoryImp = Depends(get_permission_repository),
    role_repo: RoleRepositoryImp = Depends(get_role_repository),
    user_repo: UserRepositoryImp = Depends(get_user_repository),
) -> AuthorizationServiceImp:
    """
    Get authorization service instance

    Args:
        permission_repo: Permission repository
        role_repo: Role repository
        user_repo: User repository

    Returns:
        AuthorizationServiceImp instance
    """
    logger.debug("📦 Creating AuthorizationServiceImp instance")
    return AuthorizationServiceImp(permission_repo, role_repo, user_repo)


def get_verification_token_service(
    verification_token_repo: VerificationTokenRepositoryImp = Depends(
        get_verification_token_repository
    ),
    user_repo: UserRepositoryImp = Depends(get_user_repository),
) -> VerificationTokenService:
    """
    Get verification token service instance

    Args:
        verification_token_repo: Verification token repository
        user_repo: User repository
    Returns:
        VerificationTokenService instance
    """
    logger.debug("📦 Creating VerificationTokenService instance")
    return VerificationTokenService(verification_token_repo, user_repo)


def get_terminal_service(
    hub_repo: HubRepositoryImp = Depends(get_hub_repository),
    user_repo: UserRepositoryImp = Depends(get_user_repository),
    courier_repo: CourierRepositoryImp = Depends(get_courier_repository),
) -> TerminalService:
    """
    Get terminal service instance

    Args:
        hub_repo: Hub repository
        user_repo: User repository
        courier_repo: Courier repository

    Returns:
        TerminalService instance
    """
    logger.debug("📦 Creating TerminalService instance")
    return TerminalService(hub_repo, user_repo, courier_repo)


def get_courier_service(
    courier_repo: CourierRepositoryImp = Depends(get_courier_repository),
    user_repo: UserRepositoryImp = Depends(get_user_repository),
    vehicle_repo: VehicleRepositoryImp = Depends(get_vehicle_repository),
) -> CourierService:
    """
    Get courier service instance

    Args:
        courier_repo: Courier repository
        user_repo: User repository
        vehicle_repo: Vehicle repository

    Returns:
        CourierService instance
    """
    logger.debug("📦 Creating CourierService instance")
    return CourierService(courier_repo, user_repo, vehicle_repo)


def get_shift_service(
    shift_repo: HubShiftRepositoryImp = Depends(get_hub_shift_repository),
    hub_repo: HubRepositoryImp = Depends(get_hub_repository),
    courier_repo: CourierRepositoryImp = Depends(get_courier_repository),
    user_repo: UserRepositoryImp = Depends(get_user_repository),
) -> ShiftService:
    """
    Get shift service instance

    Args:
        shift_repo: Shift repository
        hub_repo: Hub repository
        courier_repo: Courier repository
        user_repo: User repository

    Returns:
        ShiftService instance
    """
    logger.debug("📦 Creating ShiftService instance")
    return ShiftService(shift_repo, hub_repo, courier_repo, user_repo)


def get_vehicle_service(
    vehicle_repo: VehicleRepositoryImp = Depends(get_vehicle_repository),
    courier_repo: CourierRepositoryImp = Depends(get_courier_repository),
    user_repo: UserRepositoryImp = Depends(get_user_repository),
) -> VehicleService:
    """
    Get vehicle service instance

    Args:
        vehicle_repo: Vehicle repository
        courier_repo: Courier repository
        user_repo: User repository

    Returns:
        VehicleService instance
    """
    logger.debug("📦 Creating VehicleService instance")
    return VehicleService(vehicle_repo, courier_repo, user_repo)


def get_order_service(
    order_repo: OrderRepositoryImp = Depends(get_order_repository),
    recipient_repo: RecipientRepositoryImp = Depends(get_recipient_repository),
    courier_repo: CourierRepositoryImp = Depends(get_courier_repository),
    hub_repo: HubRepositoryImp = Depends(get_hub_repository),
    hub_shift_repo: HubShiftRepositoryImp = Depends(get_hub_shift_repository),
    user_repo: UserRepositoryImp = Depends(get_user_repository),
    role_repo: RoleRepositoryImp = Depends(get_role_repository),
    auth_service: AuthServiceImp = Depends(get_auth_service),
    session: AsyncSession = Depends(get_db_session),
) -> OrderService:
    """
    Get order service instance

    Args:
        order_repo: Order repository
        recipient_repo: Recipient repository
        courier_repo: Courier repository
        hub_repo: Hub repository
        hub_shift_repo: Hub shift repository
        user_repo: User repository
        role_repo: Role repository
        auth_service: Auth service
        session: Database session

    Returns:
        OrderService instance
    """
    logger.debug("📦 Creating OrderService instance")
    return OrderService(
        order_repo=order_repo,
        recipient_repo=recipient_repo,
        courier_repo=courier_repo,
        hub_repo=hub_repo,
        hub_shift_repo=hub_shift_repo,
        user_repo=user_repo,
        role_repo=role_repo,
        auth_service=auth_service,
        session=session,
    )


# Billing service
def get_billing_service(
    stripe_client: StripeAsyncClient = Depends(get_stripe_client),
    billing_customer_repo: BillingCustomerRepositoryImp = Depends(
        get_billing_customer_repository
    ),
    subscription_repo: SubscriptionRepositoryImp = Depends(get_subscription_repository),
    plan_repo: PlanRepositoryImp = Depends(get_plan_repository),
    plan_price_repo: PlanPriceRepositoryImp = Depends(get_plan_price_repository),
    usage_repo: UsageRecordRepositoryImp = Depends(get_usage_record_repository),
    payment_repo: PaymentRepositoryImp = Depends(get_payment_repository),
    invoice_repo: InvoiceRepositoryImp = Depends(get_invoice_repository),
    user_repo: UserRepositoryImp = Depends(get_user_repository),
    courier_repo: CourierRepositoryImp = Depends(get_courier_repository),
) -> BillingService:
    logger.debug("📦 Creating BillingService instance")
    return BillingService(
        stripe_client=stripe_client,
        billing_customer_repo=billing_customer_repo,
        subscription_repo=subscription_repo,
        plan_repo=plan_repo,
        plan_price_repo=plan_price_repo,
        usage_repo=usage_repo,
        payment_repo=payment_repo,
        invoice_repo=invoice_repo,
        user_repo=user_repo,
        courier_repo=courier_repo,
    )


def get_solver_service(
    order_repo: OrderRepositoryImp = Depends(get_order_repository),
    route_repo: RouteRepositoryImp = Depends(get_route_repository),
    hub_repo: HubRepositoryImp = Depends(get_hub_repository),
    vehicle_repo: VehicleRepositoryImp = Depends(get_vehicle_repository),
    shift_repo: HubShiftRepositoryImp = Depends(get_hub_shift_repository),
    user_repo: UserRepositoryImp = Depends(get_user_repository),
    courier_repo: CourierRepositoryImp = Depends(get_courier_repository),
    mission_repo: MissionRepositoryImp = Depends(get_mission_repository),
    recipient_repo: RecipientRepositoryImp = Depends(get_recipient_repository),
    hubshift_repo: HubShiftRepositoryImp = Depends(get_hub_shift_repository),
    billing_service: BillingService = Depends(get_billing_service),
    session: AsyncSession = Depends(get_db_session),
) -> RouteService:
    logger.debug("📦 Creating RouteService instance")
    return RouteService(
        solver_service=TrendRouteSolverService(),
        order_repo=order_repo,
        route_repo=route_repo,
        hub_repo=hub_repo,
        vehicle_repo=vehicle_repo,
        shift_repo=shift_repo,
        user_repo=user_repo,
        courier_repo=courier_repo,
        mission_repo=mission_repo,
        recipient_repo=recipient_repo,
        hubshift_repo=hubshift_repo,
        billing_service=billing_service,
        session=session,
    )


def get_avatar_service(
    avatar_repo: AvatarRepositoryImp = Depends(get_avatar_repository),
    user_repo: UserRepositoryImp = Depends(get_user_repository),
) -> AvatarService:
    """Get avatar service"""
    logger.debug("📦 Creating AvatarService instance")
    return AvatarService(avatar_repo, user_repo)


def get_user_service(
    user_repo: UserRepositoryImp = Depends(get_user_repository),
    role_repo: RoleRepositoryImp = Depends(get_role_repository),
    auth_service: AuthServiceImp = Depends(get_auth_service),
    billing_service: BillingService = Depends(get_billing_service),
    token_verification_service: VerificationTokenService = Depends(
        get_verification_token_service
    ),
) -> UserService:
    """
    Get user service instance

    Args:
        user_repo: User repository
        role_repo: Role repository
        auth_service: Auth service
        billing_service: Billing service
        token_verification_service: Token verification service

    Returns:
        UserService instance
    """
    logger.debug("📦 Creating UserService instance")
    return UserService(
        user_repo, role_repo, auth_service, billing_service, token_verification_service
    )


def get_role_service(
    role_repo: RoleRepositoryImp = Depends(get_role_repository),
    permission_repo: PermissionRepositoryImp = Depends(get_permission_repository),
) -> RoleService:
    """
    Get role service instance

    Args:
        role_repo: Role repository
        permission_repo: Permission repository

    Returns:
        RoleService instance
    """
    logger.debug("📦 Creating RoleService instance")
    return RoleService(role_repo, permission_repo)


def get_mission_service(
    mission_repo: MissionRepositoryImp = Depends(get_mission_repository),
    courier_repo: CourierRepositoryImp = Depends(get_courier_repository),
) -> MissionService:
    """
    Get mission service instance

    Args:
        mission_repo: Mission repository
        courier_repo: Courier repository

    Returns:
        MissionService instance
    """
    logger.debug("📦 Creating MissionService instance")
    return MissionService(mission_repo, courier_repo)


# OCR REPOSITORIES
def get_openai_repository() -> OpenAILLMRepository:
    """
    Get OpenAI LLM repository instance (synchronous)

    Returns:
        OpenAILLMRepository instance

    Raises:
        ValueError: If settings are not configured
    """
    logger.debug("📦 Creating OpenAILLMRepository instance")

    try:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")

        if not settings.SCHEMA_CONFIG_PATH:
            raise ValueError("SCHEMA_CONFIG_PATH is not configured")

        repo = OpenAILLMRepository(schema_config_path=settings.SCHEMA_CONFIG_PATH)
        logger.info("✅ OpenAILLMRepository created successfully")
        return repo

    except Exception as e:
        logger.error(f"❌ Error creating OpenAILLMRepository: {str(e)}", exc_info=True)
        raise


def get_ocr_repository():
    """
    Get OCR repository based on configured LLM provider (synchronous)

    Returns:
        LLM repository instance (OpenAI, Anthropic, etc.)

    Raises:
        ValueError: If LLM provider is not supported or not configured
    """
    logger.debug(f"📦 Creating OCR repository for provider: {settings.LLM_PROVIDER}")

    try:
        if settings.LLM_PROVIDER.lower() == "openai":
            logger.info("✅ Using OpenAI LLM provider")
            return get_openai_repository()

        elif settings.LLM_PROVIDER.lower() == "anthropic":
            logger.error("❌ Anthropic LLM provider not yet implemented")
            raise NotImplementedError("Anthropic LLM provider is not yet supported")

        else:
            logger.error(f"❌ Unsupported LLM provider: {settings.LLM_PROVIDER}")
            raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

    except (NotImplementedError, ValueError):
        raise
    except Exception as e:
        logger.error(f"❌ Error creating OCR repository: {str(e)}", exc_info=True)
        raise


# SCAN SERVICE
def get_scan_service(
    ocr_repo=Depends(get_ocr_repository),
) -> ScanService:
    """
    Get scan service instance

    Args:
        ocr_repo: OCR repository (injected via Depends)

    Returns:
        ScanService instance
    """
    logger.debug("📦 Creating ScanService instance")
    return ScanService(ocr_repo)


async def get_courier_state_service(
    current_state_repo: CourierCurrentStateRepositoryImp = Depends(
        get_courier_current_state_repository
    ),
    route_repo: RouteRepositoryImp = Depends(get_route_repository),
    mission_repo: MissionRepositoryImp = Depends(get_mission_repository),
    courier_repo: CourierRepositoryImp = Depends(get_courier_repository),
    order_repo: OrderRepositoryImp = Depends(get_order_repository),
    billing_service: BillingService = Depends(get_billing_service),
) -> CourierStateService:
    return CourierStateService(
        current_state_repo=current_state_repo,
        route_repo=route_repo,
        mission_repo=mission_repo,
        courier_repo=courier_repo,
        order_repo=order_repo,
        billing_service=billing_service,
    )
