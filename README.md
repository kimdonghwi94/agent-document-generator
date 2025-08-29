# Document Generator Agent

An AI agent for HTML/Markdown document generation and multi-functional Q&A using A2A Protocol.

## Overview

This project is an AI agent that provides real-time responses to various user requests, offering document generation, web search, and Q&A services. It leverages the A2A protocol and MCP servers to provide 6 core functionalities.

## Key Features

### 6 Core Skills

1. **HTML Document Generation** 
   - Generate structured HTML documents based on user requests
   - Complete HTML5 structure with CSS styling included
   - Support for various formats: web pages, reports, guide documents

2. **Markdown Document Generation**
   - Generate clean and readable markdown documents
   - Optimized for technical documentation, manuals, and blog posts
   - Systematic structure with rich content

3. **URL-based Q&A**
   - Analyze provided URL content to answer questions
   - Website content summarization and information extraction
   - Integration with MCP content-summarizer server

4. **Agent Information Q&A (RAG)**
   - Detailed answers about the agent's own functions and capabilities
   - Knowledge search through Milvus vector database
   - Customized information provision based on user questions

5. **Web Search**
   - Latest information search and trend analysis
   - Real-time web search result organization and summarization
   - Integration with MCP webresearch server

6. **General Q&A**
   - Natural responses to everyday questions and conversations
   - Support for greetings, simple questions, and interactive conversations
   - Maintain friendly and professional tone

### Technical Features

- **A2A Protocol**: Utilizes Google's official A2A Python SDK
- **MCP Server Integration**: External service integration through Model Context Protocol
- **LLM-based**: Intelligent response generation using OpenAI GPT models
- **Vector Database**: RAG system using Milvus (optional)
- **Real-time Processing**: Performance optimization for fast responses
- **Skill-based Routing**: Automatic analysis of question types for optimal function routing

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Host Agent    │───▶│ Document Gen     │───▶│   MCP Servers   │
│   (A2A SDK)     │    │   Agent (A2A)    │    │                 │
└─────────────────┘    └──────────────────┘    │ • content-      │
                               │                │   summarizer    │
                               │                │ • webresearch   │
                               ▼                └─────────────────┘
                       ┌──────────────────┐
                       │  Generated Docs  │    ┌─────────────────┐
                       │  HTML/MD Files   │───▶│  Milvus Vector  │
                       │  Response Data   │    │ Database (Opt.) │
                       └──────────────────┘    └─────────────────┘
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

#### Usage Examples by Skill

1. **HTML Document Generation**
   - "Create an HTML document for a Python basics guide"
   - "Generate an HTML page about quantum computing"

2. **Markdown Document Generation**
   - "Write API documentation in markdown format"
   - "Generate a React tutorial as an md file"

3. **URL-based Q&A**
   - "What is the main content of this site: https://example.com?"
   - "Please summarize important information from this URL: https://news.example.com"

4. **Agent Information Q&A**
   - "What features do you have available?"
   - "What can you do?"

5. **Web Search**
   - "Search for AI trends in 2024"
   - "Find information about the latest Python version"

6. **General Q&A**
   - "Hello"
   - "How's the weather today?"

### MCP Server Configuration

Configure MCP servers in the `mcpserver.json` file:

```json
{
  "mcpServers": {
    "content-summarizer": {
      "command": "node",
      "args": [
        "C:/Users/donghwi/PycharmProjects/mcp-summarizer/dist/index.js"
      ]
    },
    "webresearch": {
      "command": "npx",
      "args": ["-y", "@mzxrai/mcp-webresearch@latest"]
    }
  }
}
```

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

### Q&A Skills Response (URL QA, RAG QA, Web Search, General QA)

```text
"[Web Search Results]

🔍 Search Query: Latest Python Version
📊 Search Results: 5 items

[1] Python 3.12 Released
🔗 https://www.python.org/downloads/
📝 New features and improvements in Python 3.12...

---
※ These are the latest web search results. Please refer to the links for more detailed information."
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
│   ├── __main__.py              # Main application
│   ├── agent_executor.py        # Agent execution logic
│   ├── skill_classifier.py      # Skill classification system
│   ├── skill_handlers.py        # Individual skill handlers
│   ├── document_generator.py    # Document generation engine
│   ├── rag_manager.py          # RAG system management
│   ├── mcp_manager.py          # MCP server management
│   ├── prompts.py              # Centralized prompt management
│   ├── models.py               # Data models
│   └── config.py               # Configuration management
├── test/
│   ├── integration_test.py      # Integration tests
│   └── test_skill_classifier.py # Skill classification tests
├── .well-known/
│   └── agent-card.json          # A2A agent card
├── output/                      # Generated document storage
├── mcpserver.json              # MCP server configuration
├── pyproject.toml              # Python project configuration
├── package.json                # Node.js dependencies
├── .env.example                # Environment variable template
└── README.md                   # This file
```

### Running Tests

```bash
# Install development dependencies
uv sync --dev

# Run integration tests
python test\integration_test.py

# Run skill classification tests
python -m pytest test\test_skill_classifier.py
```

### Performance Optimization

- **Cache System**: Improved response speed through classification result caching
- **Parallel Processing**: Concurrent execution of initialization tasks
- **Timeout Settings**: Appropriate timeouts applied to all API calls
- **Token Limits**: Optimized token usage for LLM calls

### API Endpoints

- `GET /`: Status check
- `GET /.well-known/agent.json`: Agent information (prettified JSON)
- `POST /`: A2A protocol message processing

## Integration and Connectivity

This agent operates in integration with the following systems:

1. **Web Page Server** - GitHub Pages static website (Public)
2. **Proxy Server** - FastAPI-based middleware (Private)
3. **Host Agent Server** - A2A protocol agent hosting server (Public)
4. **MCP Servers** - Model Context Protocol servers (Public)
5. **Milvus Vector DB** - Vector database for RAG system (Optional)

## Troubleshooting

### Common Issues

1. **Timeout Errors**
   - Check OpenAI API key
   - Verify network connection status
   - Adjust timeout settings

2. **MCP Server Connection Failures**
   - Check `mcpserver.json` configuration
   - Verify Node.js dependency installation
   - Validate server paths and commands

3. **Milvus Connection Errors**
   - Check `VECTOR_DB_URL` configuration
   - Verify Milvus server running status
   - Check network access permissions

### Log Checking

```bash
# Run with detailed logging
DEBUG=true uv run python -m src.agent_document_generator
```

## License

MIT License

## Version Information

- **Current Version**: 2.0.0
- **A2A SDK Version**: Latest
- **Supported Python Version**: 3.10+
- **Last Updated**: December 2024

---

*For Korean documentation, please refer to `README.ko.md`.*