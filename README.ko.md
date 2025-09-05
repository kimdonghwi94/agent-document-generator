# 고급 문서 생성 에이전트

MCP(Model Context Protocol) 도구와 LLM을 결합한 강력한 AI 에이전트로 문서 생성 및 일반 Q&A를 수행합니다. A2A(Agent-to-Agent) 프로토콜을 사용하여 완벽한 통합을 제공합니다.

## 개요

이 프로젝트는 Google Gemini AI와 MCP Runner 서버를 통합한 효율적인 문서 생성 에이전트입니다. A2A 프로토콜 기반으로 구축되어 지능적인 문서 생성, 웹 분석, 대화형 AI 서비스를 제공합니다. 에이전트는 단일 결정 시스템을 통해 사용자 요청을 분석하고 적절한 도구를 효율적으로 선택합니다.

## 주요 기능

### 🤖 단순하고 효율적인 아키텍처
- **단일 결정 시스템**: AI가 쿼리를 분석해서 도구 사용 여부와 실행 계획을 한 번에 결정
- **Google Gemini 통합**: Google Gemini 2.0 Flash 모델을 사용한 고품질 응답 생성
- **맥락 인식**: 대화 기록 유지 및 이전 상호작용 기반 응답
- **지능적 라우팅**: MCP 도구와 직접 LLM 처리 간의 스마트한 선택

### 핵심 기능

1. **📝 문서 생성** 
   - 사용자 요청에 따른 구조화된 HTML 및 Markdown 문서 생성
   - 완전한 HTML5 구조와 모던 CSS 스타일링
   - 다양한 형식 지원: 웹페이지, 기술 문서, 보고서, 가이드

2. **🔍 웹 분석**
   - MCP Runner 서버를 통한 웹 페이지 분석
   - URL 콘텐츠 분석 및 요약
   - 실시간 웹 데이터 처리

3. **💬 대화형 AI**
   - Google Gemini 기반 자연어 처리
   - 대화 기록 유지 및 맥락 인식
   - 마크다운 렌더링 지원

4. **🔧 MCP 통합**
   - MCP Runner 서버를 통한 다중 MCP 도구 지원
   - 동적 도구 발견 및 실행
   - 세션 기반 도구 관리
   - 사용자 친화적 오류 처리

### 🔧 기술적 특징

- **A2A 프로토콜**: A2A Python SDK 기반 에이전트 간 통신
- **Google Gemini 통합**: Gemini 2.0 Flash 모델을 사용한 고품질 AI 응답
- **MCP Runner 아키텍처**: 중앙집중식 MCP 서버 관리 시스템
- **단일 결정 시스템**: 효율적인 AI 기반 도구 선택 및 실행 계획
- **스트리밍 응답**: 실시간 응답 생성 및 전송
- **마크다운 렌더링**: 웹 인터페이스에서 풍부한 텍스트 포맷팅
- **사용자 친화적 오류 처리**: 기술적 오류를 사용자가 이해하기 쉬운 메시지로 변환
- **세션 관리**: 효율적인 MCP 도구 세션 관리

## 시스템 아키텍처

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  A2A 웹 서버     │───▶│   DH 에이전트     │───▶│  MCP Runner     │
│  (FastAPI)      │    │ (단일 결정 AI)    │    │  서버           │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │                         │
                               ▼                         ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Google Gemini   │    │   MCP 도구들     │
                       │  2.0 Flash       │    │ • web-analyzer  │
                       │                  │    │ • 기타 도구      │
                       └──────────────────┘    └─────────────────┘
```

## 설치 및 설정

### 시스템 요구사항

- Python 3.9 이상
- Google API 키 (Gemini용)
- MCP Runner 서버

### 설치 과정

1. **저장소 복제 및 디렉터리 이동**
```bash
git clone <repository-url>
cd agent-document-generator
```

2. **Python 의존성 설치**
```bash
pip install -r requirements.txt
```

3. **환경 변수 설정**
`.env` 파일을 생성하고 다음 변수를 설정하세요:
```env
# Google Gemini API 키 (필수)
GOOGLE_API_KEY=your_google_gemini_api_key_here

# MCP Runner 서버 URL (기본값: http://localhost:10000)
MCP_RUNNER_URL=http://localhost:10000

# 서버 설정
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

4. **MCP 서버 설정**
`mcpserver.json` 파일에서 MCP 서버들을 설정합니다:
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

## 사용 방법

### 에이전트 실행

```bash
python -m src
```

에이전트는 `http://localhost:8000`에서 실행됩니다.

### API 엔드포인트

