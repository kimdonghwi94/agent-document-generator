from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from starlette.responses import JSONResponse, RedirectResponse, HTMLResponse

from src.executor.dh_executor import DhAgentExecutor
from src.config import Config


def create_mcp_skills_from_tools(server_name: str, tools: list[dict]) -> list[AgentSkill]:
    """Create individual AgentSkill objects for each MCP tool - each tool represents a distinct capability"""
    if not tools:
        return []
    
    skills = []
    
    for tool in tools:
        tool_name = tool.get("name", "")
        tool_desc = tool.get("description", "")
        
        if not tool_name:
            continue
        
        # Generate skill ID based on tool name
        skill_id = f"mcp_{server_name}_{tool_name}"
        
        # Generate human-readable skill name
        skill_name = tool_name.replace('_', ' ').replace('-', ' ').title()
        
        # Use tool's actual description
        description = tool_desc if tool_desc else f"{tool_name} 도구 기능"
        
        # Generate tags based on tool name and server
        tags = ["mcp", server_name, tool_name]
        
        skill = AgentSkill(
            id=skill_id,
            name=skill_name,
            description=description,
            tags=tags,
            examples=[],  # Remove examples as requested
        )
        
        skills.append(skill)
    
    return skills


async def create_agent_skills(tools):
    """Create agent skills from all available MCP servers (sub_agent_1.py 방식)"""
    if not tools:
        return []
    
    all_skills = []
    
    # 모든 MCP 서버의 도구들을 처리
    for server_name, mcp_tools in tools.items():
        if not mcp_tools:  # 도구가 없는 서버는 건너뛰기
            continue
            
        new_meta = []
        for tool in mcp_tools:
            meta_tool = {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
                "server": server_name
            }
            new_meta.append(meta_tool)
        
        if new_meta:  # 메타데이터가 있는 경우에만 스킬 생성
            mcp_skills = create_mcp_skills_from_tools(server_name, new_meta)
            all_skills.extend(mcp_skills)
    
    return all_skills


