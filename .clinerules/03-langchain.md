# LangChain Framework

LangChain is a framework for developing applications powered by language models. It enables applications that are:
- Data-aware: connect language models to other data sources
- Agentic: allow language models to interact with their environment

## Key Components

1. **LLMs and Chat Models**: Interfaces for large language models
2. **Prompts**: Templates and optimization for model inputs
3. **Chains**: Sequences of operations for complex tasks
4. **Output Parsers**: Structured output formatting
5. **Memory**: State persistence between chain runs
6. **Retrievers**: Query data from external sources
7. **Agents**: LLMs that can use tools and make decisions

## Project Usage Patterns

In our project, LangChain is used for:

1. Generating AI responses based on form inputs
2. Creating structured prompts with system and user messages
3. Parsing outputs into structured Pydantic models
4. Integrating with OpenAI's GPT models

## Current Implementation Patterns

### Setting Up Chat Models

```python
from langchain_openai import ChatOpenAI

# Initialize OpenAI client
llm = ChatOpenAI(
    temperature=0.2, 
    model="gpt-4.1", 
    max_tokens=5000, 
    api_key=openai_api_key
)
```

### Creating Chat Prompts

```python
from langchain.prompts import ChatPromptTemplate

# Define prompt templates with system and user messages
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", """
Based on the user's responses to the reflective questions below, create a concise summary.

USER RESPONSES:
{responses}

SUMMARY:
""")
])

# Format the prompt with specific values
formatted_prompt = prompt.format(responses=formatted_responses)
```

### Structured Output with Pydantic

```python
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# Define Pydantic models for structured output
class SummaryOutput(BaseModel):
    purpose: str = Field(description="A concise summary identifying who the person is and what their purpose is.")
    mantra: str = Field(description="A personalized mantra for the user.")

# Bind the schema to the model
model_with_structure = llm.with_structured_output(SummaryOutput)

# Invoke LLM for summary with structured output
summary_output = model_with_structure.invoke(formatted_prompt)

# Access structured data
purpose = summary_output.purpose
mantra = summary_output.mantra
```

### Processing Form Responses

```python
# Format responses for the prompt
formatted_responses = f"User's Name: {user.name}\n"
formatted_responses += f"User's Astrological Sign: {zodiac_info['sign']} ({zodiac_info['element']} element)\n"
formatted_responses += f"Typical {zodiac_info['sign']} Traits: {zodiac_info['traits']}\n\n"
formatted_responses += "\n".join(
    f"Question {response.question_number}: {get_question_text(response.question_number)}\nResponse: {response.response}\n"
    for response in responses
)

# Generate content using the formatted responses
summary_prompt_formatted = summary_prompt.format(responses=formatted_responses)
summary_output = model_with_structure.invoke(summary_prompt_formatted)
```

## Documentation Links

- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [LangChain GitHub Repository](https://github.com/langchain-ai/langchain)
- [LangChain Modules](https://python.langchain.com/docs/modules/)
- [LangChain Cookbook](https://python.langchain.com/docs/additional_resources/cookbook)
- [LangChain Templates](https://python.langchain.com/docs/templates/)
- [LangChain Integrations](https://python.langchain.com/docs/integrations/providers/)
