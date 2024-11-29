import os
from dotenv import load_dotenv
load_dotenv()

import yaml
import argparse

from chains.fact_check_chain import base_fact_check, multi_hop_fact_check
from agents.statement_checker import multi_agent_fact_check
from evaluation.eval_utils import eval_on_ls_dataset


CHAINS = {
    'base-check': base_fact_check,
    'multi-hop-fact-check': multi_hop_fact_check,
    'multi-agent-fact-check': multi_agent_fact_check
}



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
    chain = config_yml['chain']

    os.environ['LANGCHAIN_PROJECT'] = ls_project
    os.environ['LANGCHAIN_TRACING_V2'] = 'false'

    # Get Chain
    
    
    # Run RAGAS Evaluation in LangSmith
    result = eval_on_ls_dataset(
        metrics=metrics,
        chain=CHAINS[chain],
        ls_dataset_name=ls_dataset_name,
        ls_project_name=ls_project,
        ls_experiment_name=ls_experiment_name
    )