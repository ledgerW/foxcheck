from langchain_core.output_parsers import StrOutputParser, PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents.base import Document
from typing import Optional, List, Dict, Annotated
from typing_extensions import TypedDict
from enum import Enum
from pydantic import BaseModel, Field, AnyHttpUrl
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI


class VerdictEnum(str, Enum):
    true = 'True'
    mostly_true = 'Mostly True'
    uncertain = 'Uncertain'
    mostly_false = 'Mostly False'
    false = 'False'


class VerdictRefs(TypedDict):
    """References that support the verdict."""
    
    title: Annotated[str, ..., "The title of the reference"]
    source: Annotated[AnyHttpUrl, ..., "The source URL of the reference"]
    summary: Annotated[str, ..., "Brief summary of the justifying content in the reference material."]


class Verdict(BaseModel):
    """Use to record your verdict on statement accuracy."""

    verdict: VerdictEnum = Field(description="The verdict.")
    explanation: str = Field(description="Justification for the verdict. Must be derived from the References.")
    references: List[VerdictRefs] = Field(description="The References used to actually justify the verdict.")


llm = ChatOpenAI(model="gpt-4o", streaming=True)

prompt = ChatPromptTemplate.from_template(
    """
    Statement:
    {statement}

    
    References:
    {wiki}

    {web}

    {arxiv}


    You are a journalist on the prestigious fact-checking team at a major news publication. Journalistic integrity is paramount. 
    Your job is to judge if the statement above is accurate and reasonable given the References provided above. The references have
    been gathered by other members of your team.
    """
)

tools = [Verdict]

chain = (
    prompt
    | llm.bind_tools(tools)
    | PydanticToolsParser(tools=tools, first_tool_only=True)
)


def init_chain(settings: Dict):
    llm = ChatOpenAI(model=settings["Model"], streaming=True)
    chain = (
        prompt
        | llm.bind_tools(tools)
        | PydanticToolsParser(tools=tools, first_tool_only=True)
    )
    
    return chain


def judge_statement(input: Dict['statement': str, 'references': List[Document]]) -> Verdict:
    verdict = chain.invoke(input)
    return verdict