# 문서 생성 에이전트

A2A 프로토콜을 활용한 HTML/Markdown 문서 생성 및 다기능 질의응답 AI 에이전트입니다.

## 개요

이 프로젝트는 사용자의 다양한 요청에 실시간으로 응답하여 문서 생성, 웹 검색, 질의응답 서비스를 제공하는 AI 에이전트입니다. A2A 프로토콜과 MCP 서버를 활용하여 6가지 핵심 기능을 제공합니다.

## 주요 기능

### 6가지 핵심 스킬

1. **HTML 문서 생성** 
   - 사용자 요청에 따라 구조화된 HTML 문서 생성
   - 완전한 HTML5 구조와 CSS 스타일링 포함
   - 웹페이지, 보고서, 가이드 문서 등 다양한 형태 지원

2. **Markdown 문서 생성**
   - 깔끔하고 읽기 쉬운 마크다운 문서 생성
   - 기술 문서, 설명서, 블로그 포스트 최적화
   - 체계적인 구조와 풍부한 콘텐츠 제공

3. **URL 기반 질의응답**
   - 제공된 URL의 내용을 분석하여 질문에 답변
   - 웹사이트 내용 요약 및 정보 추출
   - MCP content-summarizer 서버 연동

4. **에이전트 정보 질의응답 (RAG)**
   - 에이전트 자체 기능과 능력에 대한 상세 답변
   - Milvus 벡터 데이터베이스를 통한 지식 검색
   - 사용자 질문에 맞춤형 정보 제공

5. **웹 검색**
   - 최신 정보 검색 및 트렌드 분석
   - 실시간 웹 검색 결과 정리 및 요약
   - MCP webresearch 서버 연동

6. **일반 질의응답**
   - 일상적인 질문과 대화에 자연스러운 응답
   - 인사, 간단한 질문, 대화형 상호작용 지원
   - 친근하고 전문적인 톤 유지

### 기술적 특징

- **A2A 프로토콜**: Google의 공식 A2A Python SDK 활용
- **MCP 서버 통합**: Model Context Protocol을 통한 외부 서비스 연동
- **LLM 기반**: OpenAI GPT 모델을 사용한 지능형 응답 생성
- **벡터 데이터베이스**: Milvus를 활용한 RAG 시스템 (선택적)
- **실시간 처리**: 빠른 응답을 위한 성능 최적화
- **스킬 기반 라우팅**: 질문 유형을 자동 분석하여 최적 기능으로 연결

## 시스템 아키텍처

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   호스트 에이전트  │───▶│ 문서생성 에이전트   │───▶│   MCP 서버들     │
│   (A2A SDK)     │    │   (A2A SDK)      │    │                │
└─────────────────┘    └──────────────────┘    │ • content-      │
                               │                │   summarizer    │
                               │                │ • webresearch   │
                               ▼                └─────────────────┘
                       ┌──────────────────┐
                       │   생성된 문서     │    ┌─────────────────┐
                       │   HTML/MD 파일   │───▶│  Milvus Vector  │
                       │   응답 데이터      │    │  Database (옵션) │
                       └──────────────────┘    └─────────────────┘
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

#### 스킬별 사용 예시

1. **HTML 문서 생성**
   - "Python 기초 가이드를 HTML 문서로 만들어줘"
   - "양자 컴퓨팅에 대한 HTML 페이지 생성"

2. **Markdown 문서 생성**
   - "API 문서를 마크다운으로 작성해줘"
   - "React 튜토리얼을 md 파일로 생성"

3. **URL 기반 질의응답**
   - "https://example.com 이 사이트의 주요 내용은 무엇인가요?"
   - "다음 URL에서 중요한 정보를 요약해주세요: https://news.example.com"

4. **에이전트 정보 질의응답**
   - "당신이 가지고 있는 기능은 어떤 것들이 있나요?"
   - "너는 무엇을 할 수 있니?"

5. **웹 검색**
   - "2024년 AI 트렌드를 검색해줘"
   - "Python 최신 버전 정보를 찾아봐"

