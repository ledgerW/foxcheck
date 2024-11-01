from langchain_core.output_parsers import PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dspy.predict.langchain import LangChainPredict
import dspy
from operator import itemgetter
from typing import Annotated
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI

lm = dspy.LM('openai/gpt-4o', max_tokens=5000)
dspy.configure(lm=lm)

llm = ChatOpenAI(model="gpt-4o", streaming=True)


class QueryOutput(BaseModel):
    """Use to generate a question that will help evaluate
the statement.
"""
    query: Annotated[str, ..., "The question about the statement."]

    def __str__(self):
        return self.query


prompt = ChatPromptTemplate.from_template(
    """
Statement:
{statement}

Research:
{research}


You are a journalist on the prestigious fact-checking team at a major news publication. Journalistic integrity is paramount. 
Above is the Statement you are tasked with fact-checking, along with some research that has been gathered on the 
Statement (if any).

Given, the Statement and the Research you have so far, write a follow up question that will help evaluate the 
potentially complex Statement above. The follow up question should be with respect to the research (if any) and
should include specific information from the research if needed, because the research information won't be
available to your teammate that receives this follow up question.
"""
)

tools = [QueryOutput]
get_query = lambda x: x.query

chain = (
    prompt 
    | llm.bind_tools(tools) 
    | PydanticToolsParser(tools=tools, first_tool_only=True)
    | get_query
)

dspy_chain = (
    LangChainPredict(prompt, llm.bind_tools(tools))
    | PydanticToolsParser(tools=tools, first_tool_only=True)
)


def get_query(content: str) -> str:
    res = chain.invoke(content)
    return [st.strip() for st in res.split('\n')]