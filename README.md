# Advanced Document Generator Agent

An intelligent AI agent powered by ReAct architecture for document generation, web research, and conversational AI using A2A Protocol and MCP integration.

## Overview

This project is an advanced AI agent that leverages the ReAct (Reasoning and Acting) pattern to intelligently process user requests. It provides intelligent document generation, real-time web research, and conversational AI services through seamless integration with A2A protocol and MCP (Model Control Protocol) servers. The agent dynamically selects appropriate tools and combines multiple capabilities to deliver comprehensive responses.

## Key Features

### 🤖 ReAct Architecture
- **Reasoning and Acting**: The agent analyzes user requests and dynamically selects appropriate tools
- **Multi-step Processing**: Handles complex tasks through iterative thinking and tool execution
- **Context Awareness**: Maintains conversation history and builds upon previous interactions
- **Intelligent Tool Selection**: Automatically chooses optimal tools for each task

### 4 Core Skills

1. **📝 Document Generation** 
   - Generate structured HTML and Markdown documents based on user requests
   - Complete HTML5 structure with modern CSS styling
   - Support for various formats: web pages, technical documentation, reports, guides
   - Automatic file saving with timestamp-based naming

2. **🔍 Web Research & Summary**
   - Real-time web search through MCP webresearch server integration
   - URL content analysis and summarization via MCP content-summarizer
   - Intelligent fallback to direct OpenAI processing when MCP unavailable
   - Comprehensive information gathering and synthesis

3. **💬 Intelligent Q&A**
   - Context-aware conversational responses using ReAct pattern
   - RAG (Retrieval-Augmented Generation) system for agent knowledge
   - Natural language understanding for diverse query types
   - Maintains conversation flow and builds on previous context

4. **🔧 MCP Tool Integration**
   - Dynamic MCP server discovery and tool enumeration  
   - Automatic server health checking and capability validation
   - Seamless integration with external services and APIs
   - Fault-tolerant operation with graceful degradation

### 🔧 Technical Features

- **A2A Protocol**: Built on Google's official A2A Python SDK with streaming support and JSON-RPC communication
- **ReAct Pattern**: Implements Reasoning and Acting for intelligent multi-step decision making
- **MCP Integration**: Dynamic Model Control Protocol server discovery, health checking, and tool enumeration
- **LLM-Powered**: Advanced response generation using OpenAI GPT models with context-aware processing
- **Context Management**: Sophisticated conversation history preservation with structured ConversationContext models
- **Tool Result Preservation**: Complete tool execution results (4000+ chars) stored to prevent redundant operations
- **Fault Tolerance**: Graceful MCP server degradation with OpenAI fallback when external services unavailable
- **Performance Optimized**: Efficient processing with proper timeout handling, error recovery, and dynamic tool selection

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Host Agent    │───▶│ ReAct Agent      │───▶│   MCP Servers   │
│   (A2A SDK)     │    │ (Dynamic Tools)  │    │                 │
└─────────────────┘    └──────────────────┘    │ • content-      │
                               │                │   summarizer    │
                               │                │ • webresearch   │
                               ▼                │ • Custom Tools  │
                       ┌──────────────────┐    └─────────────────┘
                       │ ConversationCtx  │           │
                       │ Tool Results     │◄──────────┘
                       │ Generated Docs   │    ┌─────────────────┐
                       │ Response Data    │───▶│ OpenAI GPT-4    │
                       └──────────────────┘    │ (Fallback LLM)  │
                                               └─────────────────┘
```

## Installation and Setup

### System Requirements

- Python 3.10+
- Node.js (for MCP servers)
- UV package manager
- OpenAI API key

### Installation Process

1. **Clone Repository and Navigate**
```bash
git clone <repository-url>
cd agent-document-generator
```

2. **Install Python Dependencies**
```bash
uv sync
```

3. **Install Node.js Dependencies**
```bash
npm install
```

4. **Create Environment Configuration File**
```bash
cp .env.example .env
```

5. **Configure Environment Variables**
```env
# A2A Protocol Configuration
A2A_AGENT_ID=agent-document-generator
A2A_HOST_URL=http://localhost:8000
A2A_API_KEY=your-api-key-here

