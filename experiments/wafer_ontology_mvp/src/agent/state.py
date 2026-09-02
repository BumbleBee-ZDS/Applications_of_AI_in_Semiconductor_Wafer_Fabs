from typing import TypedDict, List
from langchain_core.messages import BaseMessage


class GraphState(TypedDict):
    """
    LangGraph 的状态定义
    包含对话历史、下一步行动、最终答案和工具调用结果
    """
    messages: List[BaseMessage]
    next_step: str
    final_answer: str
    tool_results: List[dict]
    hold_lots: List[str]
