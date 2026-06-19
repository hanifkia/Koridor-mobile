from abc import ABC, abstractmethod
from typing import Any


class ILLMBasedOcrInterface(ABC):
    """LLM-Based OCR Repository Interface"""

    @abstractmethod
    def invoke(self, image: str) -> dict[str, Any]:
        """Synchronous OCR invocation"""
        pass

    @abstractmethod
    async def ainvoke(self, image: str) -> dict[str, Any]:
        """Asynchronous OCR invocation"""
        pass
