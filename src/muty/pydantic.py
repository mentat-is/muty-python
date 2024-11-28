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
        if hasattr(field, "examples") and field.examples:
            example[field_name] = field.examples[0]
        # Fall back to json_schema_extra
        elif field.json_schema_extra and "examples" in field.json_schema_extra:
            example[field_name] = field.json_schema_extra["examples"][0]
    return example


def autogenerate_model_example(cls, *args, **kwargs):
    """
    helper method to generate an example for a pydantic model, using the examples from the fields.

    NOTE: this is solely to use as a class method override for `model_json_schema` in a BaseModel class.

    Args:
        cls (BaseModel): the model to generate the example for.
        *args: arbitrary positional arguments.
        **kwargs: arbitrary keyword arguments.

    Returns:
        dict: the generated example
    """
    schema = super().model_json_schema(*args, **kwargs)

    # build example from field examples
    example = autogenerate_model_example_by_class(cls)
    schema["examples"] = [example]
    return schema
