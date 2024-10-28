from pydantic import BaseModel, RootModel, field_validator
from langchain_core.documents.base import Document
from typing import List, Dict
from uuid import UUID


class DocList(RootModel[List[Document]]):
    model_config = {'validate_assignment': True}


class QuestionObject(RootModel[Dict[str, str]]):
    model_config = {'validate_assignment': True}

    @field_validator('root')
    def validate_key_is_uuid(cls, value):
        for key in value.keys():
            try:
                u = UUID(key)
                if u.version != 4:
                    raise ValueError(f"{key} is not UUID v4")
            except ValueError as e:
                raise ValueError(f"{key} is not UUID v4")
        return value


class ContextObject(RootModel[Dict[str, List[str]]]):
    model_config = {'validate_assignment': True}

    @field_validator('root')
    def validate_key_is_uuid(cls, value):
        for key in value.keys():
            try:
                u = UUID(key)
                if u.version != 4:
                    raise ValueError(f"{key} is not UUID v4")
            except ValueError as e:
                raise ValueError(f"{key} is not UUID v4")
        return value

    @field_validator('root')
    def validate_values_are_uuid(cls, value):
        for key, val in value.items():
            for v in val:
                try:
                    u = UUID(v)
                    if u.version != 4:
                        raise ValueError(f"{key} is not UUID v4")
                except:
                    raise ValueError(f"{key} is not UUID v4")
        return value