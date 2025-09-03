# 고급 문서 생성 에이전트

ReAct 아키텍처 기반의 지능형 AI 에이전트로 문서 생성, 웹 리서치, 대화형 AI를 A2A 프로토콜과 MCP 통합으로 제공합니다.

## 개요

이 프로젝트는 ReAct (Reasoning and Acting) 패턴을 활용하여 사용자 요청을 지능적으로 처리하는 고급 AI 에이전트입니다. A2A 프로토콜과 MCP(Model Control Protocol) 서버들의 완전한 통합을 통해 지능적인 문서 생성, 실시간 웹 리서치, 대화형 AI 서비스를 제공합니다. 에이전트는 적절한 도구를 동적으로 선택하고 여러 기능을 결합하여 포괄적인 응답을 제공합니다.

## 주요 기능

### 🤖 ReAct 아키텍처
- **추론과 행동**: 에이전트가 사용자 요청을 분석하고 적절한 도구를 동적으로 선택
- **다단계 처리**: 복잡한 작업을 반복적 사고와 도구 실행을 통해 처리
- **맥락 인식**: 대화 기록을 유지하고 이전 상호작용을 바탕으로 구축
- **지능적 도구 선택**: 각 작업에 최적화된 도구를 자동으로 선택

### 4가지 핵심 스킬

1. **📝 문서 생성** 
   - 사용자 요청에 따른 구조화된 HTML 및 Markdown 문서 생성
   - 완전한 HTML5 구조와 모던 CSS 스타일링
   - 다양한 형식 지원: 웹페이지, 기술 문서, 보고서, 가이드
   - 타임스탬프 기반 자동 파일명 지정 및 저장

2. **🔍 웹 리서치 & 요약**
   - MCP webresearch 서버 통합을 통한 실시간 웹 검색
   - MCP content-summarizer를 통한 URL 콘텐츠 분석 및 요약
   - MCP가 불가능할 때 OpenAI 직접 처리로의 지능적 폴백
   - 포괄적인 정보 수집 및 종합

3. **💬 지능적 Q&A**
   - ReAct 패턴을 활용한 맥락 인식 대화형 응답
   - 에이전트 지식을 위한 RAG(검색 증강 생성) 시스템
   - 다양한 질의 유형을 위한 자연어 이해
   - 대화 흐름 유지 및 이전 맥락 기반 구축

4. **🔧 MCP 도구 통합**
   - 동적 MCP 서버 발견 및 도구 열거  
   - 자동 서버 상태 확인 및 기능 검증
   - 외부 서비스 및 API와의 완전한 통합
   - 우아한 성능 저하를 통한 내결함성 운영

### 🔧 기술적 특징

- **A2A 프로토콜**: 스트리밍 지원과 JSON-RPC 통신을 갖춘 Google 공식 A2A Python SDK 기반
- **ReAct 패턴**: 지능적인 다단계 의사결정을 위한 추론과 행동 구현
- **MCP 통합**: 동적 Model Control Protocol 서버 발견, 상태 확인, 도구 열거
- **LLM 기반**: 맥락 인식 처리를 갖춘 OpenAI GPT 모델을 사용한 고급 응답 생성
- **맥락 관리**: 구조화된 ConversationContext 모델을 활용한 정교한 대화 기록 보존
- **도구 결과 보존**: 중복 작업 방지를 위한 완전한 도구 실행 결과(4000+ 문자) 저장
- **내결함성**: 외부 서비스 불가능 시 OpenAI 폴백을 갖춘 우아한 MCP 서버 성능 저하
- **성능 최적화**: 적절한 타임아웃 처리, 오류 복구, 동적 도구 선택을 갖춘 효율적 처리

## 시스템 아키텍처

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   호스트 에이전트  │───▶│  ReAct 에이전트   │───▶│   MCP 서버들     │
│   (A2A SDK)     │    │ (동적 도구 활용)   │    │                │
└─────────────────┘    └──────────────────┘    │ • content-      │
                               │                │   summarizer    │
                               │                │ • webresearch   │
                               ▼                │ • 커스텀 도구    │
                       ┌──────────────────┐    └─────────────────┘
                       │ ConversationCtx  │           │
                       │ 도구 결과 저장    │◄──────────┘
                       │ 생성된 문서       │    ┌─────────────────┐
                       │ 응답 데이터       │───▶│ OpenAI GPT-4    │
                       └──────────────────┘    │ (폴백 LLM)       │
                                               └─────────────────┘
```

## 설치 및 설정

### 시스템 요구사항

- Python 3.10 이상
- Node.js (MCP 서버용)
- UV 패키지 매니저
- OpenAI API 키

### 설치 과정

1. **저장소 복제 및 디렉터리 이동**
```bash
git clone <repository-url>
cd agent-document-generator
```

2. **Python 의존성 설치**
```bash
uv sync
```

3. **Node.js 의존성 설치**
```bash
npm install
```

4. **환경 설정 파일 생성**
```bash
cp .env.example .env
```

5. **환경 변수 설정**
```env
# A2A 프로토콜 설정
A2A_AGENT_ID=agent-document-generator
A2A_HOST_URL=http://localhost:8000
A2A_API_KEY=your-api-key-here

