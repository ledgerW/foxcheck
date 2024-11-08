from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticToolsParser
from pydantic import BaseModel, validator, Field
from typing import Optional
from dateutil.parser import parse as parse_date
from dateutil.parser._parser import ParserError


llm = ChatOpenAI(model='gpt-4o', temperature=0.1)


class Metadata(BaseModel):
    """Use to extract metadata information from content."""

    authors: str = Field(description="the author or authors of the content.")
    publication_date: Optional[str] = Field(description="the date this content was published.")

    @validator("publication_date", pre=True)
    def validate_date_string(cls, value):
        if isinstance(value, str):
            try:
                # Attempt to parse the date with dateutil
                parse_date(value)
                return value  # Return the valid date string if parsing is successful
            except ParserError:
                return None  # If parsing fails, return None
        return None  # If the value isn't a string, return None


prompt = ChatPromptTemplate.from_template(
    """
    Content:
    {content}

    You are a research assistant at a prestigious fact-checking organization. Please thoroughly
    review the content above and use the Metadata tool to extract the metadata items requested.
    """
)

tools = [Metadata]

chain = (
    prompt
    | llm.bind_tools(tools)
    | PydanticToolsParser(tools=tools, first_tool_only=True)
)