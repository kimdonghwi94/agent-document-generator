# Advanced Document Generator Agent

A powerful AI agent that combines LLM capabilities with MCP (Model Context Protocol) tools for document generation and general Q&A. Built with A2A (Agent-to-Agent) Protocol for seamless integration.

## Features

### Core Capabilities
- **Document Generation**: Generate HTML and Markdown documents
- **Web Analysis**: Analyze web pages using MCP tools
- **Conversational AI**: General Q&A with conversation history
- **Smart Tool Selection**: AI automatically chooses between direct LLM processing or MCP tools

### Technical Features
- **A2A Protocol Integration**: Standard Agent-to-Agent communication
- **MCP Runner Architecture**: Scalable MCP server management
- **Streaming Responses**: Real-time response generation
- **Markdown Rendering**: Rich text formatting in web interface
- **Error Handling**: User-friendly error messages
- **Session Management**: Persistent conversation contexts

## Architecture

### Simple Agent Architecture
The system uses a streamlined architecture focused on efficient AI-driven tool selection:

- **DhAgent**: Main AI agent with Google Gemini integration
- **Single Decision System**: AI analyzes queries and decides tool usage in one step
- **MCPRunnerClient**: Direct client for MCP Runner server communication
- **Smart Tool Selection**: Intelligent routing between LLM processing and MCP tools

### MCP Integration
- **MCP Runner Server**: Centralized server managing multiple MCP tools
- **Dynamic Tool Discovery**: Automatic tool detection from MCP Runner
- **Session Management**: Efficient session handling for tool execution
- **Error-Free Execution**: Robust error handling with user-friendly messages

## Installation

### Prerequisites
- Python 3.9+
- Google API Key (for Gemini)
- MCP Runner Server (for tool execution)

### Setup
1. Clone the repository:
```bash
git clone https://github.com/your-repo/agent-document-generator.git
cd agent-document-generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Environment Variables
Create a `.env` file with the following variables:
```env
# Google Gemini API key (Required)
GOOGLE_API_KEY=your_google_gemini_api_key_here

# MCP Runner server URL (default: http://localhost:10000)
MCP_RUNNER_URL=http://localhost:10000

# Server configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

4. Configure MCP servers in `mcpserver.json`:
```json
{
  "mcpServers": {
    "your-mcp-server": {
      "command": "node",
      "args": ["path/to/your-mcp-server/index.js"],
      "env": {
        "API_KEY": "${YOUR_MCP_SERVER_API_KEY}"
      }
    }
  }
}
```

## Usage

### Running the Agent
```bash
python -m src
```

The agent will be available at `http://localhost:8000`

### API Endpoints
- `GET /`: Web interface for chat interaction
- `POST /chat`: Direct chat API endpoint
- `GET /.well-known/agent.json`: A2A agent card
- `GET /health`: Health check endpoint

### Configuration


#### MCP Configuration
Configure your MCP servers in `mcpserver.json`. The agent will automatically discover and register available tools.

## Features in Detail

### Intelligent Tool Selection
The agent uses Google Gemini AI to analyze user queries and automatically decide whether to:
- Use MCP tools for specialized tasks (web analysis, document processing, etc.)
- Process directly with LLM for general questions and conversations
- Combine both approaches when needed for complex queries

### Web Interface
- Clean, responsive design
- Real-time markdown rendering
- Conversation history
- Error handling with user-friendly messages

### A2A Protocol Compliance
- Standard agent card format
- Skill-based capability declaration
- Compatible with A2A ecosystem

## Development

### Project Structure
```
src/
├── agent/           # Agent implementations
│   ├── dh_agent.py  # Main AI agent
│   └── __init__.py
├── executor/        # A2A protocol executors
│   ├── dh_executor.py
│   └── __init__.py
├── mcp_client/      # MCP integration
│   ├── mcp_runner_client.py
│   └── __init__.py
├── prompts/         # AI prompts
│   ├── prompts.py
│   └── *.txt        # Prompt templates
├── config.py        # Configuration management
└── __main__.py      # Application entry point
```

### Key Components

#### DhAgent (`src/agent/dh_agent.py`)
- Main AI agent with Google Gemini 2.0 Flash integration
- Single-decision MCP tool execution
- Conversation history management
- Markdown response formatting and user-friendly error handling

#### MCPRunnerClient (`src/mcp_client/mcp_runner_client.py`)
- MCP server communication
- Tool discovery and execution
- Session management

#### Prompts (`src/prompts/`)
- Centralized prompt management
- MCP decision making prompts
- Response formatting templates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- Create an issue on GitHub for bugs and feature requests
- Check the documentation for configuration details
- Ensure MCP Runner server is properly configured and running

## Changelog

### v2.1.0
- Added intelligent MCP tool selection
- Improved markdown rendering in web interface
- Enhanced error handling with user-friendly messages
- Optimized API calls with single-decision architecture
- Added response text cleaning for better formatting
- Simplified configuration (removed unused dependencies)
- Cleaned up project structure