"""DH 에이전트 실행기"""

import asyncio
import logging
from typing import Dict, List, Any, AsyncGenerator

from a2a.server.agent_execution import AgentExecutor as BaseAgentExecutor, RequestContext
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    TaskState,
    TaskStatus,
    TextPart,
    DataPart,
)
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message, new_text_artifact

from src.agent.dh_agent import DhAgent

logger = logging.getLogger(__name__)


class DhAgentExecutor(BaseAgentExecutor):
    """DH 에이전트와 연결된 실행기 클래스"""
    
    def __init__(self):
        self._startup_complete = False
        self.agent = DhAgent()
        
    async def startup(self):
        """에이전트 및 실행기 초기화"""
        if not self._startup_complete:
            try:
                # 에이전트 초기화
                await self.agent.initialize()
                self._startup_complete = True
                logger.info("DhAgentExecutor 초기화 완료")
            except Exception as e:
                logger.error(f"DhAgentExecutor 초기화 실패: {e}")
                self._startup_complete = False
                raise
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """사용자 요청을 처리하고 결과를 스트리밍"""
        
        # RequestContext에서 올바른 속성들 추출
        user_message = self._extract_message(context)
        
        # context_id와 task_id를 context에서 추출 (A2A 표준에 따라)
        context_id = getattr(context, 'context_id', 'default_context')
        task_id = getattr(context, 'id', 'default_task')
        
        try:
            # 에이전트에게 작업 위임
            async for item in self.agent.stream(user_message, context_id, task_id):
                # 작업 완료 여부 확인
                is_task_complete = item.get('is_task_complete', False)
                require_user_input = item.get('require_user_input', False)
                
                if is_task_complete:
                    # 작업 완료 시 최종 결과 전송
                    if item['response_type'] == 'data':
                        # 구조화된 데이터 응답 (예: HTML, JSON 등)
                        await event_queue.enqueue_event(
                            TaskArtifactUpdateEvent(
                                append=False,
                                context_id=context_id,
                                task_id=task_id,
                                last_chunk=True,
                                artifact=new_text_artifact(
                                    name='generated_document',
                                    description='Generated document by DH Agent',
                                    text=item['content'],
                                ),
                            )
                        )
                    else:
                        # 일반 텍스트 응답
                        await event_queue.enqueue_event(
                            TaskArtifactUpdateEvent(
                                append=False,
                                context_id=context_id,
                                task_id=task_id,
                                last_chunk=True,
                                artifact=new_text_artifact(
                                    name='response',
                                    description='Response from DH Agent',
                                    text=item['content'],
                                ),
                            )
                        )
                    
                    # 작업 완료 상태 전송
                    await event_queue.enqueue_event(
                        TaskStatusUpdateEvent(
                            status=TaskStatus(state=TaskState.completed),
                            final=True,
                            context_id=context_id,
                            task_id=task_id,
                        )
                    )
                    
                elif require_user_input:
                    # 사용자 입력 요구
                    await event_queue.enqueue_event(
                        TaskStatusUpdateEvent(
                            status=TaskStatus(
                                state=TaskState.input_required,
                                message=new_agent_text_message(
                                    item['content'],
                                ),
                            ),
                            final=True,
                            context_id=context_id,
                            task_id=task_id,
                        )
                    )
                    
                else:
                    # 진행 상태 업데이트
                    await event_queue.enqueue_event(
                        TaskStatusUpdateEvent(
                            append=True,
                            status=TaskStatus(
                                state=TaskState.working,
                                message=new_agent_text_message(
                                    item['content'],
                                ),
                            ),
                            final=False,
                            context_id=context_id,
                            task_id=task_id,
                        )
                    )
                    
        except Exception as e:
            logger.error(f"DhAgentExecutor 실행 중 오류: {e}")
            # 오류 발생 시 오류 상태 전송
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    status=TaskStatus(
                        state=TaskState.failed,
                        message=new_agent_text_message(
                            f"처리 중 오류가 발생했습니다: {str(e)}",
                        ),
                    ),
                    final=True,
                    context_id=context_id,
                    task_id=task_id,
                )
            )
    
    def _extract_message(self, context: RequestContext) -> str:
        """RequestContext에서 사용자 메시지 추출"""
        user_message = ""
        if hasattr(context, "message") and context.message:
            if hasattr(context.message, "parts") and context.message.parts:
                for part in context.message.parts:
                    if hasattr(part, "root") and part.root:
                        if hasattr(part.root, "text"):
                            user_message += part.root.text
                    elif hasattr(part, "text"):
                        user_message += part.text
        return user_message
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """작업 취소"""
        
        # context_id와 task_id를 context에서 추출
        context_id = getattr(context, 'context_id', 'default_context')
        task_id = getattr(context, 'id', 'default_task')
        
        if hasattr(self.agent, 'cancel'):
            await self.agent.cancel()
        
        # 취소 상태 전송
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                status=TaskStatus(
                    state=TaskState.cancelled,
                    message=new_agent_text_message(
                        "작업이 취소되었습니다.",
                        context_id,
                        task_id,
                    ),
                ),
                final=True,
                context_id=context_id,
                task_id=task_id,
            )
        )
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            if hasattr(self.agent, 'cleanup'):
                await self.agent.cleanup()
            self._startup_complete = False
            logger.info("DhAgentExecutor 정리 완료")
        except Exception as e:
            logger.error(f"DhAgentExecutor 정리 중 오류: {e}")
    
    @property
    def is_ready(self) -> bool:
        """실행기가 준비되었는지 확인"""
        return self._startup_complete and self.agent is not None
