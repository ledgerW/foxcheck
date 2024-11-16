from dotenv import load_dotenv
from sqlmodel import all_

load_dotenv()

import sys
sys.path.append('../..')

from chains.adjudicator_chain import Verdict

import json
from typing import List, Tuple
import numpy as np

from langsmith.schemas import Example, Run
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticToolsParser


class StatementWorthiness(BaseModel):
    """Use this to evaluate the worthiness of a statement for verification."""

    objective_truth: bool = Field(description="This statement represents an objective fact or truth.")
    verifiable: int = Field(description="Is the statement verifiable within the body of information available on the internet on a scale of 1 to 10 with 10 being definitely verifiable.", ge=1, le=10)
    significant: int = Field(description="Is this statement significant to the overall argument or conclusion of the article it came from? Do other statements or conclusions in the article rely on this statement being true? Answer on a scale of 1 to 10 with 10 being very significant", ge=1, le=10)
    



def _verdict_strength(
    statement: str,
    verdict: str,
    explanation: str,
    references: str
) -> VerdictStrength:
    template = """
Statement:
{statement}

Verdict:
{verdict}

Explanation:
{explanation}

References:
{references}


You've been chosen to judge the quality of the Verdict, Explanation, and References that were produced for the Statement.
Consider factors like, the authority of the reference sources, the confidence of the references, do the references and 
explanation address every aspect of the statement, is there missing information needed to evaluate the statement, are there 
any reasonable doubts about the verdict explanation.
"""
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)

    prompt = ChatPromptTemplate.from_template(template)

    tools = [VerdictStrength]

    chain = (
        prompt
        | llm.bind_tools(tools)
        | PydanticToolsParser(tools=tools)
    )

    result = chain.invoke({'statement': statement, 'verdict': verdict, 'explanation': explanation, 'references': references})[0]

    return result


def statement_worthiness(run: Run, example: Example) -> dict:
    statement: str = example.inputs['input']
    verdict: Verdict = run.outputs["output"]

    verdict = verdict.dict()
    verdict_strength = _verdict_strength(
        statement=statement,
        verdict=verdict['verdict'],
        explanation=verdict['explanation'],
        references=json.dumps(verdict['references'])
    )

    explanation_completeness = verdict_strength.explanation_completeness
    alternate_explanations = verdict_strength.alternate_explanations
    missing_information = verdict_strength.missing_information

    verdict_strength_score = (explanation_completeness + alternate_explanations + missing_information) / 3
    
    all_scores = {
        'results': [
            {'key': 'explanation_completeness', 'score': explanation_completeness},
            {'key': 'alternate_explanations', 'score': alternate_explanations},
            {'key': 'missing_information', 'score': missing_information},
            {"key": "Verdict Strength", "score": verdict_strength_score}
        ]
    }
    return all_scores