from pydantic import BaseModel, Field, create_model
from typing import Optional
import json
from pathlib import Path

import yaml


def load_config(config_path: str) -> dict:
    """
    Load configuration from YAML or JSON file.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary containing configuration

    Raises:
        ValueError: If file format is not supported
        FileNotFoundError: If file doesn't exist
    """
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        if config_path.endswith((".yaml", ".yml")):
            return yaml.safe_load(f)
        elif config_path.endswith(".json"):
            return json.load(f)

    raise ValueError("Config file must be .yaml, .yml, or .json")


def get_type(type_str: str, required: bool = True):
    """
    Get Python type from string, handling optional types.

    Args:
        type_str: String representation of the type
        required: Whether the field is required

    Returns:
        Python type annotation
    """
    TYPE_MAPPING = {
        "str": str,
        "string": str,
        "int": int,
        "integer": int,
        "float": float,
        "number": float,
        "bool": bool,
        "boolean": bool,
        "list": list,
        "array": list,
        "dict": dict,
        "object": dict,
    }

    base_type = TYPE_MAPPING.get(type_str.lower(), str)

    if not required:
        return Optional[base_type]
    return base_type


class SchemaBuilder:
    """Builder class to create Pydantic models from configuration files."""

    @classmethod
    def build_field(cls, field_config: dict) -> tuple:
        """Build a single field definition."""
        field_type = get_type(field_config["type"], field_config.get("required", True))

        default = field_config.get("default", ...)
        if not field_config.get("required", True) and default == ...:
            default = None

        description = field_config.get("description", "")

        field_kwargs = {"description": description}

        # Add validation rules if specified
        if "min_length" in field_config:
            field_kwargs["min_length"] = field_config["min_length"]
        if "max_length" in field_config:
            field_kwargs["max_length"] = field_config["max_length"]
        if "gt" in field_config:
            field_kwargs["gt"] = field_config["gt"]
        if "ge" in field_config:
            field_kwargs["ge"] = field_config["ge"]
        if "lt" in field_config:
            field_kwargs["lt"] = field_config["lt"]
        if "le" in field_config:
            field_kwargs["le"] = field_config["le"]
        if "pattern" in field_config:
            field_kwargs["pattern"] = field_config["pattern"]

        return (field_type, Field(default=default, **field_kwargs))

    @classmethod
    def create_model_from_config(cls, config: dict) -> type[BaseModel]:
        """Create Pydantic model from configuration."""
        model_name = config.get("model_name", "DynamicModel")
        fields_config = config.get("fields", {})

        # Handle both dict and list formats
        if isinstance(fields_config, list):
            fields_config = {f["name"]: f for f in fields_config}

        fields = {}
        for field_name, field_config in fields_config.items():
            fields[field_name] = cls.build_field(field_config)

        return create_model(model_name, **fields)

    @classmethod
    def from_file(cls, config_path: str) -> type[BaseModel]:
        """Create model directly from config file."""
        config = load_config(config_path)
        return cls.create_model_from_config(config)
