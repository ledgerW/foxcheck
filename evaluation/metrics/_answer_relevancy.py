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
from langchain_openai import OpenAIEmbeddings


class VariantQuestionAnswerCommittal(BaseModel):
    """Use to generate a question based on the given answer
    and determine if the answer is noncommittal."""

    question: str = Field(description="The generated question based on the given answer.")
    noncommittal: bool = Field(description="The judgement of if the answer is noncommittal.")


def cosine_similarity_np(embedding_a, embedding_b):
    """
    Calculate the cosine similarity between two vectors using numpy.
    
    Args:
    - embedding_a (np.array): First embedding vector.
    - embedding_b (np.array): Second embedding vector.
    
    Returns:
    - float: Cosine similarity value.
    """
    # Normalize the embeddings to avoid division by zero
    norm_a = np.linalg.norm(embedding_a)
    norm_b = np.linalg.norm(embedding_b)

    # Compute cosine similarity
    cosine_sim = np.dot(embedding_a, embedding_b) / (norm_a * norm_b)
    return cosine_sim


def mean_cosine_similarity(embeddings_list, reference_embedding):
    """
    Calculate the mean cosine similarity of a list of embeddings to a reference embedding.
    
    Args:
    - embeddings_list (list of np.array): A list of embeddings.
    - reference_embedding (np.array): The reference embedding to which the cosine similarity is calculated.
    
    Returns:
    - float: The mean cosine similarity value.
    """
    similarities = []

    for embedding in embeddings_list:
        # Calculate cosine similarity using numpy
        sim = cosine_similarity_np(reference_embedding, embedding)
        similarities.append(sim)

    # Return the mean of the cosine similarities
    return np.mean(similarities)


def calculate_similarity(question: str, generated_questions: list[str]) -> float:
    embeddings = OpenAIEmbeddings(model='text-embedding-3-large')
    question_vec = np.asarray(embeddings.embed_query(question)).reshape(1, -1)
    gen_question_vec = np.asarray(
        embeddings.embed_documents(generated_questions)
    ).reshape(len(generated_questions), -1)
    norm = np.linalg.norm(gen_question_vec, axis=1) * np.linalg.norm(
        question_vec, axis=1
    )
    
    return np.mean((np.dot(gen_question_vec, question_vec.T).reshape(-1,) / norm))


def generate_questions(answer: str) -> Tuple[str, bool]:
    template = """
    Generate a question for the given answer and identify if answer is noncommittal.
    Give noncommittal as True if the answer is noncommittal and False if the answer is committal.
    A noncommittal answer is one that is evasive, vague, or ambiguous.
    For example, "I don't know" or "I'm not sure" are noncommittal answers.

    Answer:
    {answer}
    """
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_template(template)

    tools = [VariantQuestionAnswerCommittal]

    chain = (
        prompt
        | llm.bind_tools(tools)
        | PydanticToolsParser(tools=tools)
    )

    res = chain.invoke({'answer': answer})[0]
    question = res.question
    noncommittal = res.noncommittal

    return question, noncommittal


def answer_relevancy(run: Run, example: Example) -> dict:
    # Assumes your RAG app includes the prediction in the "output" key in its response
    answer: str = run.outputs["answer"].content
    o_question: str = example.inputs['question']
    
    # Get generated question variants based on chain answer
    questions, noncommittals = [], []
    for _ in range(3):
        question, noncommittal = generate_questions(answer)

        if noncommittal:
            return {"key": "Answer Relevancy", "score": 0}
        
        questions.append(question)
        noncommittals.append(noncommittal)

    relevancy_score = calculate_similarity(o_question, questions)   
    
    return {"key": "Answer Relevancy", "score": relevancy_score}