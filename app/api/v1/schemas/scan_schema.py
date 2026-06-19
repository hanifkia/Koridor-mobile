from pydantic import BaseModel, Field


class OCRRequest(BaseModel):
    """OCR Request Schema"""

    image: str = Field(..., description="Base64 encoded image string", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            }
        }


class ErrorResponse(BaseModel):
    """Error Response Schema"""

    success: bool = Field(default=False)
    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Detailed error information")


class OCRData(BaseModel):
    """Extracted OCR Data - All possible fields"""

    # recipient_full_name: str = Field(..., description="Recipient full name")
    recipient_first_name: str | None = Field(
        ..., description="Recipient First name or organization name"
    )
    recipient_last_name: str | None = Field(
        None, description="Recipient last name if available"
    )
    street: str | None = Field(
        ..., description="street name and number of the recipient"
    )
    postal_code: str | None = Field(..., description="The postal code of the recipient")
    city: str | None = Field(..., description="The city which recipient live")
    country: str | None = Field(..., description="The country which recipient live")
    recipient_phone: str | None = Field(None, description="Recipient phone number")
    recipient_email: str | None = Field(None, description="Recipient email")
    sender_full_name: str | None = Field(None, description="Full name of the sender")
    sender_address: str | None = Field(None, description="Full address of the sender")
    weight_occupation: float | None = Field(..., description="Parcel weight in grams")
    parcel_piece: str | None = Field(
        ..., description="Parcel piece (e.g., 1/1, 1/2, 3/3)"
    )
    parcel_contents: str | None = Field(..., description="Parcel contents type")
    barcode: str | None = Field(..., description="Barcode starting with WAYBILL")
    extracted_lat: float | None = None
    extracted_lon: float | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "recipient_first_name": "John",
                "recipient_last_name": "Doe",
                "street": "123 Main St, Building A, Unit 5",
                "postal_code": "12345",
                "city": "New York",
                "country": "USA",
                "recipient_phone": "+1234567890",
                "recipient_email": "john@example.com",
                "sender_full_name": "Jane Smith",
                "sender_address": "456 Oak Ave, City XYZ",
                "weight_occupation": 1500.0,
                "parcel_piece": "1/1",
                "parcel_contents": "Electronics",
                "barcode": "WAYBILL123456789",
            }
        }


class OCRResponse(BaseModel):
    """OCR Response Schema"""

    success: bool = Field(..., description="Whether the OCR was successful")
    data: OCRData | None = Field(None, description="Extracted data")
    message: str | None = Field(None, description="Status message")
    error_msg: str | None = ""
