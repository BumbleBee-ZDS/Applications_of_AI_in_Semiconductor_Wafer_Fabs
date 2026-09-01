import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import networkx as nx
from sqlmodel import SQLModel, create_engine, Session, select

from .schema import Lot, Wafer, Equipment, ProcessStep, Defect, GRAPH_RELATIONS


class OntologyBuilder:
    """
    Ontology 构建器：使用 NetworkX (内存图) + SQLite (属性存储) 替代 Neo4j
    - NetworkX DiGraph: 存储 Object 之间的 Link 关系
    - SQLite via SQLModel: 存储 Object 的详细属性
    """

    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path
        self.engine = create_engine(f"sqlite:///{sqlite_path}")
        SQLModel.metadata.create_all(self.engine)
        # 使用有向图存储 Ontology 关系
        self.graph = nx.DiGraph()

    def _add_node(self, node_id: str, node_type: str, **attrs):
        """添加节点到图中（带类型标签）"""
        self.graph.add_node(node_id, node_type=node_type, **attrs)

    def _add_edge(self, source_id: str, target_id: str, relation: str, **attrs):
        """添加关系到图中"""
        self.graph.add_edge(source_id, target_id, relation=relation, **attrs)

    def seed_data(self):
        """生成模拟数据：3个 Lot，每个 5 个 Wafer，经过 2 个 Equipment"""
        # 清空现有数据
        self.graph.clear()
        SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine)
        print("🔄 已清空旧数据")

        with Session(self.engine) as session:
            # === 设备数据 ===
            equipment_data = [
                Equipment(eq_id="ETCH-A03", type="Etch", status="RUNNING", alarm_count=5),
                Equipment(eq_id="CVD-B02", type="CVD", status="RUNNING", alarm_count=2),
                Equipment(eq_id="LITH-C01", type="Lithography", status="WARNING", alarm_count=8),
                Equipment(eq_id="CMP-D01", type="CMP", status="RUNNING", alarm_count=1),
            ]
            session.add_all(equipment_data)
            session.commit()
            for eq in equipment_data:
                self._add_node(eq.eq_id, "Equipment",
                               type=eq.type, status=eq.status, alarm_count=eq.alarm_count)

            lot_data, wafer_data, step_data, defect_data = [], [], [], []

            for lot_idx in range(3):
                lot_id = f"Lot-W{80 + lot_idx}"
                product_name = "14nm-FinFET" if lot_idx == 0 else "7nm-GAA"
                # Lot-W80 良率偏低，作为 RCA 目标
                yield_value = 0.82 if lot_idx == 0 else 0.95

                lot = Lot(lot_id=lot_id, product_name=product_name, current_yield=yield_value)
                lot_data.append(lot)
                self._add_node(lot_id, "Lot",
                               product_name=product_name,
                               current_yield=yield_value, status="RUNNING")

                for wafer_idx in range(5):
                    wafer_id = f"WAFER-W{80 + lot_idx}-{wafer_idx:02d}"
                    wafer = Wafer(wafer_id=wafer_id, slot=wafer_idx, parent_lot_id=lot_id)
                    wafer_data.append(wafer)

                    # Lot-W80 前两片晶圆有缺陷
                    if lot_idx == 0 and wafer_idx < 2:
                        wafer.defect_count = 3
                        for d_idx in range(3):
                            defect = Defect(
                                defect_id=f"DEF-{wafer_id}-{d_idx}",
                                wafer_id=wafer_id,
                                type="Particle" if d_idx == 0 else "Scratch",
                                severity="HIGH" if d_idx == 0 else "MEDIUM",
                                location_x=0.3 + d_idx * 0.1,
                                location_y=0.4 + d_idx * 0.1,
                            )
                            defect_data.append(defect)
                            self._add_node(defect.defect_id, "Defect",
                                           wafer_id=wafer_id, type=defect.type,
                                           severity=defect.severity)
                            self._add_edge(wafer_id, defect.defect_id, "HAS_DEFECT")

                    self._add_node(wafer_id, "Wafer",
                                   slot=wafer_idx, parent_lot_id=lot_id,
                                   defect_count=wafer.defect_count)
                    # Lot -[:CONTAINS]-> Wafer
                    self._add_edge(lot_id, wafer_id, "CONTAINS")

                    # 每片晶圆经过 2 台设备
                    for step_idx, eq in enumerate(equipment_data[:2]):
                        step_id = f"STEP-{wafer_id}-{step_idx}"
                        step = ProcessStep(
                            step_id=step_id,
                            lot_id=lot_id,
                            eq_id=eq.eq_id,
                            recipe_name=f"RECIPE-{eq.type}-{step_idx}",
                            timestamp=datetime.now() - timedelta(hours=step_idx * 2),
                        )
                        step_data.append(step)
                        self._add_node(step_id, "ProcessStep",
                                       lot_id=lot_id, eq_id=eq.eq_id,
                                       recipe_name=step.recipe_name)
                        # Wafer -[:PROCESSED_ON]-> Equipment
                        self._add_edge(wafer_id, eq.eq_id, "PROCESSED_ON")
                        # Lot -[:HAS_STEP]-> ProcessStep
                        self._add_edge(lot_id, step_id, "HAS_STEP")
                        # ProcessStep -[:ASSIGNED_TO]-> Equipment
                        self._add_edge(step_id, eq.eq_id, "ASSIGNED_TO")

            session.add_all(lot_data)
            session.add_all(wafer_data)
            session.add_all(step_data)
            session.add_all(defect_data)
            session.commit()

        print(f"✅ 播种完成: {self.graph.number_of_nodes()} 个节点, "
              f"{self.graph.number_of_edges()} 条关系")

    # ============ 图查询接口（替代 Cypher）============

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """获取节点及其属性"""
        if node_id in self.graph:
            return {"id": node_id, **self.graph.nodes[node_id]}
        return None

    def get_neighbors(self, node_id: str, relation: Optional[str] = None,
                      direction: str = "out") -> List[Dict[str, Any]]:
        """
        获取节点的邻居
        - direction: "out" (出边), "in" (入边), "both" (双向)
        - relation: 过滤特定关系类型
        """
        if node_id not in self.graph:
            return []

        results = []
        if direction in ("out", "both"):
            for _, target, data in self.graph.out_edges(node_id, data=True):
                if relation is None or data.get("relation") == relation:
                    results.append({
                        "target": target,
                        "relation": data.get("relation"),
                        "target_attrs": dict(self.graph.nodes[target]),
                    })
        if direction in ("in", "both"):
            for source, _, data in self.graph.in_edges(node_id, data=True):
                if relation is None or data.get("relation") == relation:
                    results.append({
                        "source": source,
                        "relation": data.get("relation"),
                        "source_attrs": dict(self.graph.nodes[source]),
                    })
        return results

    def find_nodes_by_type(self, node_type: str) -> List[Dict[str, Any]]:
        """按类型查找所有节点"""
        return [
            {"id": n, **attrs}
            for n, attrs in self.graph.nodes(data=True)
            if attrs.get("node_type") == node_type
        ]

    def find_shortest_path(self, source: str, target: str) -> List[str]:
        """查找两个节点间的最短路径"""
        try:
            return nx.shortest_path(self.graph, source, target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_relation_subgraph(self, node_id: str, depth: int = 2) -> Dict[str, Any]:
        """获取以 node_id 为中心、深度为 depth 的子图"""
        if node_id not in self.graph:
            return {"nodes": [], "edges": []}

        # BFS 获取指定深度的节点
        visited = {node_id: 0}
        queue = [node_id]
        while queue:
            current = queue.pop(0)
            current_depth = visited[current]
            if current_depth >= depth:
                continue
            for neighbor in self.graph.successors(current):
                if neighbor not in visited:
                    visited[neighbor] = current_depth + 1
                    queue.append(neighbor)
            for neighbor in self.graph.predecessors(current):
                if neighbor not in visited:
                    visited[neighbor] = current_depth + 1
                    queue.append(neighbor)

        sub = self.graph.subgraph(visited.keys())
        nodes = [{"id": n, **attrs} for n, attrs in sub.nodes(data=True)]
        edges = [
            {"source": u, "target": v, **data}
            for u, v, data in sub.edges(data=True)
        ]
        return {"nodes": nodes, "edges": edges}

    # ============ SQLite 属性查询接口 ============

    def get_object_details(self, object_type: str, object_id: str) -> Optional[Dict[str, Any]]:
        """根据对象类型和 ID 从 SQLite 获取详细属性"""
        model_map = {
            "Lot": (Lot, "lot_id"),
            "Wafer": (Wafer, "wafer_id"),
            "Equipment": (Equipment, "eq_id"),
            "ProcessStep": (ProcessStep, "step_id"),
            "Defect": (Defect, "defect_id"),
        }
        if object_type not in model_map:
            return None
        model, id_field = model_map[object_type]
        with Session(self.engine) as session:
            statement = select(model).where(getattr(model, id_field) == object_id)
            result = session.exec(statement).first()
            return result.dict() if result else None

    def update_lot_status(self, lot_id: str, status: str) -> bool:
        """更新批次状态（Hold 操作）"""
        with Session(self.engine) as session:
            lot = session.exec(select(Lot).where(Lot.lot_id == lot_id)).first()
            if lot:
                lot.status = status
                session.commit()
                # 同步更新图节点属性
                if lot_id in self.graph:
                    self.graph.nodes[lot_id]["status"] = status
                return True
            return False

    def export_graph(self) -> Dict[str, Any]:
        """导出图为字典（用于调试/可视化）"""
        nodes = [{"id": n, **attrs} for n, attrs in self.graph.nodes(data=True)]
        edges = [
            {"source": u, "target": v, **data}
            for u, v, data in self.graph.edges(data=True)
        ]
        return {"nodes": nodes, "edges": edges}
