from typing import List, Any

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from .state import GraphState
from .nodes import create_agent_node, create_tool_node
from .tools import create_ontology_tools
from ontology.graph_builder import OntologyBuilder


def build_agent_graph(ontology_builder: OntologyBuilder, llm: ChatOpenAI) -> StateGraph:
    """
    构建 LangGraph ReAct 循环图
    
    ReAct (Reasoning + Acting) 工作流程:
    1. Agent 节点: LLM 分析问题，决定下一步行动（调用工具或给出最终答案）
    2. 路由判断: 如果需要调用工具，转到 tool 节点；否则结束流程
    3. 工具节点: 执行工具调用，获取结果后返回 Agent 节点继续推理
    
    Args:
        ontology_builder: OntologyBuilder 实例
        llm: ChatOpenAI LLM 实例
    
    Returns:
        编译后的 StateGraph
    """
    
    tools = create_ontology_tools(ontology_builder)
    agent_node = create_agent_node(llm, tools)
    tool_node = create_tool_node(tools)
    
    workflow = StateGraph(GraphState)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tool", tool_node)
    
    workflow.set_entry_point("agent")
    
    def router(state: GraphState) -> str:
        """
        路由函数：根据 Agent 的决策选择下一步
        
        如果 next_step 是工具名称，则转到 tool 节点；
        如果 next_step 是 "FINISH"，则结束流程。
        """
        next_step = state.get("next_step", "FINISH")
        
        if next_step == "FINISH":
            return END
        
        tool_names = [tool.name for tool in tools]
        if next_step in tool_names:
            return "tool"
        
        return END
    
    workflow.add_conditional_edges("agent", router)
    workflow.add_edge("tool", "agent")
    
    return workflow.compile()


def create_llm_instance(api_key: str, base_url: str) -> ChatOpenAI:
    """
    创建 LLM 实例
    
    Args:
        api_key: DeepSeek API Key
        base_url: DeepSeek API Base URL
    
    Returns:
        ChatOpenAI 实例（配置为使用 DeepSeek）
    """
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=api_key,
        base_url=base_url,
        temperature=0.1,
        max_tokens=2000,
    )
