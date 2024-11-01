from dotenv import load_dotenv
load_dotenv()

import dspy
import functools

import pandas as pd

df = pd.read_csv('fact-checking-v1.csv')\
    .rename(columns={'input_input': 'statement', 'output_output': 'verdict'})\
    .sample(frac=1.0)\
    .reset_index(drop=True)