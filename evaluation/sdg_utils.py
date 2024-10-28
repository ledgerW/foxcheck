import os

from ragas.testset.generator import TestsetGenerator
from ragas.testset.generator import TestDataset
from ragas.testset.evolutions import simple, reasoning, multi_context
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.documents.base import Document
from typing import List


from langsmith import Client
from pandas import DataFrame
import asyncio


async def ragas_sdg(
        context_docs: List[Document],
        n_qa_pairs: int = 20,
        embedding_model: OpenAIEmbeddings = OpenAIEmbeddings(model='text-embedding-3-large')
    ) -> TestDataset:
    generator_llm = ChatOpenAI(model="gpt-4o")
    critic_llm = ChatOpenAI(model="gpt-4o-mini")
    embeddings = embedding_model

    generator = TestsetGenerator.from_langchain(
        generator_llm,
        critic_llm,
        embeddings
    )

    distributions = {
        simple: 0.5,
        multi_context: 0.25,
        reasoning: 0.25
    }

    test_set = generator.generate_with_langchain_docs(context_docs, n_qa_pairs, distributions)

    return test_set



def upload_dataset_langsmith(
        dataset: TestDataset | DataFrame,
        dataset_name: str,
        description: str
    ) -> None:
    client = Client()

    ls_dataset = client.create_dataset(
        dataset_name=dataset_name, description=description
    )

    # TODO: implement a Pydantic model to validate input dataset
    if type(dataset) == TestDataset:
        dataset_df = dataset.to_pandas()
    elif type(dataset) == DataFrame:
        dataset_df = dataset
    else:
        raise TypeError('Dataset must be ragas TestDataset or pandas DataFrame')

    for idx, row in dataset_df.iterrows():
        client.create_example(
            inputs={"question" : row["question"], "context": row["contexts"]},
            outputs={"ground_truth" : row["ground_truth"]},
            metadata={'metadata': row['metadata'][0], "evolution_type": row['evolution_type']},
            dataset_id=ls_dataset.id
        )