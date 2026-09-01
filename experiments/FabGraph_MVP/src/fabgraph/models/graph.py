"""图谱数据模型。

定义 Schema Graph 与 Lineage Graph 的节点、边与超边模型，
以及 NL2SQL 使用的 JOIN 路径模型。

对应ResNet跨层连接：图结构在表节点间传播
语义与血缘信息，避免单点特征的语义孤岛。
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """图节点类型。"""

    TABLE = "table"
    COLUMN = "column"
    PROCEDURE = "procedure"


class EdgeType(str, Enum):
    """图边类型。"""

    HAS_COLUMN = "has_column"        # 表 - 字段
    FOREIGN_KEY = "foreign_key"      # 外键关联
    JOIN_INFERRED = "join_inferred"  # SQL 推断的 JOIN 关系
    READS = "reads"                  # 过程读取表（血缘）
    WRITES = "writes"                # 过程写入表（血缘）
    LINEAGE = "lineage"              # 数据血缘（表到表）


class GraphNode(BaseModel):
    """图节点。

    Attributes:
        node_id: 节点唯一标识（如 table:LOT_HISTORY）。
        node_type: 节点类型。
        name: 展示名。
        properties: 附加属性。
    """

    node_id: str
    node_type: NodeType
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """图边。

    Attributes:
        source: 源节点 id。
        target: 目标节点 id。
        edge_type: 边类型。
        weight: 边权重（JOIN 频次等）。
        properties: 附加属性。
    """

    source: str
    target: str
    edge_type: EdgeType
    weight: float = 1.0
    properties: dict[str, Any] = Field(default_factory=dict)


class HyperEdge(BaseModel):
    """超边：一个 Procedure 连接多张表。

    对应ResNet中的 skip connection：将多个表节点通过
    一个过程节点关联，保留跨表语义信息不被池化稀释。

    Attributes:
        edge_id: 超边唯一标识。
        procedure_name: 关联的过程名。
        source_tables: 输入表列表。
        target_tables: 输出表列表。
        properties: 附加属性。
    """

    edge_id: str
    procedure_name: str
    source_tables: list[str] = Field(default_factory=list)
    target_tables: list[str] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)


class JoinPath(BaseModel):
    """JOIN 路径（NL2SQL 使用）。

    由 NetworkX 最短路径算法计算得出，用于组装 NL2SQL Prompt。

    Attributes:
        start_table: 起始表。
        end_table: 终止表。
        path: 表序列。
        join_conditions: 各段 JOIN 条件。
        total_weight: 路径总权重（越小越优）。
    """

    start_table: str
    end_table: str
    path: list[str] = Field(default_factory=list)
    join_conditions: list[str] = Field(default_factory=list)
    total_weight: float = 0.0
