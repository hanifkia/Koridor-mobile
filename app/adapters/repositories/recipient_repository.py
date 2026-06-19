# app/adapters/repositories/recipient_repository.py
"""
Recipient repository implementation
"""
from typing import List, Optional
import logging
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload, selectinload

from app.core.entities import Recipient, Coordinates, Address
from app.core.interfaces import IRecipientRepository
from app.adapters.database.models import RecipientORM

logger = logging.getLogger(__name__)


class RecipientRepositoryImp(IRecipientRepository):
    """Recipient repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: Recipient) -> Recipient:
        """Create a new recipient"""
        try:
            recipient_orm = RecipientORM(
                id=entity.id,
                user_id=entity.user_id,
                latitude=entity.location.lat if entity.location else None,
                longitude=entity.location.lon if entity.location else None,
                street=entity.address.street if entity.address else None,
                city=entity.address.city if entity.address else None,
                state=entity.address.state if entity.address else None,
                country=entity.address.country if entity.address else None,
                postal_code=entity.address.postal_code if entity.address else None,
            )
            self.session.add(recipient_orm)
            await self.session.flush()
            await self.session.commit()

            # ✅ Re-fetch with eager loading
            query = (
                select(RecipientORM)
                .where(RecipientORM.id == recipient_orm.id)
                .options(selectinload(RecipientORM.orders))  # ← ADD THIS
            )
            result = await self.session.execute(query)
            recipient_orm = result.unique().scalar_one_or_none()

            return await self._orm_to_entity(
                recipient_orm
            )  # Remove await if _orm_to_entity is sync
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating recipient: {str(e)}", exc_info=True)
            raise

    async def get_by_user_id(self, user_id: UUID):
        """Get Recipient by User ID"""
        try:
            logger.info(f"🔄 Getting recipient by user ID: {user_id}")

            query = (
                select(RecipientORM)
                .where(RecipientORM.user_id == user_id)
                .options(joinedload(RecipientORM.orders))
            )
            result = await self.session.execute(query)
            recipient_orm = result.unique().scalar_one_or_none()

            if not recipient_orm:
                logger.debug(f"Recipient not found: {user_id}")
                return None

            logger.info(f"✅ Recipient retrieved: {user_id}")
            return await self._orm_to_entity(recipient_orm)

        except Exception as e:
            logger.error(
                f"❌ Error getting recipient by user id: {str(e)}", exc_info=True
            )
            return None

    async def get_by_ids(self, recipient_ids: List[UUID]) -> List[Recipient]:
        """Get recipients by list of IDs"""
        try:
            logger.info(f"🔄 Getting recipients by IDs: {recipient_ids}")

            query = (
                select(RecipientORM)
                .where(RecipientORM.id.in_(recipient_ids))
                .options(joinedload(RecipientORM.orders))
            )
            result = await self.session.execute(query)
            recipients_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(recipients_orm)} recipients")
            return [await self._orm_to_entity(r) for r in recipients_orm]

        except Exception as e:
            logger.error(f"❌ Error getting recipients by ids: {str(e)}", exc_info=True)
            return []

    async def get_by_list_of_user_ids(self, user_ids: List[UUID]) -> List[Recipient]:
        """Get recipients by list of user IDs"""
        try:
            logger.info(f"🔄 Getting recipients by user IDs: {user_ids}")

            query = (
                select(RecipientORM)
                .where(RecipientORM.user_id.in_(user_ids))
                .options(joinedload(RecipientORM.orders))
            )
            result = await self.session.execute(query)
            recipients_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(recipients_orm)} recipients")
            return [await self._orm_to_entity(r) for r in recipients_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting recipients by user ids: {str(e)}", exc_info=True
            )
            return []

    async def get_by_id(self, entity_id: UUID) -> Optional[Recipient]:
        """Get recipient by ID"""
        try:
            logger.info(f"🔄 Getting recipient by ID: {entity_id}")

            query = (
                select(RecipientORM)
                .where(RecipientORM.id == entity_id)
                .options(joinedload(RecipientORM.orders))
            )
            result = await self.session.execute(query)
            recipient_orm = result.unique().scalar_one_or_none()

            if not recipient_orm:
                logger.debug(f"Recipient not found: {entity_id}")
                return None

            logger.info(f"✅ Recipient retrieved: {entity_id}")
            return await self._orm_to_entity(recipient_orm)

        except Exception as e:
            logger.error(f"❌ Error getting recipient by id: {str(e)}", exc_info=True)
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Recipient]:
        """Get all recipients with pagination"""
        try:
            logger.info(f"🔄 Getting all recipients (skip={skip}, limit={limit})")

            query = (
                select(RecipientORM)
                .offset(skip)
                .limit(limit)
                .order_by(RecipientORM.created_at.desc())
                .options(joinedload(RecipientORM.orders))
            )
            result = await self.session.execute(query)
            recipients_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(recipients_orm)} recipients")
            return [await self._orm_to_entity(r) for r in recipients_orm]

        except Exception as e:
            logger.error(f"❌ Error getting all recipients: {str(e)}", exc_info=True)
            return []

    async def get_by_email(self, email: str) -> Optional[Recipient]:
        """Get recipient by email"""
        try:
            logger.info(f"🔄 Getting recipient by email: {email}")

            query = (
                select(RecipientORM)
                .where(RecipientORM.email == email)
                .options(joinedload(RecipientORM.orders))
            )
            result = await self.session.execute(query)
            recipient_orm = result.unique().scalar_one_or_none()

            if not recipient_orm:
                logger.debug(f"Recipient not found by email: {email}")
                return None

            logger.info(f"✅ Recipient found by email: {email}")
            return await self._orm_to_entity(recipient_orm)

        except Exception as e:
            logger.error(
                f"❌ Error getting recipient by email: {str(e)}", exc_info=True
            )
            return None

    async def get_by_phone(self, phone_number: str) -> Optional[Recipient]:
        """Get recipient by phone number"""
        try:
            logger.info(f"🔄 Getting recipient by phone: {phone_number}")

            query = (
                select(RecipientORM)
                .where(RecipientORM.phone_number == phone_number)
                .options(joinedload(RecipientORM.orders))
            )
            result = await self.session.execute(query)
            recipient_orm = result.unique().scalar_one_or_none()

            if not recipient_orm:
                logger.debug(f"Recipient not found by phone: {phone_number}")
                return None

            logger.info(f"✅ Recipient found by phone: {phone_number}")
            return await self._orm_to_entity(recipient_orm)

        except Exception as e:
            logger.error(
                f"❌ Error getting recipient by phone: {str(e)}", exc_info=True
            )
            return None

    async def get_by_name(
        self, name: str, skip: int = 0, limit: int = 100
    ) -> List[Recipient]:
        """Get recipients by name"""
        try:
            logger.info(f"🔄 Getting recipients with name: {name}")

            query = (
                select(RecipientORM)
                .where(RecipientORM.name.ilike(f"%{name}%"))
                .offset(skip)
                .limit(limit)
                .order_by(RecipientORM.created_at.desc())
                .options(joinedload(RecipientORM.orders))
            )
            result = await self.session.execute(query)
            recipients_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(recipients_orm)} recipients")
            return [await self._orm_to_entity(r) for r in recipients_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting recipients by name: {str(e)}", exc_info=True
            )
            return []

    async def email_exists(self, email: str) -> bool:
        """Check if email exists"""
        try:
            query = (
                select(func.count())
                .select_from(RecipientORM)
                .where(RecipientORM.email == email)
            )
            result = await self.session.execute(query)
            count = result.scalar()
            return count > 0

        except Exception as e:
            logger.error(f"❌ Error checking email existence: {str(e)}", exc_info=True)
            return False

    async def phone_exists(self, phone_number: str) -> bool:
        """Check if phone number exists"""
        try:
            query = (
                select(func.count())
                .select_from(RecipientORM)
                .where(RecipientORM.phone_number == phone_number)
            )
            result = await self.session.execute(query)
            count = result.scalar()
            return count > 0

        except Exception as e:
            logger.error(f"❌ Error checking phone existence: {str(e)}", exc_info=True)
            return False

    async def get_all_recipients(
        self, skip: int = 0, limit: int = 100
    ) -> List[Recipient]:
        """Get all recipients with pagination"""
        return await self.get_all(skip, limit)

    async def search_recipients(
        self, query: str, skip: int = 0, limit: int = 100
    ) -> List[Recipient]:
        """Search recipients by name or email"""
        try:
            logger.info(f"🔄 Searching recipients with query: {query}")

            db_query = (
                select(RecipientORM)
                .where(
                    or_(
                        RecipientORM.name.ilike(f"%{query}%"),
                        RecipientORM.email.ilike(f"%{query}%"),
                        RecipientORM.phone_number.ilike(f"%{query}%"),
                    )
                )
                .offset(skip)
                .limit(limit)
                .order_by(RecipientORM.created_at.desc())
                .options(joinedload(RecipientORM.orders))
            )
            result = await self.session.execute(db_query)
            recipients_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(recipients_orm)} recipients")
            return [await self._orm_to_entity(r) for r in recipients_orm]

        except Exception as e:
            logger.error(f"❌ Error searching recipients: {str(e)}", exc_info=True)
            return []

    async def update(
        self, entity_id: UUID, entity: Recipient, commit: bool = True
    ) -> Optional[Recipient]:
        """Update an existing recipient"""
        try:
            logger.info(f"🔄 Updating recipient: {entity_id}")

            recipient_orm = await self.session.get(RecipientORM, entity_id)
            if not recipient_orm:
                logger.warning(f"❌ Recipient not found: {entity_id}")
                return None

            # Update fields
            recipient_orm.latitude = entity.location.lat if entity.location else None
            recipient_orm.longitude = entity.location.lon if entity.location else None
            recipient_orm.street = entity.address.street if entity.address else None
            recipient_orm.city = entity.address.city if entity.address else None
            recipient_orm.state = entity.address.state if entity.address else None
            recipient_orm.country = entity.address.country if entity.address else None
            recipient_orm.postal_code = (
                entity.address.postal_code if entity.address else None
            )
            recipient_orm.updated_at = datetime.utcnow()

            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Recipient updated and committed: {entity_id}")
            else:
                logger.info(f"✅ Recipient updated (pending commit): {entity_id}")

            return await self._orm_to_entity(recipient_orm)

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error updating recipient: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id: UUID, commit: bool = True) -> bool:
        """
        Delete a recipient

        Args:
            entity_id: Recipient UUID
            commit: Whether to commit immediately

        Returns:
            True if deleted, False if not found

        Raises:
            Exception: If deletion fails
        """
        try:
            logger.info(f"🔄 Deleting recipient: {entity_id}")

            recipient_orm = await self.session.get(RecipientORM, entity_id)
            if not recipient_orm:
                logger.warning(f"❌ Recipient not found: {entity_id}")
                return False

            await self.session.delete(recipient_orm)
            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Recipient deleted and committed: {entity_id}")
            else:
                logger.info(f"✅ Recipient deleted (pending commit): {entity_id}")

            return True

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error deleting recipient: {str(e)}", exc_info=True)
            raise

    async def _orm_to_entity(self, recipient_orm: RecipientORM) -> Recipient:
        return Recipient(
            id=recipient_orm.id,
            user_id=recipient_orm.user_id,
            location=Coordinates(
                lat=recipient_orm.latitude, lon=recipient_orm.longitude
            ),
            address=Address(
                street=recipient_orm.street,
                city=recipient_orm.city,
                state=recipient_orm.state,
                country=recipient_orm.country,
                postal_code=recipient_orm.postal_code,
            ),
        )
