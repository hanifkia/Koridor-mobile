class OCRBaseException(Exception):
    """Base exception for OCR service"""

    pass


class InvalidInputError(OCRBaseException):
    """Raised when input validation fails"""

    pass


class OCRProcessingError(OCRBaseException):
    """Raised when OCR processing fails"""

    pass
