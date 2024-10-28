from dotenv import load_dotenv
load_dotenv()
import json
from typing import List

from langsmith.schemas import Example, Run
from pydantic import BaseModel, Field

from langchain_core.documents.base import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticToolsParser



class Statements(BaseModel):
    """Use to record each statement in the answer."""

    statements: List[str] = Field(description="The statements found in the text.")


class ContextRecallAttribution(BaseModel):
    """Use to determine if a statement can be attributed to the context."""

    attributed: int = Field(..., description="Binary (0/1) verdict of whether statement can be attributed to context.")



def extract_statements(ground_truth: str) -> List[str]:
    template = """
    Extract all statements from the Text below. Record each statement as
    a self-contained logical sentence that can be used to verify attribution
    later.

    Text:
    {ground_truth}
    """
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_template(template)

    tools = [Statements]

    chain = (
        prompt
        | llm.bind_tools(tools)
        | PydanticToolsParser(tools=tools)
    )

    return chain.invoke({'ground_truth': ground_truth})[0].statements


def get_statement_attribution(statement: str, formatted_docs: str) -> List[str]:
    template = """
    Given a Statement and a Context, classify if the Statement can be attributed
    to the Context or not. Use only (1) or (0) as a binary classification.
    
    Statement: {statement}
    
    Context:
    {formatted_docs}
    """
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_template(template)

    tools = [ContextRecallAttribution]

    chain = (
        prompt
        | llm.bind_tools(tools)
        | PydanticToolsParser(tools=tools)
    )

    res = chain.invoke({'statement': statement, 'formatted_docs': formatted_docs})
    attributed = res[0].attributed
    
    return attributed


def context_recall(run: Run, example: Example) -> dict:
    ground_truth: str = example.outputs["ground_truth"]
    retrieved_docs: List[Document] = run.outputs["contexts"]
    formatted_docs: str = "\n".join([doc.page_content for doc in retrieved_docs])
    
    statements = extract_statements(ground_truth)
    
    attributions = []
    for statement in statements:
        attribution = get_statement_attribution(statement, formatted_docs)
        attributions.append(attribution)

    context_recall_score = sum(attributions) / len(attributions) if attributions else None
    
    return {"key": "Context Recall", "score": context_recall_score}