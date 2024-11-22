from sqlalchemy.types import TypeDecorator, JSON
from backend.models import ArgumentResult
import json

class ArgumentResultType(TypeDecorator):
    impl = JSON
    
    def process_bind_param(self, value, dialect):
        print(f"DEBUG: Processing value of type: {type(value)}")
        print(f"DEBUG: Value: {value}")
        if value is None:
            return None
        if isinstance(value, dict):
            return value
        if isinstance(value, ArgumentResult):
            return value.model_dump()
        if isinstance(value, str):
            return json.loads(value)
        if hasattr(value, 'model_dump'):
            return value.model_dump()
        raise TypeError(f"Cannot process type {type(value)}")
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return ArgumentResult(**value)