async def create_app():
    agent_executor = DhAgentExecutor()
    await agent_executor.startup()

    all_skills = await create_agent_skills(agent_executor.agent.mcp_tools)

    agent_card = AgentCard(
        name="Advanced Document Generator Agent",
        description="HTML, Markdown 문서 생성과 일반 질의응답이 가능한 AI 에이전트입니다.",
        url="https://agent-document-generator.vercel.app/",
        version="2.1.0",
        default_input_modes=["text", "text/plain"],
        default_output_modes=["text/plain", "text/html", "text/markdown", "application/json", "image/png"],
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
            state_transition_history=False,
            extensions=None
        ),
        skills=all_skills,
    )

    # Create agent executor and initialize it

    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )

    # Create A2A server
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    app = server.build()

    @app.route("/health")
    async def health(request):
        return JSONResponse({"status": "healthy"})

    @app.route("/", methods=["GET"])
    async def homepage(request):
        html_content = '''<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Document Generator Agent - Chat</title>
    <style>
      body { 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; 
        margin: 0; 
        background: #f8f9fa;
        min-height: 100vh;
        color: #333;
      }
      .container { 
        max-width: 900px; 
        margin: 0 auto; 
        padding: 30px; 
      }
      h1 { 
        margin: 0 0 24px; 
        font-size: 28px; 
        color: #2c3e50;
        text-align: center;
        font-weight: 700;
        letter-spacing: -0.5px;
      }
      .chat { 
        background: white; 
        border: 1px solid #e9ecef;
        border-radius: 12px; 
        padding: 24px; 
        min-height: 400px; 
        overflow-y: auto;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
      }
      .msg { 
        padding: 12px 16px; 
        border-radius: 16px; 
        margin: 8px 0; 
        max-width: 80%; 
        white-space: pre-wrap;
        animation: fadeIn 0.3s ease-in;
        font-size: 14px;
        line-height: 1.5;
      }
      .status { 
        padding: 8px 12px; 
        border-radius: 12px; 
        margin: 4px 0; 
        max-width: 60%; 
        font-size: 12px;
        color: #6c757d;
        background: #f1f3f5;
        border: 1px solid #dee2e6;
        font-style: italic;
        animation: fadeIn 0.3s ease-in;
      }
      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(5px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .user { 
        background: #007bff;
        color: white;
        margin-left: auto;
        font-weight: 500;
      }
      .agent { 
        background: #ffffff;
        color: #495057;
        border: 1px solid #dee2e6;
      }
      .agent ul {
        margin: 8px 0;
        padding-left: 20px;
      }
      .agent li {
        margin: 4px 0;
        list-style-type: disc;
      }
      .agent strong {
        font-weight: 600;
        color: #2c3e50;
      }
      .agent em {
        font-style: italic;
        color: #6c757d;
      }
      .agent h1, .agent h2, .agent h3 {
        margin: 12px 0 8px 0;
        font-weight: 600;
        color: #2c3e50;
      }
      .agent h1 { font-size: 18px; }
      .agent h2 { font-size: 16px; }
      .agent h3 { font-size: 14px; }
      .input { 
        display: flex; 
        gap: 8px; 
        margin-top: 16px;
        background: white;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #e9ecef;
      }
      input, button { font-size: 14px; }
      input { 
        flex: 1; 
        padding: 12px 16px; 
        border-radius: 8px; 
        border: 1px solid #ced4da; 
        background: white; 
        color: #495057;
        outline: none;
        transition: all 0.2s ease;
      }
      input:focus {
        border-color: #007bff;
        box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.15);
      }
      button { 
        padding: 12px 20px; 
        border-radius: 8px; 
        border: none;
        background: #007bff;
        color: white; 
        cursor: pointer;
        font-weight: 600;
        transition: all 0.2s ease;
      }
      button:hover {
        background: #0056b3;
      }
      button:disabled { 
        opacity: 0.6; 
        cursor: not-allowed;
      }
      .hint { 
        color: #6c757d; 
        font-size: 12px; 
        margin-top: 16px;
        text-align: center;
      }
      a { 
        color: #007bff;
        text-decoration: none;
      }
      a:hover {
        text-decoration: underline;
      }
      code {
        background: #f8f9fa;
        padding: 2px 4px;
        border-radius: 3px;
        font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
        font-size: 11px;
        border: 1px solid #e9ecef;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <h1>Document Generator Agent - Chat</h1>
      <div class="chat" id="chat"></div>
      <div class="input">
        <input id="text" placeholder="메시지를 입력하세요..." />
        <button id="send">전송</button>
      </div>
      <div class="hint">
        이 UI는 <code>/chat</code> 엔드포인트로 메시지를 전송합니다. Agent Card는 <a href="/.well-known/agent.json">/.well-known/agent.json</a>에서 확인할 수 있습니다.
      </div>
    </div>
    <script>
      const chat = document.getElementById('chat');
      const input = document.getElementById('text');
      const btn = document.getElementById('send');
      
      function safeUUID() {
        try {
          if (typeof crypto !== 'undefined' && crypto && typeof crypto.randomUUID === 'function') {
            return crypto.randomUUID();
          }
        } catch (_) {}
        const s4 = () => Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
        return Date.now().toString(16) + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
      }
      let contextId = safeUUID();

      function markdownToHtml(text) {
        if (!text) return '';
        
        try {
          let html = text.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
          
          html = html
            .replace(/^### (.*)$/gim, '<h3>$1</h3>')
            .replace(/^## (.*)$/gim, '<h2>$1</h2>')
            .replace(/^# (.*)$/gim, '<h1>$1</h1>');
            
          let lines = html.split('\\n');
          let result = [];
          let inList = false;
          
          for (let i = 0; i < lines.length; i++) {
            let line = lines[i];
            let trimmed = line.trim();
            if (trimmed.startsWith('* ')) {
              if (!inList) {
                result.push('<ul>');
                inList = true;
              }
              let listItem = trimmed.substring(2);
              result.push('<li>' + listItem + '</li>');
            } else {
              if (inList) {
                result.push('</ul>');
                inList = false;
              }
              if (trimmed === '') {
                result.push('<br>');
              } else {
                result.push(line);
              }
            }
          }
          
          if (inList) {
            result.push('</ul>');
          }
          
          let finalHtml = result.join('\\n').replace(/\\n/g, '<br>');
          finalHtml = finalHtml.replace(/<br><ul>/g, '<ul>').replace(/<\\/ul><br>/g, '</ul>');
          
          return finalHtml;
        } catch (error) {
          console.error('Markdown conversion error:', error);
          return text;
        }
      }

      function addMsg(text, cls) {
        const div = document.createElement('div');
        div.className = 'msg ' + cls;
        
        if (cls === 'agent') {
          div.innerHTML = markdownToHtml(text);
        } else {
          div.textContent = text;
        }
        
        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;
      }

      function addStatusMsg(text) {
        const div = document.createElement('div');
        div.className = 'status';
        div.textContent = text;
        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;
        return div;
      }

      let isProcessing = false;
      let isComposing = false;

      async function send() {
        const text = input.value.trim();
        if (!text || isProcessing) return;
        
        isProcessing = true;
        input.value = '';
        btn.disabled = true;
        
        addMsg(text, 'user');
        const statusMsg = addStatusMsg('답변을 준비하고 있습니다...');
        
        try {
          const res = await fetch('/chat', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' }, 
            body: JSON.stringify({ text, contextId }) 
          });
          
          if (statusMsg && statusMsg.parentNode) {
            statusMsg.parentNode.removeChild(statusMsg);
          }
          
          if (!res.ok) throw new Error('Request failed');
          const data = await res.json();
          if (data && data.reply) {
            addMsg(data.reply, 'agent');
          } else {
            addMsg('[응답 없음]', 'agent');
          }
        } catch (e) {
          if (statusMsg && statusMsg.parentNode) {
            statusMsg.parentNode.removeChild(statusMsg);
          }
          console.error('POST /chat failed', e);
          addMsg('오류: ' + e.message, 'agent');
        } finally {
          btn.disabled = false;
          isProcessing = false;
          input.focus();
        }
      }

      btn.addEventListener('click', send);
      input.addEventListener('compositionstart', () => { isComposing = true; });
      input.addEventListener('compositionend', () => { isComposing = false; });
      
      input.addEventListener('keydown', (e) => { 
        if (e.key === 'Enter' && !e.shiftKey) {
          if (e.isComposing || isComposing) return;
          e.preventDefault();
          e.stopPropagation();
          e.stopImmediatePropagation();
          send(); 
        }
      });
      
      input.focus();
    </script>
  </body>
</html>'''
        return HTMLResponse(html_content)

    @app.route("/chat", methods=["POST"])
    async def chat_endpoint(request):
        try:
            body = await request.json()
            user_message = body.get("text", "")
            context_id = body.get("contextId", "default_context")
            
            if not user_message:
                return JSONResponse({"error": "Message is required"}, status_code=400)
            
            # agent의 stream 메서드를 직접 사용하되, 완료된 응답만 수집
            final_response = ""
            async for item in agent_executor.agent.stream(user_message, context_id, "chat_task"):
                # 작업이 완료된 최종 응답만 사용
                if item.get('is_task_complete', False) and item.get('content'):
                    final_response = item['content']
                    break
            
            response = final_response if final_response else "응답을 생성할 수 없습니다."
            
            return JSONResponse({"reply": response})
            
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    return app


def main():
    import asyncio

    import uvicorn

    config = Config()

    # Create and run the app synchronously
    app = asyncio.run(create_app())

    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")


if __name__ == "__main__":
    main()
