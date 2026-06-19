"""
Scan router with service layer for OCR operations
"""

import logging
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.v1.schemas.scan_schema import (
    OCRRequest,
    OCRResponse,
    ErrorResponse,
    OCRData,
)
from app.core.services.scan_service import ScanService
from app.core.exceptions import OCRProcessingError, InvalidInputError
from app.config.dependencies import get_scan_service
from app.config.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scan", tags=["Scanner"])


@router.post(
    "/base64",
    response_model=OCRResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    status_code=status.HTTP_200_OK,
    summary="Scan base64-encoded image",
    description="Process a base64-encoded image and extract text using LLM-based OCR",
)
async def scan_base64(
    request: OCRRequest,
    scan_service: ScanService = Depends(get_scan_service),
    current_user: dict = Depends(get_current_user),
) -> OCRResponse:
    """
    Scan a base64-encoded image

    **Request Body:**
    - **image**: Base64-encoded image string (already preprocessed)

    **Returns:**
    - OCRResponse with extracted data

    **Raises:**
    - HTTPException: 400 if base64 format is invalid
    - HTTPException: 500 if OCR processing fails
    """

    try:
        user_id = current_user["user_id"]

        logger.info(f"🔄 Processing base64 scan request for user: {user_id}")

        # Scan image
        ocr_data = await scan_service.scan_base64_image(
            image_base64=request.image,
            user_id=user_id,
        )
        logger.info(f"✅ Base64 scan completed successfully for user: {user_id}")

        return OCRResponse(
            success=True,
            data=ocr_data,
            message="OCR completed successfully",
            error_msg="",
        )

    except InvalidInputError as e:
        logger.error(f"❌ Invalid input: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except OCRProcessingError as e:
        logger.error(f"❌ OCR processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during OCR processing: {str(e)}",
        )


@router.post(
    "/file",
    response_model=OCRResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    status_code=status.HTTP_200_OK,
    summary="Scan uploaded image file",
    description="Upload an image file and extract text using LLM-based OCR",
)
async def scan_file(
    file: UploadFile = File(..., description="Image file to process"),
    scan_service: ScanService = Depends(get_scan_service),
    current_user: dict = Depends(get_current_user),
) -> OCRResponse:
    """
    Upload and scan an image file

    **Request Body:**
    - **file**: Image file (JPEG, PNG, GIF, WebP, etc.)

    **Returns:**
    - OCRResponse with extracted data

    **Raises:**
    - HTTPException: 400 if file format is invalid
    - HTTPException: 500 if OCR processing fails
    """

    try:
        user_id = current_user["user_id"]

        logger.info(
            f"🔄 Processing file scan request for user: {user_id} "
            f"(filename={file.filename}, content_type={file.content_type})"
        )

        # Read file content
        try:
            file_content = await file.read()
            logger.info(f"✅ File read successfully (size: {len(file_content)} bytes)")
        except Exception as e:
            logger.error(f"❌ Error reading file: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to read file",
            )

        # Scan file
        try:
            ocr_data = await scan_service.scan_uploaded_file(
                file_content=file_content,
                content_type=file.content_type,
                user_id=user_id,
            )
            logger.info(f"✅ File scan completed successfully for user: {user_id}")

            return OCRResponse(
                success=True,
                data=ocr_data,
                message="OCR completed successfully",
                error_msg="",
            )

        except InvalidInputError as e:
            logger.error(f"❌ Invalid input: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        except OCRProcessingError as e:
            logger.error(f"❌ OCR processing error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during OCR processing: {str(e)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Unexpected error in file scan endpoint: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@router.get(
    "/schema",
    status_code=status.HTTP_200_OK,
    summary="Get OCR schema information",
    description="Retrieve information about the OCR data schema",
)
async def get_ocr_schema(
    scan_service: ScanService = Depends(get_scan_service),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get OCR schema information

    **Returns:**
    - Dictionary with OCR schema details including fields and structure

    **Raises:**
    - HTTPException: 500 if schema retrieval fails
    """

    try:
        logger.info(
            f"🔄 Retrieving OCR schema information for user: {current_user['user_id']}"
        )

        schema_info = scan_service.get_schema_info()
        logger.info(f"✅ Schema information retrieved successfully")

        return schema_info

    except Exception as e:
        logger.error(f"❌ Error retrieving schema: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve schema information",
        )
