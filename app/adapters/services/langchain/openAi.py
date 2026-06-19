from typing import Any, Optional

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from app.adapters.services.langchain.schema_builder import SchemaBuilder
from app.config.settings import settings as ocr_settings
from app.core.interfaces import ILLMBasedOcrInterface


class OpenAILLMRepository(ILLMBasedOcrInterface):
    """OpenAI-based LLM OCR Repository Implementation using LangChain"""

    def __init__(self, schema_config_path: Optional[str] = None):
        """
        Initialize OpenAI LLM Repository

        Args:
            schema_config_path: Path to the schema configuration file (YAML/JSON)
                               If None, uses default path from settings
        """
        self.model_name = ocr_settings.MODEL_NAME
        self.temperature = ocr_settings.TEMPERATURE
        self.system_prompt = ocr_settings.SYSTEM_PROMPT

        # Load schema configuration
        config_path = schema_config_path or ocr_settings.SCHEMA_CONFIG_PATH
        self.schema_model = SchemaBuilder.from_file(config_path)

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            api_key=ocr_settings.OPENAI_API_KEY,
        )

        # Bind structured output
        self.structured_llm = self.llm.with_structured_output(self.schema_model)

    def invoke(self, image: str) -> dict[str, Any]:
        """
        Synchronous OCR using OpenAI Vision API with LangChain

        Args:
            image: Base64 encoded image string

        Returns:
            Dictionary containing extracted structured data
        """
        try:
            # Create message with image
            message = self._create_message(image)

            # Invoke and get structured response
            response = self.structured_llm.invoke([message])

            # Convert Pydantic model to dict
            return response.model_dump()

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}") from e

    async def ainvoke(self, image: str) -> dict[str, Any]:
        """
        Asynchronous OCR using OpenAI Vision API with LangChain

        Args:
            image: Base64 encoded image string

        Returns:
            Dictionary containing extracted structured data
        """
        try:
            # Create message with image
            message = self._create_message(image)

            # Invoke asynchronously and get structured response
            response = await self.structured_llm.ainvoke([message])

            # Convert Pydantic model to dict
            return response.model_dump()

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}") from e

    def _create_message(self, image_b64: str) -> HumanMessage:
        """
        Create a HumanMessage with image and instructions

        Args:
            image_b64: Base64 encoded image string

        Returns:
            HumanMessage object
        """
        return HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": self.system_prompt
                    or """Extract all text from this image. 
                    Structure the output according to the schema:
                    - Identify recipient and sender information
                    - Extract parcel details (weight, contents, reference numbers)
                    - Identify barcodes and tracking numbers
                    - Convert weights to grams if necessary
                    - Be precise and extract all available information
                    """,
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                },
            ]
        )

    def reload_schema(self, schema_config_path: str) -> None:
        """
        Reload schema configuration from a new file

        Args:
            schema_config_path: Path to the new schema configuration file
        """
        self.schema_model = SchemaBuilder.from_file(schema_config_path)
        self.structured_llm = self.llm.with_structured_output(self.schema_model)

    def get_schema_info(self) -> dict[str, Any]:
        """
        Get information about the current schema

        Returns:
            Dictionary containing schema information
        """
        return {
            "model_name": self.schema_model.__name__,
            "fields": list(self.schema_model.model_fields.keys()),
            "schema": self.schema_model.model_json_schema(),
        }
