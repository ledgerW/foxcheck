from langchain_community.retrievers import WikipediaRetriever
from langchain_core.output_parsers import StrOutputParser, CommaSeparatedListOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI


llm = ChatOpenAI(model="gpt-4o", streaming=True)


prompt = ChatPromptTemplate.from_template(
    """
Article:
{article}


You are a journalist on the prestigious fact-checking team at a major news publication. Journalistic integrity is paramount. 
From the Article above, extract all of the verifiable statements. Your team will research each of these statements to evaluate how accurate and reasonable they are.
    
Make sure each statement contains all the necessary information, names, descriptions, etc..., so it can be understood and verified in isolation without referring back to the Article. Also make sure that you only extract
statements that are significant to the story and interesting to the reader.

Return an un-numbered and un-hyphenated list of all the statements.
Each statement should be on a new line.
    """
)

chain = prompt | llm | StrOutputParser()


async def get_statements(content: str) -> List[str]:
    res = await chain.ainvoke(content)
    return [st.strip() for st in res.split('\n')]