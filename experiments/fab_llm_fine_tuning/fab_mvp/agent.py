"""
LangGraph 编排: 小模型预处理 -> DeepSeek 生成
============================================================
两条路径对比:
  增强路径: 用户问题 -> [小模型预处理] -> 结构化上下文 -> [DeepSeek] -> 最终SQL/回答
  直接路径: 用户问题 -> [DeepSeek] -> 最终SQL/回答 (无预处理, 作对比基线)

用 LangGraph 1.x StateGraph 编排。
"""
import os
import json
from typing import TypedDict, Optional, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

from fab_mvp.inference import get_predictor, MODE_LABELS
from fab_mvp.knowledge_base import SQL_TEMPLATES, GLOSSARY

load_dotenv()

# ResNet Step 1: DeepSeek 强模型客户端
_llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0.3,
    max_tokens=1500,
)


# ResNet Step 2: 状态定义
class GraphState(TypedDict):
    query: str                        # 用户原始口语问题
    mode: str                         # 小模型预处理模式
    small_output: Optional[dict]      # 小模型预处理结果
    enhanced_answer: Optional[str]    # 增强路径最终回答
    direct_answer: Optional[str]      # 直接路径最终回答
    error: Optional[str]


# ResNet Step 3: 节点 - 小模型预处理
def preprocess_node(state: GraphState) -> dict:
    try:
        predictor = get_predictor()
        out = predictor.predict(state["query"], state["mode"])
        return {"small_output": out}
    except Exception as e:
        return {"small_output": None, "error": f"小模型预处理失败: {e}"}


# ResNet Step 4: 节点 - 增强路径 DeepSeek (拿到小模型结构化上下文)
def enhanced_answer_node(state: GraphState) -> dict:
    so = state.get("small_output") or {}
    mode = state["mode"]
    q = state["query"]
    context_str = json.dumps(so, ensure_ascii=False, indent=2)
    prompt = (
        f"你是晶圆厂资深数据工程师。一位工程师用口语提问:\n「{q}」\n\n"
        f"一个小模型已经对该问题做了预处理(模式: {MODE_LABELS[mode]}), 输出如下结构化上下文:\n{context_str}\n\n"
        f"请基于该上下文, 给出最终回答。要求:\n"
        f"1. 若上下文含 template_id, 请给出对应的SQL(可用知识库模板并填充参数);\n"
        f"2. 若上下文含 enhanced_query, 请据此说明分析思路与涉及表;\n"
        f"3. 输出简洁, 包含【分析思路】和【SQL】两部分。"
    )
    try:
        resp = _llm.invoke(prompt)
        return {"enhanced_answer": resp.content}
    except Exception as e:
        return {"enhanced_answer": None, "error": f"DeepSeek增强路径失败: {e}"}


# ResNet Step 5: 节点 - 直接路径 DeepSeek (无预处理, 对比基线)
def direct_answer_node(state: GraphState) -> dict:
    q = state["query"]
    # 直接路径仅给最小提示(模拟无领域知识注入)
    prompt = (
        f"你是晶圆厂数据工程师。请回答以下问题, 若需要查询数据请给出SQL:\n「{q}」"
    )
    try:
        resp = _llm.invoke(prompt)
        return {"direct_answer": resp.content}
    except Exception as e:
        return {"direct_answer": None, "error": f"DeepSeek直接路径失败: {e}"}


# ResNet Step 6: 构建图
def build_graph():
    g = StateGraph(GraphState)
    g.add_node("preprocess", preprocess_node)
    g.add_node("enhanced_answer", enhanced_answer_node)
    g.add_node("direct_answer", direct_answer_node)
    # 预处理后, 同时走增强和直接两条路径
    g.add_edge(START, "preprocess")
    g.add_edge("preprocess", "enhanced_answer")
    g.add_edge("preprocess", "direct_answer")
    g.add_edge("enhanced_answer", END)
    g.add_edge("direct_answer", END)
    return g.compile()


_graph = None


def run_comparison(query: str, mode: str = "mode_a") -> dict:
    """便捷入口: 跑完整对比, 返回所有结果"""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph.invoke({"query": query, "mode": mode})


if __name__ == "__main__":
    # 自检: 跑一个对比
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "昨天3号机良率掉的厉害咋回事"
    mode = sys.argv[2] if len(sys.argv) > 2 else "mode_a"
    print(f"问题: {q}  | 模式: {MODE_LABELS[mode]}")
    r = run_comparison(q, mode)
    print("\n--- 小模型预处理 ---")
    print(json.dumps(r.get("small_output"), ensure_ascii=False, indent=2))
    print("\n--- 增强路径 DeepSeek ---")
    print(r.get("enhanced_answer"))
    print("\n--- 直接路径 DeepSeek (对比) ---")
    print(r.get("direct_answer"))
