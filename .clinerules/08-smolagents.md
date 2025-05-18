# Smolagents Framework

Smolagents is a powerful Python framework for building AI agent systems that can perform complex tasks through tool use, planning, and execution. This guide provides a comprehensive overview of how to use smolagents in your projects.

## Key Components

### 1. Agent Types

Smolagents provides several agent types for different use cases:

- **CodeAgent**: A powerful agent that can write and execute Python code to solve tasks. It can manage other agents and use tools.
- **ToolCallingAgent**: An agent that uses tools to accomplish tasks through a structured action/observation loop.
- **ChatAgent**: A simple agent for conversational interactions.

### 2. Tools

Tools are the primary way agents interact with external systems and data sources:

- **Built-in tools**: DuckDuckGoSearchTool, VisitWebpageTool, etc.
- **Custom tools**: Created using the `@tool` decorator or by implementing the Tool interface.
- **LangChain tools**: Can be integrated using `Tool.from_langchain()`.

### 3. Models

Smolagents supports various LLM providers:

- **LiteLLMModel**: A wrapper for LiteLLM that supports multiple providers (OpenAI, Anthropic, etc.)
- **OpenAIModel**: Direct integration with OpenAI models.
- **AnthropicModel**: Direct integration with Anthropic models.

## Setting Up Smolagents

### Installation

```bash
pip install smolagents
# For specific integrations
pip install "smolagents[litellm]"  # For LiteLLM support
```

### Basic Configuration

```python
from smolagents import CodeAgent, ToolCallingAgent, LiteLLMModel
from smolagents import DuckDuckGoSearchTool, VisitWebpageTool

# Initialize an LLM
llm = LiteLLMModel(
    "anthropic/claude-3-opus-20240229",
    temperature=0.1,
    max_tokens=2000,
    api_key="your-api-key"
)

# Create a tool-using agent
web_agent = ToolCallingAgent(
    tools=[DuckDuckGoSearchTool(), VisitWebpageTool()],
    model=llm,
    max_steps=5,
    name="web_search",
    description="Runs web searches for you."
)

# Create a code agent that can manage other agents
manager_agent = CodeAgent(
    tools=[],  # Direct tools for the manager
    model=llm,
    managed_agents=[web_agent],  # Agents managed by this agent
    additional_authorized_imports=["time", "numpy", "pandas"],
    planning_interval=2  # How often to re-plan
)
```

## Creating Custom Tools

### Using the @tool Decorator

```python
from smolagents import tool

@tool
def semantic_search(
    query: str,
    k: int = 3,
) -> str:
    """
    Search a vector database for semantically similar documents.
    
    Args:
        query: The query to search for.
        k: The number of documents to return.
    """
    # Implementation here
    return "Search results..."
```

### Converting LangChain Tools

```python
from smolagents import Tool
from langchain.agents import load_tools

# Convert a LangChain tool to a smolagents Tool
arxiv_tool = Tool.from_langchain(load_tools(["arxiv"])[0])
```

## Customizing Agent Prompts

Smolagents allows customizing the prompts used by agents:

```python
import yaml
import pathlib

# Load custom prompt templates from YAML
custom_prompt_templates = yaml.safe_load(
    pathlib.Path("custom_prompts.yaml").read_text()
)

# Create a custom ToolCallingAgent with modified prompts
custom_agent = ToolCallingAgent(
    tools=[...],
    model=llm,
    prompt_templates=custom_prompt_templates
)
```

The YAML file should contain the prompt templates for different agent functions:

```yaml
system_prompt: |-
  You are an expert assistant who can solve any task using tool calls...

planning:
  initial_facts: |-
    Below I will present you a task...
  
  initial_plan: |-
    You are a world expert at making efficient plans...

# Additional prompt sections...
```

## Integrating with FastAPI

Smolagents can be easily integrated with FastAPI for creating API endpoints:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class TaskInput(BaseModel):
    task: str

class TaskOutput(BaseModel):
    output: str

@app.post("/agent", response_model=TaskOutput)
def run_agent(input: TaskInput) -> TaskOutput:
    # Run the agent with the input task
    result = manager_agent.run(input.task)
    return TaskOutput(output=result)
```

## Telemetry and Monitoring

Smolagents supports OpenTelemetry for monitoring agent performance:

```python
from phoenix.otel import register
from openinference.instrumentation.smolagents import SmolagentsInstrumentor

# Configure the Phoenix tracer
tracer_provider = register(
  project_name="your-project-name"
)

# Instrument smolagents
SmolagentsInstrumentor().instrument(tracer_provider=tracer_provider)
```

## Best Practices

1. **Agent Hierarchy**: Use a CodeAgent as a manager for specialized ToolCallingAgents.

2. **Tool Design**: 
   - Keep tools focused on a single responsibility
   - Provide clear documentation in tool docstrings
   - Use type hints for better agent understanding

3. **Prompt Engineering**:
   - Customize prompts for specific use cases
   - Include examples in system prompts for better performance
   - Test different prompt variations

4. **Error Handling**:
   - Set appropriate max_steps to prevent infinite loops
   - Implement error handling in custom tools
   - Use planning_interval to allow agents to adapt to changing conditions

5. **Security**:
   - Limit CodeAgent's additional_authorized_imports to necessary modules
   - Validate inputs in custom tools
   - Consider using a sandbox for code execution

## Common Patterns

### Multi-Agent Systems

```python
# Create specialized agents
web_agent = ToolCallingAgent(
    tools=[DuckDuckGoSearchTool(), VisitWebpageTool()],
    model=llm,
    name="web_search"
)

data_agent = ToolCallingAgent(
    tools=[custom_data_tool],
    model=llm,
    name="data_analysis"
)

# Create a manager agent
manager_agent = CodeAgent(
    tools=[],
    model=llm,
    managed_agents=[web_agent, data_agent]
)
```

### Custom Tool Implementation

```python
from smolagents import Tool
from typing import Dict, Any

class CustomDatabaseTool(Tool):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        # Define tool metadata
        super().__init__(
            name="database_query",
            description="Query a database for information",
            input_schema={
                "query": {
                    "type": "string",
                    "description": "SQL query to execute"
                }
            }
        )
    
    def _run(self, query: str) -> str:
        # Implementation to run the query
        # ...
        return "Query results"
```

### Stateful Agents

```python
class StatefulAgent(ToolCallingAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = {}
    
    def run(self, task: str) -> str:
        # Access or update state before/after running
        self.state["last_task"] = task
        result = super().run(task)
        self.state["last_result"] = result
        return result
```

## Conclusion

Smolagents provides a flexible and powerful framework for building AI agent systems. By understanding its key components and following best practices, you can create sophisticated agent-based applications that leverage the power of LLMs and custom tools to solve complex tasks.

For more information, refer to the official documentation and examples in the smolagents repository.
