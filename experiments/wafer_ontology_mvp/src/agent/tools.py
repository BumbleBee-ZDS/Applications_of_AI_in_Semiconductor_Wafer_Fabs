from typing import List, Any
from langchain.tools import tool

from ontology.graph_builder import OntologyBuilder


def create_ontology_tools(ontology_builder: OntologyBuilder):
    """
    创建 Agent 可用的工具集
    将 OntologyBuilder 实例注入到工具中
    使用 NetworkX 图查询接口替代 Cypher，LLM 无需学习 Cypher 语法
    """

    @tool("query_ontology_graph")
    def query_ontology_graph(node_id: str, relation: str = "", direction: str = "out") -> str:
        """
        在 Ontology 知识图谱中查询指定节点的关联关系。
        使用图遍历方式查询，无需 Cypher 语法。

        Args:
            node_id: 起始节点 ID，例如 "Lot-W80", "WAFER-W80-00", "ETCH-A03"
            relation: 关系类型过滤，可选值: CONTAINS, PROCESSED_ON, HAS_STEP, ASSIGNED_TO, HAS_DEFECT
                     留空表示查询所有关系
            direction: 查询方向，可选值: out(出边), in(入边), both(双向)

        Returns:
            关联节点列表的字符串表示。

        示例:
            - 查询 Lot-W80 包含哪些晶圆: node_id="Lot-W80", relation="CONTAINS", direction="out"
            - 查询哪些晶圆在 ETCH-A03 上加工过: node_id="ETCH-A03", relation="PROCESSED_ON", direction="in"
        """
        try:
            rel = relation if relation else None
            results = ontology_builder.get_neighbors(node_id, relation=rel, direction=direction)
            if not results:
                return f"未找到节点 {node_id} 的关联关系"
            return str(results)
        except Exception as e:
            return f"❌ 查询失败: {str(e)}"

    @tool("find_nodes_by_type")
    def find_nodes_by_type(node_type: str) -> str:
        """
        按类型查找 Ontology 中的所有节点。

        Args:
            node_type: 节点类型，可选值: Lot, Wafer, Equipment, ProcessStep, Defect

        Returns:
            该类型所有节点的列表。
        """
        try:
            results = ontology_builder.find_nodes_by_type(node_type)
            if not results:
                return f"未找到类型为 {node_type} 的节点"
            return str(results)
        except Exception as e:
            return f"❌ 查询失败: {str(e)}"

    @tool("get_object_details")
    def get_object_details(object_type: str, object_id: str) -> str:
        """
        根据 Object ID 从 SQLite 中获取详细属性（如良率数值、报警计数等）。

        Args:
            object_type: 对象类型，可选值: Lot, Wafer, Equipment, ProcessStep, Defect
            object_id: 对象的唯一标识符

        Returns:
            对象的详细属性信息。
        """
        try:
            result = ontology_builder.get_object_details(object_type, object_id)
            if result:
                return str(result)
            else:
                return f"❌ 未找到 {object_type} {object_id}"
        except Exception as e:
            return f"❌ 获取详情失败: {str(e)}"

    @tool("hold_lot_action")
    def hold_lot_action(lot_id: str) -> str:
        """
        Action 工具：在 MES 系统中 Hold 住批次，防止继续加工。

        Args:
            lot_id: 需要 Hold 的批次 ID，例如 "Lot-W80"

        Returns:
            Hold 操作的执行结果。
        """
        try:
            result = ontology_builder.update_lot_status(lot_id, "HOLD")
            if result:
                return f"🚨 ACTION: Holding Lot {lot_id} - 批次已成功暂停"
            else:
                return f"❌ 未找到批次 {lot_id}"
        except Exception as e:
            return f"❌ Hold 操作失败: {str(e)}"

    @tool("list_equipment_status")
    def list_equipment_status() -> str:
        """
        获取所有设备的状态概览，包括报警计数。

        Returns:
            所有设备的状态信息。
        """
        try:
            equipments = ontology_builder.find_nodes_by_type("Equipment")
            return str(equipments) if equipments else "未找到设备数据"
        except Exception as e:
            return f"❌ 获取设备状态失败: {str(e)}"

    return [query_ontology_graph, find_nodes_by_type, get_object_details,
            hold_lot_action, list_equipment_status]
