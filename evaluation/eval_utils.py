import os
from dotenv import load_dotenv
load_dotenv()

from typing import List, Any
from langsmith import Client
from langsmith.evaluation import evaluate

import pandas as pd

import sys
sys.path.append('..')


from evaluation.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    statement_evaluation
)

METRICS = {
    'faithfulness': faithfulness,
    'answer_relevancy': answer_relevancy,
    'context_precision': context_precision,
    'context_recall': context_recall,
    'statement_evaluation': statement_evaluation
}


def get_ls_dataset(ls_dataset_name: str) -> pd.DataFrame:
    client = Client()
    examples = client.list_examples(dataset_name=ls_dataset_name)
    rows = [row.outputs | row.inputs | {'id': str(row.id)} for row in examples]
    return pd.DataFrame(rows)


# Get RAG QA Chain
def eval_on_ls_dataset(
        metrics: List[str],
        chain: Any,
        ls_dataset_name: str,
        ls_project_name: str,
        ls_experiment_name: str
    ):
    os.environ['LANGCHAIN_PROJECT'] = ls_project_name

    # Get LS Dataset and Eval Dataset
    #print('Getting Test Set from LangSmith')
    #test_df = get_ls_dataset(ls_dataset_name)
    #test_questions = test_df['question'].to_list()
    #test_groundtruths = test_df['ground_truth'].to_list()

    # Evaluate
    print('Running Experiment in LangSmith')
    print(f'Evaluating {metrics}')

    client = Client(auto_batch_tracing=False)
    results = evaluate(
        lambda inputs: chain.invoke({'statement': inputs["input"]}),
        data=ls_dataset_name,
        evaluators=[METRICS[metric] for metric in metrics],
        experiment_prefix=ls_experiment_name,
        num_repetitions=3,
        client=client
    )

    return results