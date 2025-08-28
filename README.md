# Document Generator Agent

A2A Protocol Sub Agent Server for generating HTML/Markdown documents from user queries using LLM and MCP servers.

## Overview

이 프로젝트는 사용자가 질문하면 에이전트가 실시간 응답하고, HTML·Markdown 페이지를 자동 생성해 정보를 제공하는 마이크로서비스 아키텍처 시스템의 일부입니다. 이 특정 에이전트(3.1 Sub Agent Server)는 A2A SDK를 사용하여 실제 문서 생성을 담당합니다.

## Features

- **A2A SDK 기반**: Google의 공식 A2A Python SDK 사용
- **MCP 서버 통합**: 문서 처리를 위한 다중 MCP 서버 사용:
  - `mcp-pandoc`: 문서 변환 및 생성
  - `mcp-filesystem`: 파일 시스템 작업
  - `markdownify`: HTML을 Markdown으로 변환
- **LLM 기반 생성**: OpenAI GPT 모델을 사용한 포괄적인 문서 생성
- **다중 출력 형식**: HTML 및 Markdown 출력 형식 지원
- **자동 파일 저장**: 생성된 문서는 타임스탬프와 함께 자동 저장

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Host Agent    │───▶│ Document Gen     │───▶│   MCP Servers   │
│   (A2A SDK)     │    │ Agent (A2A SDK)  │    │   (pandoc, fs)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌──────────────────┐
                       │   Generated      │
                       │   Documents      │
                       │   (HTML/MD)      │
                       └──────────────────┘
```

## Installation

### Prerequisites

- Python 3.10+
- Node.js (markdownify MCP 서버용)
- UV package manager
- OpenAI API key

### Setup

1. **프로젝트 클론 및 이동**:
```bash
git clone <repository-url>
cd agent-document-generator
```

2. **Python 의존성 설치**:
```bash
uv sync
```

3. **MCP 서버용 Node.js 의존성 설치**:
```bash
npm install
```

4. **환경 설정**:
```bash
cp .env.example .env
# .env 파일을 편집하여 설정
```

5. **필수 환경 변수**:
```env
# A2A Protocol 설정
A2A_AGENT_ID=agent-document-generator
A2A_HOST_URL=http://localhost:8000
A2A_API_KEY=your-api-key-here

# LLM 설정  
OPENAI_API_KEY=your-openai-api-key
MODEL_NAME=gpt-4-turbo-preview

# 서버 설정
HOST=0.0.0.0
PORT=8001
```

## Usage

### 에이전트 시작

```bash
# UV 사용
uv run python -m src.agent_document_generator

# 또는 npm script 사용
npm run start
```

### A2A 통신

이 에이전트는 A2A SDK를 사용하여 통신합니다:

#### 메시지 형식

**JSON 형식 (상세 설정)**:
```json
{
  "question": "양자 컴퓨팅에 대해 설명해주세요",
  "format": "html",
  "context": {},
  "metadata": {}
}
```

**단순 텍스트**:
```
"머신러닝이란 무엇인가요?"
```

#### 테스트 클라이언트

```bash
# 테스트 클라이언트 실행
uv run python test_client.py

# 또는
npm run test
```

## MCP 서버 설정

에이전트는 `mcpserver.json`에서 설정된 여러 MCP 서버를 사용합니다:

```json
{
  "mcpServers": {
    "mcp-pandoc": {
      "command": "uvx",
      "args": ["mcp-pandoc"],
      "description": "문서 변환 및 생성"
    },
    "mcp-filesystem": {
      "command": "uvx", 
      "args": ["mcp-filesystem", "--directory", "./output"],
      "description": "파일 시스템 접근"
    },
    "markdownify": {
      "command": "node",
      "args": ["./node_modules/markdownify-mcp/dist/index.js"],
      "description": "HTML을 Markdown으로 변환"
    }
  }
}
```

## A2A 메시지 처리

### 지원하는 기능

1. **HTML 문서 생성**: 질문을 기반으로 HTML 문서 생성
2. **Markdown 문서 생성**: 질문을 기반으로 Markdown 문서 생성  
3. **자동 파일 저장**: 생성된 문서를 타임스탬프와 함께 저장

### 응답 예시

```json
{
  "status": "success",
  "content": "<html>...</html>",
  "format": "html",
  "title": "Generated Document",
  "file_path": "./output/20240101_120000_Generated_Document.html",
  "metadata": {
    "generated_at": "2024-01-01T12:00:00Z",
    "model": "gpt-4-turbo-preview"
  }
}
```

## Output

Generated documents are saved in the `./output` directory with the following naming pattern:
```
YYYYMMDD_HHMMSS_Document_Title.html
YYYYMMDD_HHMMSS_Document_Title.md
```

## Development

### Project Structure

```
agent-document-generator/
├── src/agent_document_generator/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── config.py            # Configuration management
│   ├── document_generator.py # Core document generation
│   ├── mcp_manager.py       # MCP server management
│   └── a2a_protocol.py      # A2A protocol handler
├── mcpserver.json           # MCP server configuration
├── .well-known/
│   └── agent-card.json      # Agent card for A2A discovery
├── output/                  # Generated documents
├── pyproject.toml           # Python project configuration
├── package.json             # Node.js dependencies
├── .env.example             # Environment template
└── README.md
```

### Running Tests

```bash
# Install test dependencies
uv sync --dev

# Run tests
uv run pytest
```

## Integration

This agent is designed to work with:

1. **Web Page Server** - GitHub Pages static website (Public)
2. **Proxy Server** - FastAPI-based middleware (Private)
3. **Host Agent Server** - Agent hosting server with A2A Protocol (Public)
4. **MCP Server** - Model Context Protocol server (Public)

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions, please create an issue in the GitHub repository.