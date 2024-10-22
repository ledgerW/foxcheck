import sys
sys.path.append('../')
import time

import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider

from chains.statement_chain import get_statements
from chains.wikipedia_chain import retriever as wiki_retriever
from chains.tavily_chain import retriever as web_retriever
from chains.arxiv_chain import retriever as arxiv_retriever
from chains.adjudicator_chain import init_chain as init_judge_chain

from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter


@cl.on_chat_start
async def on_chat_start():
    settings = await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="OpenAI - Model",
                values=["gpt-4o", "gpt-4o-mini"],
                initial_index=0,
            )
        ]
    ).send()
    await setup_chain(settings)
    await cl.Message(content="Enter a statement you want to check").send()


@cl.on_settings_update
async def setup_chain(settings):
    judge_chain = init_judge_chain(settings)

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

    cl.user_session.set("fact_check_chain", fact_check_chain)


@cl.on_message
async def main(message):
    fact_check_chain = cl.user_session.get("fact_check_chain")

    msg = cl.Message(content="Checking...", elements=[])
    verdict = None
    verdict = await fact_check_chain.ainvoke(message.content)
    #async for chunk in fact_check_chain.astream({"question": message.content}):
    #    if chunk.get("contexts"):
    #        contexts = chunk["contexts"]

    #    if answer := chunk.get("answer"):
    #        await msg.stream_token(answer.content)

    #source_elements = []
    #for doc in contexts:
    #    doc_path = await get_pdf_object(doc)
    #    source_elements.append(cl.Text(content=doc_path))
    
    msg.content = f"**Verdict**: {verdict.dict().get('verdict').value}\n**Explanation**: {verdict.dict().get('explanation')}"

    source_elements = []
    for ref in verdict.dict().get('references'):
        source_elements.append(cl.Text(content=f"{ref['summary']}\n[{ref['title']}]({ref['source']})"))
    
    msg.elements = source_elements
    await msg.send()