import os
from dotenv import load_dotenv
load_dotenv()

from typing import Dict, Tuple
from collections.abc import Callable
import yaml
import argparse
import asyncio

from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

from policy_rag.text_utils import DocLoader
from policy_rag.text_utils import get_recursive_token_chunks, get_semantic_chunks
from policy_rag.sdg_utils import ragas_sdg, upload_dataset_langsmith


# Config Options
CHUNK_METHOD = {
    'token-overlap': get_recursive_token_chunks,
    'semantic': get_semantic_chunks
}

EMBEDDING_MODEL_SOURCE = {
    'openai': OpenAIEmbeddings,
    'huggingface': HuggingFaceEmbeddings
}


# Helpers
def get_chunk_func(chunk_method: Dict) -> Tuple[Callable, Dict]:
    chunk_func = CHUNK_METHOD[chunk_method['method']]

    if chunk_method['method'] == 'token-overlap':
        chunk_func_args = chunk_method['args']
    
    if chunk_method['method'] == 'semantic':
        args = chunk_method['args']
        chunk_func_args = {
            'embedding_model': EMBEDDING_MODEL_SOURCE[args['model_source']](model=args['model_name']),
            'breakpoint_type': args['breakpoint_type']
        }

    return chunk_func, chunk_func_args



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='YAML config file')
    args = parser.parse_args()
    with open(args.config, 'r') as file:
        config_yml = yaml.safe_load(file)

    data_dir = config_yml['data_dir']
    chunk_method = config_yml['chunk_method']
    n_qa_pairs = config_yml['n_qa_pairs']
    ls_project = config_yml['ls_project']
    ls_dataset_name = config_yml['ls_dataset_name']
    ls_dataset_description = config_yml['ls_dataset_description']


    # Load Raw Data
    print('Loading Docs')
    loader = DocLoader()
    docs = loader.load_dir(data_dir)


    # Chunk Docs
    print('Chunking Docs')
    chunk_func, chunk_func_args = get_chunk_func(chunk_method)
    chunks = chunk_func(docs=docs, **chunk_func_args)
    print(f"len of chunks: {len(chunks)}")


    # SDG
    print('RAGAS SDG')
    test_set = asyncio.run(ragas_sdg(
        context_docs=chunks,
        n_qa_pairs=n_qa_pairs,
        embedding_model=OpenAIEmbeddings(model='text-embedding-3-large')
    ))

    # Save as LangSmith Dataset
    os.environ['LANGCHAIN_PROJECT'] = ls_project

    print('Uploading to LangSmith')
    upload_dataset_langsmith(
        dataset=test_set,
        dataset_name=ls_dataset_name,
        description=ls_dataset_description
    )