6. **일반 질의응답**
   - "안녕하세요"
   - "오늘 날씨는 어때?"

### MCP 서버 설정

`mcpserver.json` 파일에서 MCP 서버들을 설정합니다:

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

### 질의응답 스킬 응답 (URL QA, RAG QA, Web Search, General QA)

```text
"[웹 검색 결과]

🔍 검색어: Python 최신 버전
📊 검색 결과: 5개

[1] Python 3.12 Released
🔗 https://www.python.org/downloads/
📝 Python 3.12의 새로운 기능과 개선사항...

---
※ 최신 웹 검색 결과입니다. 더 자세한 정보는 해당 링크를 참조하세요."
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
│   ├── __main__.py              # 메인 애플리케이션
│   ├── agent_executor.py        # 에이전트 실행 로직
│   ├── skill_classifier.py      # 스킬 분류 시스템
│   ├── skill_handlers.py        # 개별 스킬 처리기
│   ├── document_generator.py    # 문서 생성 엔진
│   ├── rag_manager.py          # RAG 시스템 관리
│   ├── mcp_manager.py          # MCP 서버 관리
│   ├── prompts.py              # 중앙화된 프롬프트 관리
│   ├── models.py               # 데이터 모델
│   └── config.py               # 설정 관리
├── test/
│   ├── integration_test.py      # 통합 테스트
│   └── test_skill_classifier.py # 스킬 분류 테스트
├── .well-known/
│   └── agent-card.json          # A2A 에이전트 카드
├── output/                      # 생성된 문서 저장소
├── mcpserver.json              # MCP 서버 설정
├── pyproject.toml              # Python 프로젝트 설정
├── package.json                # Node.js 의존성
├── .env.example                # 환경 변수 템플릿
└── README.ko.md                # 한국어 문서 (이 파일)
```

### 테스트 실행

```bash
# 개발 의존성 설치
uv sync --dev

# 통합 테스트 실행
python test\integration_test.py

# 스킬 분류 테스트 실행
python -m pytest test\test_skill_classifier.py
```

### 성능 최적화

- **캐시 시스템**: 분류 결과 캐싱으로 응답 속도 향상
- **병렬 처리**: 초기화 작업의 동시 실행
- **타임아웃 설정**: 모든 API 호출에 적절한 타임아웃 적용
- **토큰 제한**: LLM 호출 시 최적화된 토큰 사용

### API 엔드포인트

- `GET /`: 상태 확인
- `GET /.well-known/agent.json`: 에이전트 정보 (예쁘게 포맷된 JSON)
- `POST /`: A2A 프로토콜 메시지 처리

## 통합 및 연동

이 에이전트는 다음 시스템들과 통합되어 동작합니다:

1. **웹 페이지 서버** - GitHub Pages 정적 웹사이트 (Public)
2. **프록시 서버** - FastAPI 기반 미들웨어 (Private)
3. **호스트 에이전트 서버** - A2A 프로토콜 에이전트 호스팅 서버 (Public)
4. **MCP 서버들** - Model Context Protocol 서버들 (Public)
5. **Milvus 벡터 DB** - RAG 시스템용 벡터 데이터베이스 (선택적)

## 문제 해결

### 일반적인 문제들

1. **타임아웃 오류**
   - OpenAI API 키 확인
   - 네트워크 연결 상태 확인
   - 타임아웃 설정 조정

2. **MCP 서버 연결 실패**
   - `mcpserver.json` 설정 확인
   - Node.js 의존성 설치 확인
   - 서버 경로 및 명령어 검증

3. **Milvus 연결 오류**
   - `VECTOR_DB_URL` 설정 확인
   - Milvus 서버 실행 상태 확인
   - 네트워크 접근 권한 확인

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

- **현재 버전**: 2.0.0
- **A2A SDK 버전**: 최신
- **지원 Python 버전**: 3.10+
- **마지막 업데이트**: 2024년 12월

---

*이 문서는 한국어 사용자를 위해 작성되었습니다. 영어 문서는 `README.md`를 참조하세요.*