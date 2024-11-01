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


class VerdictStrengthOLD(BaseModel):
    """Use this to evaluate the verdict strength of a statement."""

    reference_authority: int = Field(description="Are the reference sources trustworthy and reputable on a scale of 1 to 10 with 10 being very trustworth.", ge=1, le=10)
    reference_confidence: int = Field(description="Are the references confident on a scale of 1 to 10 with 10 being very confident.", ge=1, le=10)
    explanation_completeness: int = Field(description="Is the explanation throrough and air tight on a scale of 1 to 10 with 10 being very thorough.", ge=1, le=10)
    alternate_explanations: int = Field(description="Would an honest expert propose a reasonable alternate explanation in response to this verdict on a scale of 1 to 10 with 10 being very unlikely to propose an alternate explanation.", ge=1, le=10)
    missing_information: int = Field(description="Would an honest expert point out missing information pertinent to statement evaluation on a scale of 1 - 10 with 10 being very unlikely to point out missing information.", ge=1, le=10)


class VerdictStrength(BaseModel):
    """Use this to evaluate the verdict strength of a statement."""

    explanation_completeness: int = Field(description="Is the explanation throrough and air tight on a scale of 1 to 10 with 10 being very thorough.", ge=1, le=10)
    alternate_explanations: int = Field(description="Would an honest expert propose a reasonable alternate explanation in response to this verdict on a scale of 1 to 10 with 10 being very unlikely to propose an alternate explanation.", ge=1, le=10)
    missing_information: int = Field(description="Would an honest expert point out missing information needed to properly evaluate the statement on a scale of 1 - 10 with 10 being very unlikely to point out missing information.", ge=1, le=10)



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


def statement_evaluation(run: Run, example: Example) -> dict:
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