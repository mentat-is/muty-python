"""
pydantic models related utilities
"""


def autogenerate_model_example(cls, *args, **kwargs):
    """
    helper method to generate an example for a pydantic model, using the examples from the fields.

    Args:
        cls (BaseModel): the model to generate the example for.
        *args: arbitrary positional arguments.
        **kwargs: arbitrary keyword arguments.

    Returns:
        dict: the generated example
    """
    schema = super().model_json_schema(*args, **kwargs)
    # Build example from field examples
    example = {}
    for field_name, field in cls.model_fields.items():
        if field.json_schema_extra and "examples" in field.json_schema_extra:
            example[field_name] = field.json_schema_extra["examples"][0]
    schema["examples"] = [example]
    return schema
