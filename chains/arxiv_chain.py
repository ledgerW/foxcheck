from langchain_community.retrievers import ArxivRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from typing import Optional, List, Dict, TypedDict, Annotated
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI



class WikipediaMetaData(TypedDict):
    """Metadata for a Wikipedia article"""
    title: str
    summary: str
    source: str


class WikipediaCheckOutput(TypedDict):
    """Output of Wikipedia Chain to verify a statement"""
    statement: Annotated[str, ..., "The statement to check"]
    verdict: Annotated[str, ..., "How accurate and reasonable the statement is"]
    context: Annotated[List[WikipediaMetaData], "The returned Wikipedia references"]


llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)

retriever = ArxivRetriever(name='arxiv', load_max_docs=3, get_full_documents=False)

prompt = ChatPromptTemplate.from_template(
    """
    Is the Statement below accurate or reasonable given the Web content provided?

    If no Web content was provided, simply indicate that you weren't able to find
    anything related to the statement on the Web.
    
    Web: {context}

    Statement: {statement}
    """
)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

chain = (
    {"context": retriever, "statement": RunnablePassthrough()}
    | RunnablePassthrough.assign(statement=itemgetter('statement'), context=itemgetter('context'))
    | {
        'statement': itemgetter('statement'),
        'verdict': prompt | llm | StrOutputParser(),
        'context': itemgetter('context')
      }
)


async def check_arxiv(statement: str) -> WikipediaCheckOutput:
    return await chain.ainvoke(statement)


async def acheck_arxiv(statements: List[str]) -> List[WikipediaCheckOutput]:
    all_checks = []
    for statement in statements:
        print(statement)
        res = await chain.ainvoke(statement)
        all_checks.append(res)

    #for idx, check in enumerate(all_checks):
    #    all_checks[idx]['context'] = [ref.metadata for ref in check['context']]

    return all_checks