- `GET /`: 웹 인터페이스 (채팅 UI)
- `POST /chat`: 직접 채팅 API 엔드포인트
- `GET /.well-known/agent.json`: A2A 에이전트 카드
- `GET /health`: 상태 확인 엔드포인트

### 핵심 스킬별 사용 예시

1. **📝 문서 생성**
   - "Python 기초 가이드를 HTML 문서로 만들어줘"
   - "포괄적인 React 튜토리얼을 마크다운으로 생성해줘"
   - "양자 컴퓨팅에 대한 기술 문서를 작성해줘"

2. **🔍 웹 분석**
   - "이 웹사이트를 분석해줘: https://example.com"
   - "이 기사를 요약해줘: https://example.com/news"
   - "웹페이지의 주요 내용을 분석해줘"

3. **💬 대화형 AI**
   - "당신의 기능과 사용 가능한 도구들을 설명해줘"
   - "복잡한 질문에 대해 단계별로 답변해줘"
   - "프로그래밍 관련 질문에 답해줘"

4. **🔧 MCP 도구 통합**
   - "웹 분석 도구를 사용해서 이 사이트를 분석해줘"
   - "MCP 도구를 통해 이 URL 내용을 분석해줘"
   - "사용 가능한 도구들을 보여줘"

### MCP 서버 설정

**주요 특징:**
- **MCP Runner 통합**: 중앙집중식 MCP 서버 관리
- **동적 도구 발견**: MCP Runner에서 사용 가능한 도구 자동 발견
- **세션 관리**: 효율적인 도구 실행 세션 관리
- **오류 처리**: 사용자 친화적 오류 메시지

## 응답 형식

### 일반 응답 형식

DH 에이전트는 마크다운 형식으로 응답을 제공하며, 웹 인터페이스에서 자동으로 HTML로 렌더링됩니다:

```markdown
# 제목

**굵은 글씨**로 강조된 내용과 함께 일반 텍스트가 표시됩니다.

## 섹션 제목

- 목록 아이템 1
- 목록 아이템 2

```code
코드 블록 예시
```

[링크 텍스트](https://example.com)
```

## 개발 정보

### 프로젝트 구조

```
src/
├── agent/           # AI 에이전트 구현
│   ├── dh_agent.py  # 메인 AI 에이전트
│   └── __init__.py
├── executor/        # A2A 프로토콜 실행자
│   ├── dh_executor.py
│   └── __init__.py
├── mcp_client/      # MCP 통합
│   ├── mcp_runner_client.py
│   └── __init__.py
├── prompts/         # AI 프롬프트
│   ├── prompts.py
│   └── *.txt        # 프롬프트 템플릿
├── config.py        # 설정 관리
└── __main__.py      # 애플리케이션 진입점
```

### 주요 컴포넌트

#### DhAgent (`src/agent/dh_agent.py`)
- Google Gemini 2.0 Flash 통합을 사용한 메인 AI 에이전트
- 단일 결정 MCP 도구 실행
- 대화 기록 관리
- 마크다운 응답 포맷팅 및 사용자 친화적 오류 처리

#### MCPRunnerClient (`src/mcp_client/mcp_runner_client.py`)
- MCP Runner 서버와의 HTTP 통신
- 도구 발견 및 실행
- 세션 관리

#### 프롬프트 (`src/prompts/`)
- 중앙집중식 프롬프트 관리
- MCP 결정 프롬프트
- 응답 포맷팅 템플릿

## 문제 해결

### 일반적인 문제들

1. **Google API 오류**
   - 환경 변수에서 `GOOGLE_API_KEY` 확인
   - Google AI Studio에서 API 키 상태 확인
   - 네트워크 연결 상태 확인

2. **MCP Runner 연결 실패**
   - MCP Runner 서버가 실행 중인지 확인
   - `MCP_RUNNER_URL` 설정 확인
   - 포트 및 방화벽 설정 확인

3. **에이전트 시작 문제**
   - Python 의존성 설치 확인: `pip install -r requirements.txt`
   - 포트 8000이 사용 가능한지 확인
   - 로그에서 오류 메시지 확인

### 로그 확인

```bash
# 상세 로깅으로 실행
DEBUG=true python -m src
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
- **Google Gemini**: 2.0 Flash 모델 사용
- **MCP Runner**: 중앙집중식 아키텍처
- **지원 Python 버전**: 3.9+
- **마지막 업데이트**: 2025년 1월

---

*이 문서는 한국어 사용자를 위해 작성되었습니다. 영어 문서는 `README.md`를 참조하세요.*