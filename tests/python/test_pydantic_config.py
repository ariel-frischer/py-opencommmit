"""Tests for the Pydantic configuration."""

import pytest
from pydantic import BaseModel, ValidationError

from py_opencommit.utils.pydantic_config import model_config


class TestPydanticConfig:
    """Tests for the Pydantic configuration."""
    
    def test_model_config_extra_fields(self):
        """Test that the model config ignores extra fields."""
        # Define a test model using our model_config
        class TestModel(BaseModel):
            model_config = model_config
            name: str
            age: int
        
        # Create an instance with extra fields
        model = TestModel(name="Test", age=30, extra_field="This should be ignored")
        
        # Verify the model was created successfully
        assert model.name == "Test"
        assert model.age == 30
        
        # Verify the extra field was ignored (not accessible as an attribute)
        with pytest.raises(AttributeError):
            assert model.extra_field
    
    def test_model_config_validate_assignment(self):
        """Test that the model config validates assignments."""
        # Define a test model using our model_config
        class TestModel(BaseModel):
            model_config = model_config
            name: str
            age: int
        
        # Create a valid instance
        model = TestModel(name="Test", age=30)
        
        # Test valid assignment
        model.age = 31
        assert model.age == 31
        
        # Test invalid assignment
        with pytest.raises(ValidationError):
            model.age = "not an integer"
    
    def test_model_config_arbitrary_types(self):
        """Test that the model config allows arbitrary types."""
        # Define a custom class
        class CustomClass:
            def __init__(self, value):
                self.value = value
        
        # Define a test model using our model_config
        class TestModel(BaseModel):
            model_config = model_config
            name: str
            custom: CustomClass
        
        # Create a custom object
        custom_obj = CustomClass("test value")
        
        # Create a model with the custom object
        model = TestModel(name="Test", custom=custom_obj)
        
        # Verify the model was created successfully
        assert model.name == "Test"
        assert model.custom is custom_obj
        assert model.custom.value == "test value"
    
    def test_model_config_populate_by_name(self):
        """Test that the model config allows population by field name."""
        # Define a test model using our model_config with field aliases
        class TestModel(BaseModel):
            model_config = model_config
            user_name: str
            user_age: int
        
        # Create an instance using field names
        model = TestModel(user_name="Test", user_age=30)
        
        # Verify the model was created successfully
        assert model.user_name == "Test"
        assert model.user_age == 30