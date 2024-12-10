"""
pydantic models related utilities
"""

from pydantic import BaseModel


def autogenerate_model_example_by_class(model_class: BaseModel):
    """
    helper method to generate an example for a pydantic model, using the examples from the fields.

    Args:
        model_class (BaseModel): the model to generate the example for.
    """
    example = {}
    for field_name, field in model_class.model_fields.items():
        if field.json_schema_extra and "examples" in field.json_schema_extra:
            # take first example if multiple exist
            example[field_name] = field.json_schema_extra["examples"][0]
        # fallback for legacy
        elif hasattr(field, "example") and field.example:
            example[field_name] = field.example[0]
    return example
