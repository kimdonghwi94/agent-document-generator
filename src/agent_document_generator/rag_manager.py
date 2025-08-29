"""RAG (Retrieval-Augmented Generation) manager for agent self-knowledge."""

import logging
import asyncio
from typing import List, Dict, Any, Optional
import os
import openai
from .config import Config
from .prompts import AgentPrompts

logger = logging.getLogger(__name__)

# Try to import pymilvus, but handle gracefully if not available
try:
    from pymilvus import connections, Collection, DataType, CollectionSchema, FieldSchema, utility
    MILVUS_AVAILABLE = True
except ImportError:
    logger.warning("pymilvus not available. RAG functionality will be disabled.")
    MILVUS_AVAILABLE = False


class RAGManager:
    """Manages RAG operations for agent self-knowledge using Milvus vector database."""

    def __init__(self, config: Config):
        self.config = config
        self.vector_db_url = os.getenv("VECTOR_DB_URL")
        self.collection_name = os.getenv("VECTOR_DB_COLLECTION_NAME", "agent_knowledge")
        self.connected = False
        self.collection = None
        
        # Agent self-knowledge base
        self.agent_knowledge = {
            "identity": "나는 5가지 주요 기능을 제공하는 AI 문서 생성 에이전트입니다. 사용자의 다양한 요청에 응답하여 문서 생성, 정보 검색, 질의응답 서비스를 제공합니다.",
            "capabilities": [
                "HTML 문서 생성 - 사용자 요청에 따라 구조화된 HTML 문서를 생성합니다. 웹페이지, 보고서, 가이드 문서 등을 HTML 형식으로 작성할 수 있습니다.",
                "Markdown 문서 생성 - 깔끔하고 읽기 쉬운 마크다운 문서를 생성합니다. 기술 문서, 설명서, 블로그 포스트 등을 마크다운 형식으로 작성합니다.", 
                "URL 기반 질의응답 - 제공된 URL의 내용을 분석하여 관련 질문에 답변합니다. 웹사이트 내용을 요약하고 특정 질문에 대한 답변을 제공합니다.",
                "에이전트 정보 질의응답 - 제 기능과 능력에 대한 질문에 RAG를 활용하여 답변합니다. 저에 대한 모든 질문에 상세하게 답변드립니다.",
                "웹 검색 - 최신 정보를 검색하여 사용자에게 제공합니다. 실시간 정보 검색과 트렌드 분석을 수행합니다.",
                "일반 질의응답 - 일반적인 질문이나 대화에 자연스럽게 응답합니다."
            ],
            "skills_overview": "제가 가지고 있는 주요 기능은 총 6가지입니다: 1) HTML 문서 생성, 2) Markdown 문서 생성, 3) URL 기반 질의응답, 4) 에이전트 정보 질의응답(RAG), 5) 웹 검색, 6) 일반 질의응답. 각 기능은 특화된 용도로 설계되어 사용자의 다양한 요구사항을 충족합니다.",
            "technology": "a2a 프로토콜을 활용하여 구축되었으며, OpenAI GPT 모델과 MCP 서버를 연동합니다. Milvus 벡터 데이터베이스를 통한 RAG 시스템도 지원합니다.",
            "features": [
                "실시간 문서 생성 및 저장 - 요청 즉시 문서를 생성하고 파일로 저장합니다",
                "다양한 형식 지원 (HTML, Markdown) - 용도에 맞는 최적의 문서 형식을 제공합니다",
                "벡터 데이터베이스를 통한 지식 검색 - RAG 시스템으로 정확한 정보를 검색합니다",
                "MCP 프로토콜을 통한 외부 서비스 연동 - 웹 검색과 URL 분석 기능을 제공합니다",
                "스킬 기반 라우팅 - 질문 유형을 분석하여 최적의 기능으로 자동 연결합니다"
            ],
            "common_queries": [
                "당신이 가지고 있는 기능은 어떤 것들이 있나요? - 제가 제공하는 6가지 주요 기능을 안내해드립니다",
                "너는 무엇을 할 수 있니? - 문서 생성, 질의응답, 웹 검색 등 다양한 서비스를 제공합니다",
                "에이전트 소개해줘 - 저는 AI 문서 생성 및 질의응답 전문 에이전트입니다",
                "주요 기능 설명해줘 - HTML/Markdown 생성, URL 분석, 웹 검색, RAG 질의응답을 제공합니다"
            ]
        }

    async def initialize(self) -> bool:
        """Initialize RAG system with conditional Milvus connection."""
        logger.info("Initializing RAG system...")
        
        if not self.vector_db_url:
            logger.info("VECTOR_DB_URL not configured. RAG will use built-in knowledge only.")
            return True
            
        if not MILVUS_AVAILABLE:
            logger.warning("Milvus library not available. RAG will use built-in knowledge only.")
            return True
            
        try:
            # Try to connect to Milvus
            logger.info(f"Attempting to connect to Milvus at {self.vector_db_url}")
            connections.connect(
                alias="default",
                host=self.vector_db_url.replace("http://", "").split(":")[0],
                port=int(self.vector_db_url.split(":")[-1]) if ":" in self.vector_db_url else 19530
            )
            
            # Check if collection exists, create if not
            if not utility.has_collection(self.collection_name):
                await self._create_collection()
                await self._populate_initial_knowledge()
            else:
                self.collection = Collection(self.collection_name)
                
            self.connected = True
            logger.info("Successfully connected to Milvus vector database")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to connect to Milvus: {e}. Using built-in knowledge only.")
            self.connected = False
            return True

    async def _create_collection(self):
        """Create Milvus collection for agent knowledge."""
        try:
            # Define collection schema
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
                FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=1000)
            ]
            
            schema = CollectionSchema(fields, description="Agent knowledge base")
            self.collection = Collection(name=self.collection_name, schema=schema)
            
            # Create index for vector similarity search
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT", 
                "params": {"nlist": 128}
            }
            self.collection.create_index(field_name="embedding", index_params=index_params)
            logger.info(f"Created Milvus collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to create Milvus collection: {e}")
            raise

    async def _populate_initial_knowledge(self):
        """Populate collection with initial agent knowledge."""
        try:
            knowledge_entries = []
            
            # Convert agent knowledge to searchable entries
            for category, content in self.agent_knowledge.items():
                if isinstance(content, list):
                    for item in content:
                        knowledge_entries.append({
                            "text": item,
                            "category": category,
                            "metadata": f"agent_knowledge_{category}"
                        })
                else:
                    knowledge_entries.append({
                        "text": content,
                        "category": category,
                        "metadata": f"agent_knowledge_{category}"
                    })
            
            # Generate embeddings and insert
            for entry in knowledge_entries:
                embedding = await self._generate_embedding(entry["text"])
                entry["embedding"] = embedding
                
            # Insert into collection
            self.collection.insert([
                [entry["text"] for entry in knowledge_entries],
                [entry["embedding"] for entry in knowledge_entries],
                [entry["category"] for entry in knowledge_entries],
                [entry["metadata"] for entry in knowledge_entries]
            ])
            
            self.collection.load()
            logger.info(f"Populated {len(knowledge_entries)} knowledge entries")
            
        except Exception as e:
            logger.error(f"Failed to populate knowledge: {e}")

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        try:
            client = openai.AsyncOpenAI(
                api_key=self.config.OPENAI_API_KEY,
                timeout=10.0  # 10 second timeout for embeddings
            )
            response = await client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.0] * 1536  # Return zero vector as fallback

    async def search_knowledge(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant knowledge based on query."""
        if self.connected and self.collection:
            try:
                # Generate query embedding
                query_embedding = await self._generate_embedding(query)
                
                # Search in Milvus
                search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
                results = self.collection.search(
                    data=[query_embedding],
                    anns_field="embedding",
                    param=search_params,
                    limit=limit,
                    output_fields=["text", "category", "metadata"]
                )
                
                knowledge_results = []
                for hits in results:
                    for hit in hits:
                        knowledge_results.append({
                            "text": hit.entity.get("text"),
                            "category": hit.entity.get("category"),
                            "score": hit.distance,
                            "metadata": hit.entity.get("metadata")
                        })
                
                return knowledge_results
                
            except Exception as e:
                logger.error(f"Vector search failed: {e}")
                return self._fallback_search(query, limit)
        else:
            return self._fallback_search(query, limit)

    def _fallback_search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Fallback search using built-in knowledge when Milvus is not available."""
        logger.info("Using fallback knowledge search")
        results = []
        query_lower = query.lower()
        
        # Simple keyword matching for fallback
        for category, content in self.agent_knowledge.items():
            if isinstance(content, list):
                for item in content:
                    if any(word in item.lower() for word in query_lower.split()):
                        results.append({
                            "text": item,
                            "category": category,
                            "score": 0.8,  # Static score for fallback
                            "metadata": f"fallback_{category}"
                        })
            else:
                if any(word in content.lower() for word in query_lower.split()):
                    results.append({
                        "text": content,
                        "category": category,
                        "score": 0.8,
                        "metadata": f"fallback_{category}"
                    })
        
        return results[:limit]

    async def generate_rag_response(self, query: str) -> str:
        """Generate response using RAG approach."""
        try:
            # Search for relevant knowledge
            relevant_knowledge = await self.search_knowledge(query, limit=3)
            
            if not relevant_knowledge:
                return "죄송합니다. 해당 질문에 대한 정보를 찾을 수 없습니다. 제 기능이나 능력에 대해 더 구체적으로 질문해 주세요."
            
            # Prepare context from retrieved knowledge
            context = "\n".join([item["text"] for item in relevant_knowledge])
            
            # Generate response using LLM with retrieved context
            client = openai.AsyncOpenAI(
                api_key=self.config.OPENAI_API_KEY,
                timeout=15.0  # 15 second timeout for RAG responses
            )
            
            # Use standardized prompts from AgentPrompts
            prompts = AgentPrompts.get_rag_qa_prompt(context, query)

            response = await client.chat.completions.create(
                model=self.config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": prompts["user"]}
                ],
                max_tokens=400,  # Reduced for faster response
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"RAG response generation failed: {e}")
            return f"답변 생성 중 오류가 발생했습니다: {str(e)}"

    async def cleanup(self):
        """Cleanup RAG resources."""
        if self.connected:
            try:
                connections.disconnect("default")
                logger.info("Disconnected from Milvus")
            except Exception as e:
                logger.error(f"Error disconnecting from Milvus: {e}")