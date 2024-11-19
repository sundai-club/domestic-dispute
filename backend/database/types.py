from sqlalchemy.types import TypeDecorator, JSON
from models import ArgumentResult
import json

class ArgumentResultType(TypeDecorator):
    impl = JSON
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, ArgumentResult):
            return json.loads(value.model_dump_json())
        if isinstance(value, str):
            return json.loads(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return ArgumentResult(**value) 