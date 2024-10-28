import os
from dotenv import load_dotenv
load_dotenv()

import yaml
import argparse


from chains.wikipedia_chain import retriever as wiki_retriever
from chains.tavily_chain import retriever as web_retriever
from chains.arxiv_chain import retriever as arxiv_retriever
from chains.adjudicator_chain import chain as judge_chain

from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter

from evaluation.eval_utils import eval_on_ls_dataset



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default=None, help='YAML config file to run')
    parser.add_argument('--config_dir', default=None, help='Directory of YAML config files to run')
    args = parser.parse_args()
    with open(args.config, 'r') as file:
        config_yml = yaml.safe_load(file)

    
    ls_project = config_yml['ls_project']
    ls_dataset_name = config_yml['ls_dataset_name']
    ls_experiment_name = config_yml['ls_experiment_name']
    metrics = config_yml['metrics']

    os.environ['LANGCHAIN_PROJECT'] = ls_project
    os.environ['LANGCHAIN_TRACING_V2'] = 'false'

    # Get Chain
    fact_check_chain = (
        {"statement": RunnablePassthrough(), "wiki": wiki_retriever, 'web': web_retriever, 'arxiv': arxiv_retriever}
        | RunnablePassthrough.assign(
            statement=itemgetter('statement'),
            wiki=itemgetter('wiki'),
            web=itemgetter('web'),
            arxiv=itemgetter('arxiv')
        )
        | judge_chain
    )
    
    # Run RAGAS Evaluation in LangSmith
    result = eval_on_ls_dataset(
        metrics=metrics,
        chain=fact_check_chain,
        ls_dataset_name=ls_dataset_name,
        ls_project_name=ls_project,
        ls_experiment_name=ls_experiment_name
    )