from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter

from chains.wikipedia_chain import retriever as wiki_retriever
from chains.tavily_chain import retriever as web_retriever
from chains.arxiv_chain import retriever as arxiv_retriever
from chains.query_chain import chain as query_chain
from chains.adjudicator_chain import chain as judge_chain
from langchain_core.load import dumpd, dumps, load, loads
import os
import json


# DSPy-optimized Langchain Chain
#with open("chains/saved_chains/opt_multi_hop_fact_check.json", "r") as fp:
#    opt_multi_hop_fact_check = loads(
#      json.load(fp),
#      secrets_map={
#        "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
#        "TAVILY_API_KEY": os.environ["TAVILY_API_KEY"],
#        "LANGCHAIN_API_KEY": os.environ["LANGCHAIN_API_KEY"],
#        "LANGCHAIN_PROJECT": os.environ["LANGCHAIN_PROJECT"],
#        "LANGCHAIN_TRACING_V2": os.environ["LANGCHAIN_TRACING_V2"],
#      }
#    )

base_fact_check = (
    RunnablePassthrough.assign(
      wiki = itemgetter('statement') | wiki_retriever,
      web = itemgetter('statement') | web_retriever,
      arxiv = itemgetter('statement') | arxiv_retriever
    )
    | {
      'statement': itemgetter('statement'),
      'research': lambda x: "\n\n".join([str(x['wiki']), str(x['web']), str(x['arxiv'])])
    }
    | judge_chain
)


multi_hop_fact_check = (
    RunnablePassthrough.assign(research=lambda x: "")
    | RunnablePassthrough.assign(query=query_chain)
    | RunnablePassthrough.assign(
        wiki = itemgetter('query') | wiki_retriever,
        web = itemgetter('query') | web_retriever,
        arxiv = itemgetter('query') | arxiv_retriever
    )
    | {
        'statement': itemgetter('statement'),
        'research': lambda x: "\n\n".join([str(x['wiki']), str(x['web']), str(x['arxiv'])])
      }
    | RunnablePassthrough.assign(query=query_chain)
    | RunnablePassthrough.assign(
        wiki = itemgetter('query') | wiki_retriever,
        web = itemgetter('query') | web_retriever,
        arxiv = itemgetter('query') | arxiv_retriever
    )
    | {
        'statement': itemgetter('statement'),
        'research': lambda x: "\n\n".join([str(x['research']), str(x['wiki']), str(x['web']), str(x['arxiv'])])
      }
    | judge_chain
)