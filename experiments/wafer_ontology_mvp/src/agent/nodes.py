from typing import Dict, Any, List
import json
import ast

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .state import GraphState


def parse_llm_json(response_text: str) -> Dict[str, Any]:
    """
    解析 LLM 返回的 JSON
    支持标准 JSON (双引号) 和 Python 字典格式 (单引号)
    """
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(response_text)
        except (SyntaxError, ValueError):
            return {"thought": response_text, "action": "FINISH", "action_input": response_text}


def create_agent_node(llm: ChatOpenAI, tools: List[Any]):
    """
    创建 Agent 的核心节点函数
    负责调用 LLM 进行推理和决策
    """

    # 系统提示词：强调基于 Ontology 工具进行调查，禁止凭空猜测
    system_prompt = """
你是一位资深的半导体晶圆厂 PIE (Process Integration Engineer) 专家，擅长根因分析 (RCA)。

**核心职责**:
基于 Ontology 知识图谱和工具，对晶圆厂的质量问题进行系统性调查和根因定位。

**重要规则**:
1. 禁止凭空猜测！必须使用提供的工具进行调查。
2. 优先使用 query_ontology_graph 查找关联关系（无需 Cypher，直接传入节点ID和关系类型）。
3. 使用 get_object_details 获取具体属性数值（良率、报警计数等）。
4. 使用 find_nodes_by_type 列出某类型的所有节点。
5. 确认问题后，可使用 hold_lot_action 暂停受影响的批次。
6. 最终结论必须基于工具返回的实际数据。

**Ontology 对象类型**:
- Lot: 批次，包含 lot_id, product_name, current_yield, status
- Wafer: 晶圆，包含 wafer_id, slot, parent_lot_id, defect_count
- Equipment: 设备，包含 eq_id, type(Etch/CVD/Lithography/CMP), status, alarm_count
- ProcessStep: 工艺步骤，包含 step_id, lot_id, eq_id, recipe_name
- Defect: 缺陷，包含 defect_id, wafer_id, type(Particle/Scratch), severity(HIGH/MEDIUM)

**可用关系 (Link Types)**:
- CONTAINS: Lot -> Wafer (批次包含晶圆)
- PROCESSED_ON: Wafer -> Equipment (晶圆在设备上加工)
- HAS_STEP: Lot -> ProcessStep (批次包含工艺步骤)
- ASSIGNED_TO: ProcessStep -> Equipment (工艺步骤分配到设备)
- HAS_DEFECT: Wafer -> Defect (晶圆存在缺陷)

**工具调用示例**:
- 查询 Lot-W80 包含哪些晶圆: query_ontology_graph(node_id="Lot-W80", relation="CONTAINS", direction="out")
- 查询哪些晶圆在 ETCH-A03 上加工过: query_ontology_graph(node_id="ETCH-A03", relation="PROCESSED_ON", direction="in")
- 获取 Lot-W80 的详细属性: get_object_details(object_type="Lot", object_id="Lot-W80")
- 列出所有设备: find_nodes_by_type(node_type="Equipment")

**输出格式**:
返回 JSON 格式，包含以下字段:
- thought: 你的思考过程
- action: 工具名称或 "FINISH"
- action_input: 工具参数（字典）或最终答案（字符串）

示例:
{{
    "thought": "我需要先查找 Lot-W80 包含的晶圆",
    "action": "query_ontology_graph",
    "action_input": {{"node_id": "Lot-W80", "relation": "CONTAINS", "direction": "out"}}
}}

当完成调查并给出最终结论时:
{{
    "thought": "调查完成，已定位根因",
    "action": "FINISH",
    "action_input": "根因分析报告..."
}}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    def agent_node(state: GraphState) -> Dict[str, Any]:
        """
        Agent 节点：调用 LLM 进行推理

        ReAct 循环中的 Reasoning 阶段：
        1. 读取当前消息历史（包括工具返回的 Observation）
        2. 调用 LLM 决策下一步行动
        3. 更新 state 中的 next_step 字段，供 router 判断

        Args:
            state: 当前图状态

        Returns:
            更新后的状态
        """
        messages = state["messages"]
        # 取最后一条消息作为 LLM 输入（工具结果会作为 HumanMessage 追加）
        input_text = messages[-1].content if messages else ""

        chain = prompt | llm

        try:
            response = chain.invoke({"input": input_text})
            response_text = response.content

            # 尝试解析 LLM 返回的 JSON 决策
            result = parse_llm_json(response_text)

            state["messages"].append(AIMessage(content=str(result)))
            state["next_step"] = result.get("action", "FINISH")

            # 如果是 FINISH，保存最终答案
            if state["next_step"] == "FINISH":
                state["final_answer"] = result.get("action_input", "")

            return state

        except Exception as e:
            error_msg = f"LLM 调用失败: {str(e)}"
            state["messages"].append(AIMessage(content=error_msg))
            state["next_step"] = "FINISH"
            state["final_answer"] = error_msg
            return state

    return agent_node


def create_tool_node(tools: List[Any]):
    """
    创建工具执行节点函数
    负责执行 Agent 调用的工具
    """
    tool_map = {tool.name: tool for tool in tools}

    def tool_node(state: GraphState) -> Dict[str, Any]:
        """
        工具节点：执行工具调用

        ReAct 循环中的 Acting 阶段：
        1. 从 Agent 的最后一条消息中解析 action 和 action_input
        2. 调用对应工具执行查询/操作
        3. 将工具结果作为 Observation 追加到消息历史

        Args:
            state: 当前图状态

        Returns:
            更新后的状态
        """
        last_message = state["messages"][-1]
        message_content = last_message.content

        try:
            result = parse_llm_json(message_content)
            action = result.get("action", "")
            action_input = result.get("action_input", "")

            if action in tool_map:
                tool_func = tool_map[action]

                # action_input 可以是 dict（多参数）或 str（单参数）
                if isinstance(action_input, dict):
                    tool_result = tool_func.invoke(action_input)
                else:
                    tool_result = tool_func.invoke(action_input)

                # 将工具结果作为 Observation 追加到消息历史
                tool_msg = ToolMessage(str(tool_result), tool_call_id=action)
                state["messages"].append(tool_msg)
                state["tool_results"].append({"action": action, "result": str(tool_result)})

                # 如果是 hold_lot_action 且执行成功，记录到 hold_lots
                if action == "hold_lot_action" and "Holding" in str(tool_result):
                    lot_id = action_input if isinstance(action_input, str) else action_input.get("lot_id", "")
                    if lot_id and lot_id not in state["hold_lots"]:
                        state["hold_lots"].append(lot_id)
            else:
                error_msg = f"未知工具: {action}"
                state["messages"].append(ToolMessage(error_msg, tool_call_id=action))

        except json.JSONDecodeError as e:
            error_msg = f"JSON 解析失败: {str(e)}"
            state["messages"].append(ToolMessage(error_msg, tool_call_id="parse_error"))
        except Exception as e:
            error_msg = f"工具执行失败: {str(e)}"
            state["messages"].append(ToolMessage(error_msg, tool_call_id="execute_error"))

        # 工具执行完毕，回到 agent 节点继续推理
        state["next_step"] = "agent"
        return state

    return tool_node
