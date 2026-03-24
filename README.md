# OpenGraph

*An open-source framework for building agentic AI applications with graph-structured knowledge, modular workflows, and developer-first tools.*

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/yourusername/opengraph-ai/actions)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/yourusername/opengraph-ai/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/yourusername/opengraph-ai/pulls)

## Overview

OpenGraph is an open-source framework designed to simplify the development of agentic AI applications. It provides a graph-native architecture for representing knowledge, orchestrating modular workflows, and integrating with various AI models and data sources.

### Why OpenGraph?

Building agentic AI systems often involves complex interactions between multiple components, state management, and reasoning over interconnected data. Traditional approaches can lead to monolithic codebases that are hard to maintain and scale. OpenGraph addresses this by offering:

- **Graph-based reasoning**: Represent knowledge and relationships as graphs for more intuitive and powerful AI reasoning
- **Modular workflows**: Build complex agent behaviors from composable, reusable components
- **Developer-first tools**: Focus on productivity with clean APIs, CLI tools, and extensive documentation

### Core Philosophy

OpenGraph embraces an **agent-native architecture** that prioritizes:

- **Graph-structured knowledge**: Everything is a graph - from data representation to workflow orchestration
- **Modular components**: Small, focused modules that can be mixed and matched
- **Openness**: Extensible design that welcomes community contributions and integrations
- **Developer experience**: Intuitive APIs and tools that make building AI agents accessible

## Key Features

- **Graph-native knowledge representation**: Model complex relationships and reasoning patterns as graphs
- **Agent workflow engine**: Orchestrate multi-step agent behaviors with conditional logic and loops
- **Flexible API layer**: RESTful and GraphQL APIs for easy integration
- **CLI tool**: Command-line interface for development, testing, and deployment
- **Extensible module/plugin design**: Add custom agents, tools, and connectors

### Example Use Cases

- **AI Assistants**: Build conversational agents that maintain context across multiple interactions
- **Multimodal Agents**: Process and reason over text, images, and other data types
- **Data Agents**: Automate data analysis, transformation, and visualization workflows
- **Workflow Automation**: Create custom business logic agents for specific domains

## Repository Structure

```
├── src/                    # Core framework code
│   ├── agents/            # Agent implementations
│   ├── prompts/           # Prompt templates and utilities
│   └── utils/             # Helper functions and utilities
├── examples/              # Example applications and demos
├── data/                  # Sample datasets and configuration
├── archive/               # Legacy code and documentation
└── docs/                  # Documentation (future)
```

## Installation

### Using Python / pip

```bash
pip install opengraph-ai
```

### Using Docker

```bash
docker pull opengraph/opengraph-ai:latest
docker run -p 8000:8000 opengraph/opengraph-ai
```

### Using CLI

```bash
# Install CLI tool
pip install opengraph-cli

# Verify installation
opengraph --version
```

## Quick Start

### Basic Agent Setup

```python
from opengraph import Agent, GraphEngine

# Initialize the graph engine
graph = GraphEngine()

# Create a simple agent
agent = Agent(
    name="HelloAgent",
    graph=graph,
    tools=["web_search", "text_analyzer"]
)

# Run the agent
response = agent.run("What is the weather today?")
print(response)
```

### Registering Custom Tools

```python
from opengraph import Tool

@Tool.register("custom_calculator")
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    return eval(expression)

# The tool is now available to all agents
agent = Agent(tools=["custom_calculator"])
```

### CLI Usage

```bash
# Create a new agent project
opengraph init my-agent

# Run an agent with a query
opengraph run --agent hello_agent --query "Hello world"

# List available tools
opengraph tools list
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI / SDK     │    │   API Layer     │    │   Connectors    │
│                 │    │                 │    │                 │
│ • Command line  │◄──►│ • REST API      │◄──►│ • LLM APIs      │
│ • SDK libraries │    │ • GraphQL       │    │ • Data sources  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Workflow       │    │   Agent Engine  │    │   Graph Engine  │
│  Orchestrator   │    │                 │    │                 │
│                 │◄──►│ • Agent logic   │◄──►│ • Knowledge     │
│ • Task queues   │    │ • State mgmt    │    │ • Relationships │
│ • Conditional   │    │ • Tool calling  │    │ • Reasoning     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Memory /      │
                    │   State Store   │
                    │                 │
                    │ • Persistent    │
                    │ • Distributed   │
                    │ • Versioned     │
                    └─────────────────┘
```

### Core Components

- **Graph Engine**: Handles graph-based knowledge representation and querying
- **Agent Engine**: Manages agent lifecycle, tool calling, and decision making
- **Workflow Orchestrator**: Coordinates complex multi-step workflows
- **Memory / State**: Persistent storage for agent state and conversation history
- **Connectors**: Integration layer for external APIs and data sources
- **CLI / SDK**: Developer tools and programmatic interfaces

## Roadmap

### Near-term (MVP - v0.1.0)
- [x] Basic graph engine implementation
- [x] Simple agent framework
- [x] Core CLI tool
- [ ] REST API endpoints
- [ ] Basic documentation

### Mid-term (v0.2.0 - v0.5.0)
- [ ] Advanced workflow orchestration
- [ ] Plugin system for custom agents
- [ ] GraphQL API
- [ ] Performance optimizations
- [ ] Comprehensive test suite

### Long-term (v1.0.0+)
- [ ] Distributed agent deployment
- [ ] Multi-modal reasoning capabilities
- [ ] Enterprise integrations
- [ ] Advanced graph algorithms
- [ ] Community marketplace for agents

## Contributing

We welcome contributions from the community! Here's how you can get involved:

### Filing Issues
- Use GitHub Issues to report bugs or request features
- Provide detailed descriptions and code examples when possible
- Check existing issues to avoid duplicates

### Proposing New Modules/Tools
- Open a GitHub Discussion to discuss your idea
- Follow our module design guidelines (coming soon)
- Submit a pull request with your implementation

### Coding Standards
- Follow PEP 8 for Python code
- Write comprehensive tests for new features
- Update documentation for API changes
- Use type hints and docstrings

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

OpenGraph draws inspiration from:

- **LangChain** and **LlamaIndex** for agent frameworks
- **NetworkX** and **igraph** for graph algorithms
- **FastAPI** for API design patterns
- The broader AI and graph computing communities

Special thanks to our contributors and the open-source ecosystem that makes projects like this possible.