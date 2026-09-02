from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from langchain_core.messages import HumanMessage

from agent.graph import build_agent_graph, create_llm_instance
from ontology.graph_builder import OntologyBuilder
from agent.state import GraphState
from config import settings

router = APIRouter()

# 全局 Ontology 和 Agent 实例（应用启动时初始化）
ontology_builder: OntologyBuilder = None
agent_graph = None


class InvestigateRequest(BaseModel):
    query: str


class InvestigateResponse(BaseModel):
    final_answer: str
    thought_chain: List[Dict[str, str]]
    tool_calls: List[Dict[str, str]]
    hold_lots: List[str]


@router.post("/investigate", response_model=InvestigateResponse)
async def investigate(request: InvestigateRequest):
    """
    启动 Agent 进行根因分析调查

    流程:
    1. 将用户查询作为初始消息注入 LangGraph
    2. Agent 节点调用 LLM 推理决策
    3. 路由器判断是否需要调用工具
    4. 工具节点执行查询/操作后回到 Agent 节点
    5. 循环直到 Agent 给出最终答案

    Args:
        request: 包含用户查询的请求体

    Returns:
        Agent 的完整思考链和最终结论
    """
    if not agent_graph or not ontology_builder:
        raise HTTPException(status_code=500, detail="Agent 系统未初始化")

    try:
        initial_state: GraphState = {
            "messages": [HumanMessage(content=request.query)],
            "next_step": "agent",
            "final_answer": "",
            "tool_results": [],
            "hold_lots": [],
        }

        # 异步调用 LangGraph
        result = await agent_graph.ainvoke(initial_state)

        # 构建思考链
        thought_chain = []
        for msg in result["messages"]:
            thought_chain.append({
                "type": msg.type,
                "content": msg.content[:500] if len(msg.content) > 500 else msg.content,
            })

        return InvestigateResponse(
            final_answer=result.get("final_answer") or str(result["messages"][-1].content),
            thought_chain=thought_chain,
            tool_calls=result["tool_results"],
            hold_lots=result["hold_lots"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调查失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}


@router.get("/graph")
async def get_graph():
    """获取 Ontology 图结构（用于可视化）"""
    if not ontology_builder:
        raise HTTPException(status_code=500, detail="系统未初始化")
    return ontology_builder.export_graph()


def initialize_agent():
    """
    初始化 Agent 系统
    在应用启动时调用：创建 OntologyBuilder → 播种数据 → 构建 Agent 图
    """
    global agent_graph, ontology_builder

    print("🔧 初始化 Ontology Builder (NetworkX + SQLite)...")
    ontology_builder = OntologyBuilder(sqlite_path=settings.SQLITE_DB_PATH)

    print("🌱 播种模拟数据...")
    ontology_builder.seed_data()

    print("🤖 创建 LLM 实例 (DeepSeek)...")
    llm = create_llm_instance(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
    )

    print("🔗 构建 Agent 图...")
    agent_graph = build_agent_graph(ontology_builder, llm)

    print("✅ Agent 系统初始化完成！")
