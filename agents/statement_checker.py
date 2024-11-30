from dotenv import load_dotenv
from langchain_core.runnables import RunnablePassthrough
load_dotenv()

from typing import Literal, Annotated, List, Sequence, Optional
from typing_extensions import TypedDict

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.output_parsers import PydanticToolsParser
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.documents.base import Document
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter

from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
from langgraph.pregel import RetryPolicy

from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum
from datetime import datetime

from chains.wikipedia_chain import retriever as wiki_retriever
from chains.arxiv_chain import retriever as arxiv_retriever
from chains.tavily_chain import retriever as web_retriever
from chains.adjudicator_chain import chain as judge_chain, Verdict


# State
class GraphState(TypedDict):
    current_date: str
    statement: str
    messages: Annotated[Sequence[BaseMessage], add_messages]
    research: Optional[List[ToolMessage]]
    verdict: Optional[Verdict]
    improved: bool
    next: str


# Tools
## Wikipedia
@tool('search_wikipedia')
def search_wikipedia(query: str) -> List[dict]:
    """Search Wikipedia. Useful for when you need well-established information."""
    docs = wiki_retriever.invoke(query)
    return [doc.dict() for doc in docs]

search_wikipedia_node = ToolNode([search_wikipedia])


## Arxiv
@tool("search_arxiv")
def search_arxiv(query: str) -> List[dict]:
    """Search Arxiv. Useful for when you need scholarly technical papers."""
    docs = arxiv_retriever.invoke(query)
    return [doc.dict() for doc in docs] 

search_arxiv_node = ToolNode([search_arxiv])


## Web
@tool("search_web")
def search_web(query: str) -> List[dict]:
    """Search the Web. Useful for when you need recent information or anything that wouldn't be found in Wikipedia or Scholarly journals."""
    docs = web_retriever.invoke(query)
    return [doc.dict() for doc in docs]

search_web_node = ToolNode([search_web])


## Judge as Tool
class JudgeStatement(BaseModel):
    """Render a Verdict on the Statement given the available research. 
    Useful when you're confident you have sufficient information to render a verdict on the statement."""
    statement: str = Field(description="the statement to be Judged.")

def judge(state: GraphState) -> GraphState:
    """Render a Verdict on the Statement given the available research. Useful when you probably have enough information about the Statement."""
    statement = state['statement']
    research = state['research']
    verdict = judge_chain.invoke({'statement': statement, 'research': research})
    return {'verdict': verdict}


# Reviewer Agent (returns message as ToolMessage)
def review(state: GraphState) -> GraphState:
    """Render a Verdict on the Statement given the available research. Useful when you probably have enough information about the Statement."""
    
    statement = state['statement']
    verdict = state['verdict']

    opening_prompt = """
You are a journalist on the review committee of a prestigious fact-checking team at a major news publication.
Journalistic integrity is paramount. A Statement and Verdict are provided below, and you must review them to ensure 
they meet quality standards.

This Statement: {statement}

The Verdict: {verdict}


A high quality statement fact-check result (a Verdict) will a) have a complete explanation, b) will not have or will take into account 
reasonable alternate explanations, and c) will not be based on information that isn't present or will take into account 
lack of information. In other words, it will be air-tight and cogent and ideally be corroborated by more than one source.

Does this Verdict need improvement or is it finished and ready to publish?
""".format(statement=statement, verdict=verdict)

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(opening_prompt)
        ]
    )

    class ReviewFeedback(BaseModel):
        next: Annotated[Literal["Improve", "FINISH"], "Does this Verdict need Improvement, or is it FINISHED?"]
        comments: Annotated[str, "If recommending to Improve, then why?  What does fact-check team need to do to make this better?"]

    tools = [ReviewFeedback]

    llm = ChatOpenAI(model="gpt-4o", streaming=True).bind_tools(tools)
    chain = prompt | llm

    message = chain.invoke({'statement': statement, 'verdict': verdict})
    review_message = ToolMessage(
        content=message.tool_calls[0]['args']['comments'],
        tool_call_id=state['messages'][-1].tool_calls[0]['id'],
        name='review',
        status='success'
    )
    try:
        next = 'FINISH' if state['improved'] else message.tool_calls[0]['args']['next']
    except:
        next = message.tool_calls[0]['args']['next']
    return {'messages': [review_message], 'next': next, 'improved': True}



def supervisor_agent(state: GraphState) -> GraphState:
    def next_action(message: AIMessage) -> str:
        if message.tool_calls:
            return message.tool_calls[0]['name']
        else:
            print('Error')
            return 'supervisor'
        
    ## All Tools
    tools = [search_wikipedia, search_arxiv, search_web, JudgeStatement]
    
    # Supervisor
    opening_prompt = """
    You are a journalist on the prestigious fact-checking team at a major news publication. Journalistic integrity is paramount. 

    This is the Statement you are tasked with fact-checking: {statement}

    A high quality statement fact-check result will a) have a complete explanation, b) will not have or will take into account 
    reasonable alternate explanations, and c) will not be based on information that isn't present or will take into account 
    lack of information. In other words, it will be air-tight and cogent and ideally be corroborated by more than one source.

    Below is the work you've done so far.
    """

    closing_prompt = """
    Given the work done so far, which one of your available tool actions do you want to 
    take next? You must chose one of your available tools.
    """


    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(opening_prompt),
            MessagesPlaceholder(variable_name="messages"),
            SystemMessage(closing_prompt)
        ]
    )

    llm = ChatOpenAI(model="gpt-4o", streaming=True).bind_tools(tools)
    supervisor_chain = prompt | llm
    message = supervisor_chain.invoke(state)
    research = [msg for msg in state['messages'] if isinstance(msg, ToolMessage)]
    next = next_action(message)
    return {'messages': [message], 'research': research, 'next': next}


# The Graph
graph = StateGraph(GraphState)

graph.add_node('supervisor', supervisor_agent, retry=RetryPolicy(max_attempts=2))
graph.add_node('wikipedia', search_wikipedia_node, retry=RetryPolicy(max_attempts=2))
graph.add_node('arxiv', search_arxiv_node, retry=RetryPolicy(max_attempts=2))
graph.add_node('web', search_web_node, retry=RetryPolicy(max_attempts=2))
graph.add_node('judgement', judge, retry=RetryPolicy(max_attempts=2))
graph.add_node('review', review, retry=RetryPolicy(max_attempts=2))

graph.add_edge(START, 'supervisor')
graph.add_conditional_edges(
    'supervisor',
    lambda x: x['next'],
    {
        'search_wikipedia': 'wikipedia',
        'search_arxiv': 'arxiv',
        'search_web': 'web',
        'JudgeStatement': 'judgement'
    }
)
graph.add_edge('wikipedia', 'supervisor')
graph.add_edge('arxiv', 'supervisor')
graph.add_edge('web', 'supervisor')
graph.add_edge('judgement', 'review')

graph.add_conditional_edges(
    'review',
    lambda x: x['next'],
    {
        'Improve': 'supervisor',
        'FINISH': END
    }
)

agent_graph = graph.compile()
agent_graph.name = "Multi-Agent Statement Checker"



## As Chain
get_state = lambda x: GraphState(**x)
get_verdict = lambda x: x['verdict']
get_messages = lambda x: [HumanMessage(x['statement'])]
get_improved = lambda x: False

multi_agent_fact_check = (
    RunnablePassthrough.assign(
        messages = get_messages,
        improved = get_improved
    )
    | get_state | agent_graph
    | get_verdict
).with_config({"run_name": "Multi-Agent Statement Checker"})