# LLM 설정  
OPENAI_API_KEY=your-openai-api-key-here
MODEL_NAME=gpt-4-turbo-preview

# 서버 설정
HOST=0.0.0.0
PORT=8002
DEBUG=false

# 출력 디렉터리 설정
OUTPUT_DIR=./output
DEFAULT_FORMAT=html

# 벡터 데이터베이스 설정 (선택적)
VECTOR_DB_URL=http://localhost:19530
VECTOR_DB_COLLECTION_NAME=agent_knowledge
```

## 사용 방법

### 에이전트 실행

```bash
# UV를 사용한 실행
uv run python -m src.agent_document_generator

# 또는 npm 스크립트 사용
npm start
```

### A2A 프로토콜 통신

#### 메시지 형식

**JSON 형식 (상세 설정)**:
```json
{
  "question": "양자 컴퓨팅에 대한 HTML 문서를 생성해주세요",
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

**단순 텍스트 형식**:
```text
"머신러닝이란 무엇인가요?"
```

#### 핵심 스킬별 사용 예시

1. **📝 문서 생성**
   - "Python 기초 가이드를 HTML 문서로 만들어줘"
   - "포괄적인 React 튜토리얼을 마크다운으로 생성해줘"
   - "양자 컴퓨팅에 대한 기술 문서를 작성해줘"

2. **🔍 웹 리서치 & 요약**
   - "2024년 최신 AI 개발 동향을 검색해줘"
   - "이 기사를 요약해줘: https://example.com/ai-news"
   - "최근 Python 릴리즈 정보를 찾아서 분석해줘"

3. **💬 지능적 Q&A**
   - "당신의 기능과 사용 가능한 도구들을 설명해줘"
   - "복잡한 다단계 분석을 단계별로 진행해줘"
   - "ReAct 패턴 구현에 가장 좋은 접근법은 무엇인가요?"

4. **🔧 MCP 도구 통합**
   - "웹 리서치 도구를 사용해서 현재 기술 트렌드를 찾아줘"
   - "MCP 요약 서비스를 통해 이 URL 내용을 분석해줘"
   - "사용 가능한 MCP 서버 기능들을 보여줘"

### MCP 서버 설정

시스템이 `mcpserver.json`에 설정된 MCP 서버들을 자동으로 발견하고 통합합니다:

```json
{
  "mcpServers": {
    "content-summarizer": {
      "command": "node",
      "args": ["path/to/mcp-summarizer/dist/index.js"],
      "description": "Gemini 모델을 사용한 텍스트 요약"
    },
    "webresearch": {
      "command": "npx",
      "args": ["-y", "@mzxrai/mcp-webresearch@latest"],
      "description": "실시간 웹 검색 및 콘텐츠 검색"
    }
  }
}
```

**주요 특징:**
- **동적 발견**: 서버들이 시작 시 자동으로 발견되고 상태 확인됨
- **우아한 성능 저하**: 일부 MCP 서버가 실패해도 시스템이 계속 작동
- **도구 열거**: 실행 중인 서버에서 사용 가능한 도구가 자동으로 발견됨
- **크로스 플랫폼 지원**: 적절한 PATH 해결을 통한 향상된 Windows 지원

## 응답 형식

### 문서 생성 스킬 응답 (HTML/Markdown)

```json
{
  "text": "[HTML 문서 생성 완료]\n\n제목: 생성된 문서 제목\n저장 위치: ./output/file.html\n생성 시간: 2024-01-01T12:00:00Z",
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
    "content": "생성된 문서의 전체 내용",
    "format": "html",
    "title": "문서 제목",
    "file_path": "./output/file.html",
    "metadata": {
      "generated_at": "2024-01-01T12:00:00Z",
      "model": "gpt-4-turbo-preview"
    }
  }
}
```

### ReAct 패턴 응답 (지능적 Q&A)

```text
"[ReAct 에이전트 분석]

🤔 추론: 사용자가 Python 버전 업데이트에 대해 질문하고 있습니다. 최신 정보를 검색해야 합니다.

🔧 행동: 웹 리서치 MCP 도구를 사용하여 현재 Python 릴리스를 찾는 중...

🔍 검색 결과: Python 최신 버전
📊 발견: 5개의 관련 소스

[1] Python 3.12 Released - 2024년 12월
🔗 https://www.python.org/downloads/
📝 주요 기능: 개선된 오류 메시지, 성능 최적화...

💡 분석: 검색 결과에 따르면, Python 3.12가 성능과 개발자 경험의 상당한 개선을 제공하는 최신 안정 릴리스입니다.

---
※ 실시간 웹 리서치와 함께 ReAct 패턴을 사용하여 생성된 응답입니다."
```

## 출력 파일

생성된 문서는 `./output` 디렉터리에 다음 명명 규칙으로 저장됩니다:

```
YYYYMMDD_HHMMSS_Document_Title.html
YYYYMMDD_HHMMSS_Document_Title.md
```

예시:
- `20240101_120000_Python_Guide.html`
- `20240101_120000_API_Documentation.md`

## 개발 정보

### 프로젝트 구조

```
agent-document-generator/
├── src/agent_document_generator/
│   ├── __init__.py
│   ├── __main__.py              # A2A 서버 & 에이전트 스킬
│   ├── agent_executor.py        # 에이전트 실행 오케스트레이션
│   ├── agent.py                 # ReAct 패턴 구현
│   ├── mcp_manager.py          # MCP 서버 통합 & 관리
│   ├── config.py               # 설정 & 환경 설정
│   └── models.py               # Pydantic 데이터 모델
├── test/
│   ├── test_react_agent.py     # ReAct 에이전트 기능 테스트
│   ├── test_models.py          # 데이터 모델 검증 테스트
│   ├── test_a2a_protocol.py    # A2A 프로토콜 통합 테스트
│   └── test_mcp_integration.py # MCP 서버 통합 테스트
├── .well-known/
│   └── agent-card.json          # A2A 에이전트 카드 사양
├── output/                      # 생성된 문서 저장소
├── mcpserver.json              # MCP 서버 설정 (불변)
├── pyproject.toml              # Python 의존성 & 프로젝트 설정
├── package.json                # Node.js MCP 서버 의존성
├── .env.example                # 환경 변수 템플릿
└── README.ko.md                # 이 문서
```

### 테스트 실행

```bash
# 개발 의존성 설치
uv sync --dev

# ReAct 에이전트 테스트 실행
python test\test_react_agent.py

# A2A 프로토콜 통합 테스트 실행
python test\test_a2a_protocol.py

# MCP 통합 테스트 실행
python test\test_mcp_integration.py

# pytest로 모든 테스트 실행
python -m pytest test/
```

### 성능 최적화

- **서버 시작**: MCP 서버와 에이전트가 애플리케이션 시작 시 한 번 초기화
- **도구 결과 보존**: 중복 작업 방지를 위해 완전한 실행 결과(4000+ 문자) 캐시
- **동적 MCP 발견**: 자동 서버 상태 확인 및 우아한 성능 저하
- **맥락 관리**: 효율적인 처리를 갖춴 구조화된 대화 기록
- **타임아웃 처리**: 모든 외부 서비스에 대한 적절한 타임아웃 및 오류 복구

### API 엔드포인트

- `GET /`: 개발자 홈페이지로 리다이렉트
- `GET /health`: 상태 확인 엔드포인트
- `GET /.well-known/agent.json`: A2A 에이전트 카드 사양 (예쁘게 포맷된 JSON)
- `POST /`: ReAct 패턴 실행을 통한 A2A 프로토콜 메시지 처리

## 통합 및 연동

이 에이전트는 다음 시스템들과 통합되어 동작합니다:

1. **웹 페이지 서버** - GitHub Pages 정적 웹사이트 (Public)
2. **프록시 서버** - FastAPI 기반 미들웨어 (Private)
3. **호스트 에이전트 서버** - A2A 프로토콜 에이전트 호스팅 서버 (Public)
4. **MCP 서버들** - Model Context Protocol 서버들 (Public)
5. **Milvus 벡터 DB** - RAG 시스템용 벡터 데이터베이스 (선택적)

## 문제 해결

### 일반적인 문제들

1. **MCP 서버 시작 실패**
   - Node.js와 npm/npx가 설치되고 PATH에 있는지 확인
   - `mcpserver.json` 설정 경로 및 명령어 확인
   - MCP 서버 패키지 설치 확인: `npm install -g @mzxrai/mcp-webresearch`

2. **OpenAI API 오류**
   - 환경 변수에서 `OPENAI_API_KEY` 확인
   - API 할당량 및 빌링 상태 확인
   - OpenAI 서비스에 대한 네트워크 연결 보장

3. **에이전트 시작 문제**
   - 시작 중 애플리케이션 로그 확인
   - 모든 Python 의존성 설치 확인: `uv sync`
   - 포트 8004가 사용 가능한지 확인

### 로그 확인

```bash
# 상세 로깅으로 실행
DEBUG=true uv run python -m src.agent_document_generator
```

## 라이선스

MIT License

## 기여하기

1. 저장소 포크
2. 기능 브랜치 생성
3. 변경사항 구현
4. 테스트 추가 (필요시)
5. Pull Request 제출

## 지원

문제나 질문이 있으시면 GitHub 저장소에 이슈를 생성해 주세요.

## 버전 정보

- **현재 버전**: 2.1.0
- **A2A SDK 버전**: 최신 
- **ReAct 패턴**: 도구 통합과 함께 완전 구현
- **MCP 프로토콜**: 2024-11-05 사양
- **지원 Python 버전**: 3.10+
- **마지막 업데이트**: 2025년 1월

---

*이 문서는 한국어 사용자를 위해 작성되었습니다. 영어 문서는 `README.md`를 참조하세요.*