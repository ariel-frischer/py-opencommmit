"""Pydantic configuration for OpenCommit."""

from pydantic import ConfigDict

# Define a model config that can be used by all Pydantic models
model_config = ConfigDict(
    extra='ignore',  # Ignore extra fields instead of raising an error
    validate_assignment=True,
    arbitrary_types_allowed=True,
    populate_by_name=True
)