# LLM Configuration  
OPENAI_API_KEY=your-openai-api-key-here
MODEL_NAME=gpt-4-turbo-preview

# Server Configuration
HOST=0.0.0.0
PORT=8002
DEBUG=false

# Output Directory Configuration
OUTPUT_DIR=./output
DEFAULT_FORMAT=html

# Vector Database Configuration (Optional)
VECTOR_DB_URL=http://localhost:19530
VECTOR_DB_COLLECTION_NAME=agent_knowledge
```

## Usage

### Running the Agent

```bash
# Using UV
uv run python -m src.agent_document_generator

# Or using npm script
npm start
```

### A2A Protocol Communication

#### Message Formats

**JSON Format (Detailed Configuration)**:
```json
{
  "question": "Please generate an HTML document about quantum computing",
  "format": "html",
  "context": {
    "topic": "quantum_computing",
    "level": "intermediate"
  },
  "metadata": {
    "author": "user",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

**Simple Text Format**:
```text
"What is machine learning?"
```

#### Usage Examples by Core Skills

1. **📝 Document Generation**
   - "Create an HTML document for a Python basics guide"
   - "Generate a comprehensive React tutorial in markdown"
   - "Write technical documentation about quantum computing"

2. **🔍 Web Research & Summary**
   - "Search for the latest AI developments in 2024"
   - "Summarize this article: https://example.com/ai-news"
   - "Find and analyze recent Python release information"

3. **💬 Intelligent Q&A**
   - "Explain your capabilities and available tools"
   - "Walk me through a complex multi-step analysis"
   - "What's the best approach for implementing ReAct pattern?"

4. **🔧 MCP Tool Integration**
   - "Use web research tools to find current tech trends"
   - "Analyze this URL content using MCP summarization"
   - "Demonstrate available MCP server capabilities"

### MCP Server Configuration

The system automatically discovers and integrates MCP servers configured in `mcpserver.json`:

```json
{
  "mcpServers": {
    "content-summarizer": {
      "command": "node",
      "args": ["path/to/mcp-summarizer/dist/index.js"],
      "description": "Text summarization using Gemini models"
    },
    "webresearch": {
      "command": "npx",
      "args": ["-y", "@mzxrai/mcp-webresearch@latest"],
      "description": "Real-time web search and content retrieval"
    }
  }
}
```

**Key Features:**
- **Dynamic Discovery**: Servers are automatically discovered and health-checked on startup
- **Graceful Degradation**: System continues to operate even if some MCP servers fail
- **Tool Enumeration**: Available tools are automatically discovered from running servers
- **Cross-Platform Support**: Enhanced Windows support with proper PATH resolution

## Response Formats

### Document Generation Skills Response (HTML/Markdown)

```json
{
  "text": "[HTML Document Generation Complete]\n\nTitle: Generated Document Title\nSaved to: ./output/file.html\nGenerated at: 2024-01-01T12:00:00Z",
  "part": {
    "root": {
      "file": {
        "bytes": "base64-encoded-content",
        "mime_type": "text/html",
        "name": "Document_Title.html"
      },
      "metadata": {
        "original_title": "Document Title",
        "generated_at": "2024-01-01T12:00:00Z",
        "format": "html"
      }
    }
  },
  "response": {
    "content": "Complete content of generated document",
    "format": "html",
    "title": "Document Title",
    "file_path": "./output/file.html",
    "metadata": {
      "generated_at": "2024-01-01T12:00:00Z",
      "model": "gpt-4-turbo-preview"
    }
  }
}
```

### ReAct Pattern Response (Intelligent Q&A)

```text
"[ReAct Agent Analysis]

🤔 Reasoning: User is asking about Python version updates. I need to search for the latest information.

🔧 Action: Using web research MCP tool to find current Python releases...

🔍 Search Results: Latest Python Version
📊 Found: 5 relevant sources

[1] Python 3.12 Released - December 2024
🔗 https://www.python.org/downloads/
📝 Key features: improved error messages, performance optimizations...

💡 Analysis: Based on the search results, Python 3.12 is the latest stable release with significant improvements in performance and developer experience.

---
※ Response generated using ReAct pattern with real-time web research."
```

## Output Files

Generated documents are saved in the `./output` directory with the following naming convention:

```
YYYYMMDD_HHMMSS_Document_Title.html
YYYYMMDD_HHMMSS_Document_Title.md
```

Examples:
- `20240101_120000_Python_Guide.html`
- `20240101_120000_API_Documentation.md`

## Development Information

### Project Structure

```
agent-document-generator/
├── src/agent_document_generator/
│   ├── __init__.py
│   ├── __main__.py              # A2A server & agent skills
│   ├── agent_executor.py        # Agent execution orchestration
│   ├── agent.py                 # ReAct pattern implementation
│   ├── mcp_manager.py          # MCP server integration & management
│   ├── config.py               # Configuration & environment setup
│   └── models.py               # Pydantic data models
├── test/
│   ├── test_react_agent.py     # ReAct agent functionality tests
│   ├── test_models.py          # Data model validation tests
│   ├── test_a2a_protocol.py    # A2A protocol integration tests
│   └── test_mcp_integration.py # MCP server integration tests
├── .well-known/
│   └── agent-card.json          # A2A agent card specification
├── output/                      # Generated document storage
├── mcpserver.json              # MCP server configuration (immutable)
├── pyproject.toml              # Python dependencies & project config
├── package.json                # Node.js MCP server dependencies
├── .env.example                # Environment variable template
└── README.md                   # This documentation
```

### Running Tests

```bash
# Install development dependencies
uv sync --dev

# Run ReAct agent tests
python test\test_react_agent.py

# Run A2A protocol integration tests
python test\test_a2a_protocol.py

# Run MCP integration tests
python test\test_mcp_integration.py

# Run all tests with pytest
python -m pytest test/
```

### Performance Optimization

- **Server Startup**: MCP servers and agent initialized once at application startup
- **Tool Result Preservation**: Complete execution results (4000+ chars) cached to prevent redundant operations
- **Dynamic MCP Discovery**: Automatic server health checking and graceful degradation
- **Context Management**: Structured conversation history with efficient processing
- **Timeout Handling**: Appropriate timeouts and error recovery for all external services

### API Endpoints

- `GET /`: Redirects to developer homepage
- `GET /health`: Health check endpoint
- `GET /.well-known/agent.json`: A2A agent card specification (prettified JSON)
- `POST /`: A2A protocol message processing with ReAct pattern execution

## Integration and Connectivity

This agent operates in integration with the following systems:

1. **Web Page Server** - GitHub Pages static website (Public)
2. **Proxy Server** - FastAPI-based middleware (Private)
3. **Host Agent Server** - A2A protocol agent hosting server (Public)
4. **MCP Servers** - Model Context Protocol servers (Public)
5. **Milvus Vector DB** - Vector database for RAG system (Optional)

## Troubleshooting

### Common Issues

1. **MCP Server Startup Failures**
   - Ensure Node.js and npm/npx are installed and in PATH
   - Check `mcpserver.json` configuration paths and commands
   - Verify MCP server packages are installed: `npm install -g @mzxrai/mcp-webresearch`

2. **OpenAI API Errors**
   - Verify `OPENAI_API_KEY` in environment variables
   - Check API quota and billing status
   - Ensure network connectivity to OpenAI services

3. **Agent Startup Issues**
   - Check application logs during startup
   - Ensure all Python dependencies installed: `uv sync`
   - Verify port 8004 is available

### Log Checking

```bash
# Run with detailed logging
DEBUG=true uv run python -m src.agent_document_generator
```

## License

MIT License

## Version Information

- **Current Version**: 2.1.0
- **A2A SDK Version**: Latest 
- **ReAct Pattern**: Fully implemented with tool integration
- **MCP Protocol**: 2024-11-05 specification
- **Supported Python Version**: 3.10+
- **Last Updated**: January 2025

---

*For Korean documentation, please refer to `README.ko.md`.*