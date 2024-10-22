from langchain_community.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

async def process_langchain_request(query: str, user):
    # Initialize OpenAI language model
    llm = OpenAI(temperature=0.7)

    # Create a prompt template
    prompt = PromptTemplate(
        input_variables=["query", "username"],
        template="User {username} asks: {query}\nAI Assistant: "
    )

    # Create an LLMChain
    chain = LLMChain(llm=llm, prompt=prompt)

    # Run the chain
    response = await chain.arun(query=query, username=user.username)

    return response
