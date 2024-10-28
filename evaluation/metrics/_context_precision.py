from dotenv import load_dotenv
load_dotenv()
import json
from typing import List, Tuple
import numpy as np

from langsmith.schemas import Example, Run
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticToolsParser


class ContextPrecisionVerification(BaseModel):
    """Answer for the verification task wether the context was useful."""

    verdict: int = Field(..., description="Binary (0/1) verdict of verification")


def verify_context_precision(
        question: str,
        answer: str,
        context: str
    ) -> int:
    template = """
    Given Question, Answer, and Context below, verify if the Context was useful in arriving at the given Answer.

    Question:
    {question}

    Answer:
    {answer}

    Context:
    {context}
    """
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_template(template)

    tools = [ContextPrecisionVerification]

    chain = (
        prompt
        | llm.bind_tools(tools)
        | PydanticToolsParser(tools=tools)
    )

    res = chain.invoke({'question': question, 'answer': answer, 'context': context})[0]
    
    return res.verdict


def context_precision(run: Run, example: Example) -> dict:
    question: str = example.inputs['question']
    ground_truth: str = example.outputs["ground_truth"]
    contexts: List[str] = [context.page_content for context in run.outputs['contexts']]
    
    # Verify if the context was relevant / useful to the generated answer.
    verdicts = []
    for context in contexts:
        verdict = verify_context_precision(question, ground_truth, context)
        verdicts.append(verdict)

    # Calculate Precsions@k for each context chunk
    precisions_at_k = []
    for idx, verdict in enumerate(verdicts):
        k = idx+1
        precision_at_k = verdict/k
        precisions_at_k.append(precision_at_k)

    context_precision_score = sum(precisions_at_k) / (sum(verdicts) + 1e-10) 
    
    return {"key": "Context Precision", "score": context_precision_score}