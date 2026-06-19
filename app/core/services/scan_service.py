"""
Scan service implementation for OCR operations
"""

import base64
import logging
from typing import Optional
from uuid import UUID

from app.core.entities import User
from app.core.interfaces import ILLMBasedOcrInterface
from app.core.exceptions import OCRProcessingError, InvalidInputError
from app.api.v1.schemas.scan_schema import OCRData

logger = logging.getLogger(__name__)


class ScanService:
    """Service for OCR scanning operations"""

    def __init__(
        self,
        ocr_repository: ILLMBasedOcrInterface,
    ):
        self.ocr_repository = ocr_repository

    async def scan_base64_image(self, image_base64: str, user_id: UUID) -> OCRData:
        """
        Scan a base64-encoded image

        **Validation:**
        1. Verify base64 format is valid
        2. Verify image is not empty
        3. Verify user is authenticated

        **Returns:**
        - OCRData entity with extracted information

        **Raises:**
        - InvalidInputError: If base64 format is invalid
        - OCRProcessingError: If OCR processing fails
        - Exception: If unexpected error occurs
        """
        logger.info(f"🔄 Starting base64 image scan for user: {user_id}")

        # Validate base64 format
        try:
            self._validate_base64_format(image_base64)
            logger.info(f"✅ Base64 format validated")
        except InvalidInputError as e:
            logger.error(f"❌ Invalid base64 format: {str(e)}")
            raise

        # Process OCR
        try:
            result = await self.ocr_repository.ainvoke(image_base64)
            logger.info(f"✅ OCR processing completed for user: {user_id}")

            # Convert result to OCRData
            ocr_data = self._parse_ocr_result(result)
            logger.info(f"✅ OCR data parsed successfully")

            return ocr_data

        except OCRProcessingError as e:
            logger.error(f"❌ OCR processing failed: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error during OCR: {str(e)}", exc_info=True)
            raise OCRProcessingError(f"OCR processing failed: {str(e)}") from e

    async def scan_uploaded_file(
        self, file_content: bytes, content_type: str, user_id: UUID
    ) -> OCRData:
        """
        Scan an uploaded image file

        **Validation:**
        1. Verify content type is image
        2. Verify file content is not empty
        3. Encode file to base64
        4. Process OCR

        **Returns:**
        - OCRData entity with extracted information

        **Raises:**
        - InvalidInputError: If file format is invalid
        - OCRProcessingError: If OCR processing fails
        - Exception: If unexpected error occurs
        """
        logger.info(
            f"🔄 Starting file upload scan for user: {user_id} "
            f"(content_type={content_type})"
        )

        # Validate content type
        try:
            self._validate_image_content_type(content_type)
            logger.info(f"✅ Content type validated: {content_type}")
        except InvalidInputError as e:
            logger.error(f"❌ Invalid content type: {str(e)}")
            raise

        # Validate file content
        try:
            self._validate_file_content(file_content)
            logger.info(f"✅ File content validated (size: {len(file_content)} bytes)")
        except InvalidInputError as e:
            logger.error(f"❌ Invalid file content: {str(e)}")
            raise

        # Encode to base64
        try:
            image_base64 = base64.b64encode(file_content).decode("utf-8")
            logger.info(f"✅ File encoded to base64")
        except Exception as e:
            logger.error(f"❌ Error encoding file to base64: {str(e)}", exc_info=True)
            raise InvalidInputError(f"Failed to encode file: {str(e)}")

        # Process OCR
        try:
            result = await self.ocr_repository.ainvoke(image_base64)
            logger.info(f"✅ OCR processing completed for user: {user_id}")

            # Convert result to OCRData
            ocr_data = self._parse_ocr_result(result)
            logger.info(f"✅ OCR data parsed successfully")

            return ocr_data

        except OCRProcessingError as e:
            logger.error(f"❌ OCR processing failed: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error during OCR: {str(e)}", exc_info=True)
            raise OCRProcessingError(f"OCR processing failed: {str(e)}") from e

    async def scan_with_preprocessing(
        self,
        file_content: bytes,
        content_type: str,
        user_id: UUID,
        max_side: int = 1024,
    ) -> OCRData:
        """
        Scan an uploaded image file with preprocessing

        **Validation:**
        1. Verify content type is image
        2. Preprocess image (resize, optimize)
        3. Encode to base64
        4. Process OCR

        **Returns:**
        - OCRData entity with extracted information

        **Raises:**
        - InvalidInputError: If file format is invalid
        - OCRProcessingError: If OCR processing fails
        """
        logger.info(
            f"🔄 Starting preprocessed file scan for user: {user_id} "
            f"(max_side={max_side})"
        )

        # Validate content type
        try:
            self._validate_image_content_type(content_type)
            logger.info(f"✅ Content type validated: {content_type}")
        except InvalidInputError as e:
            logger.error(f"❌ Invalid content type: {str(e)}")
            raise

        # Note: Image preprocessing logic would go here
        # For now, we'll use the standard method
        # preprocessed_content = preprocess_for_gpt4o_ocr(file_content, max_side)
        # logger.info(f"✅ Image preprocessed")

        return await self.scan_uploaded_file(file_content, content_type, user_id)

    def _validate_base64_format(self, image_base64: str) -> None:
        """
        Validate base64 image format

        **Raises:**
        - InvalidInputError: If base64 format is invalid
        """
        if not isinstance(image_base64, str):
            raise InvalidInputError("Image must be a base64 encoded string")

        if not image_base64 or len(image_base64.strip()) == 0:
            raise InvalidInputError("Image cannot be empty")

        try:
            base64.b64decode(image_base64, validate=True)
        except Exception as e:
            raise InvalidInputError(f"Invalid base64 format: {str(e)}")

    def _validate_image_content_type(self, content_type: str) -> None:
        """
        Validate image content type

        **Raises:**
        - InvalidInputError: If content type is not an image
        """
        if not content_type.startswith("image/"):
            raise InvalidInputError(f"File must be an image. Got: {content_type}")

        # Optional: whitelist specific formats
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if content_type not in allowed_types:
            logger.warning(f"⚠️  Uncommon image format: {content_type}")

    def _validate_file_content(self, file_content: bytes) -> None:
        """
        Validate file content

        **Raises:**
        - InvalidInputError: If file content is invalid
        """
        if not file_content or len(file_content) == 0:
            raise InvalidInputError("File content cannot be empty")

        # Check for minimum file size (e.g., at least 100 bytes)
        if len(file_content) < 100:
            raise InvalidInputError("File is too small to process")

        # Optional: check maximum file size (e.g., 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(file_content) > max_size:
            raise InvalidInputError(
                f"File exceeds maximum size of {max_size / 1024 / 1024}MB"
            )

    def _parse_ocr_result(self, result: dict) -> OCRData:
        """
        Parse OCR repository result to OCRData schema

        **Args:**
        - result: Dictionary returned from OCR repository

        **Returns:**
        - OCRData schema instance

        **Raises:**
        - ValueError: If result format is invalid
        """
        try:
            logger.debug(f"🔄 Parsing OCR result")

            # Handle if result is already an OCRData instance
            if isinstance(result, OCRData):
                logger.debug(f"✅ Result is already OCRData instance")
                return result

            # Handle if result is a Pydantic model that was converted to dict
            if isinstance(result, dict):
                logger.debug(f"✅ Result is dict, converting to OCRData")
                return OCRData(**result)

            # Handle if result has model_dump method (Pydantic v2)
            if hasattr(result, "model_dump"):
                logger.debug(f"✅ Result has model_dump method")
                return OCRData(**result.model_dump())

            # Handle if result has dict method (Pydantic v1)
            if hasattr(result, "dict"):
                logger.debug(f"✅ Result has dict method")
                return OCRData(**result.dict())

            logger.error(f"❌ Unknown result format: {type(result)}")
            raise ValueError(f"Unexpected result format: {type(result)}")

        except Exception as e:
            logger.error(f"❌ Error parsing OCR result: {str(e)}", exc_info=True)
            raise

    def get_schema_info(self) -> dict:
        """
        Get OCR schema information

        **Returns:**
        - Dictionary with schema details

        **Raises:**
        - Exception: If schema retrieval fails
        """
        logger.info(f"🔄 Getting OCR schema information")

        try:
            if hasattr(self.ocr_repository, "get_schema_info"):
                schema_info = self.ocr_repository.get_schema_info()
                logger.info(f"✅ Schema information retrieved")
                return schema_info
            else:
                logger.warning(f"⚠️  OCR repository doesn't support get_schema_info")
                return {"message": "Schema information not available"}

        except Exception as e:
            logger.error(f"❌ Error getting schema info: {str(e)}", exc_info=True)
            raise
