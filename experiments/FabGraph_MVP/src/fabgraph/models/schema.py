"""Schema 元数据模型。

定义晶圆厂 Oracle 元数据的 Pydantic 模型：
- :class:`Table` / :class:`Column` / :class:`Procedure`
- :class:`SemanticHint`：SQL 分析推断出的字段语义提示

对应ResNet输入层：原始元数据标准化为结构化"张量"，
后续由 sql_analyzer 逐层注入语义信号。
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ColumnSemanticType(str, Enum):
    """字段语义类型枚举。

    对应ResNet分类头的类别标签，由 SQL 分析与 LLM 推断共同预测。
    """

    PRIMARY_KEY = "primary_key"      # 主键
    FOREIGN_KEY = "foreign_key"      # 外键
    MEASURE = "measure"              # 度量值（如良率、缺陷数）
    DIMENSION = "dimension"          # 维度（如批次号、设备号）
    TIMESTAMP = "timestamp"          # 时间戳
    STATUS_FLAG = "status_flag"      # 状态标志
    IDENTIFIER = "identifier"        # 标识符
    PARAMETER = "parameter"          # 工艺参数
    UNKNOWN = "unknown"              # 未确定


class Column(BaseModel):
    """字段模型。

    Attributes:
        table_name: 所属表名。
        column_name: 字段名（保留原始命名风格）。
        data_type: Oracle 数据类型，如 VARCHAR2(20)。
        nullable: 是否允许 NULL。
        position: 字段在表中的序号。
        semantic_type: 推断的语义类型。
        semantic_label: 语义标签（中文）。
        description: 字段描述。
        confidence: 语义推断置信度 [0,1]。
        aliases: SQL 中出现过的别名。
    """

    table_name: str
    column_name: str
    data_type: str = "VARCHAR2"
    nullable: bool = True
    position: int = 0
    semantic_type: ColumnSemanticType = ColumnSemanticType.UNKNOWN
    semantic_label: str = ""
    description: str = ""
    confidence: float = 0.0
    aliases: list[str] = Field(default_factory=list)


class Table(BaseModel):
    """表模型。

    Attributes:
        table_name: 表名。
        schema_name: Oracle schema，默认 FAB。
        description: 表描述。
        row_count: 估算行数。
        columns: 字段列表。
        tags: 业务标签（如 yield/defect/spc）。
    """

    table_name: str
    schema_name: str = "FAB"
    description: str = ""
    row_count: int = 0
    columns: list[Column] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class Procedure(BaseModel):
    """存储过程模型。

    在血缘超图中作为超边，连接其读取/写入的表。

    Attributes:
        procedure_name: 过程名。
        schema_name: 所属 schema。
        definition: 过程体 SQL 文本。
        input_tables: 读取的表。
        output_tables: 写入的表。
        description: 过程描述。
    """

    procedure_name: str
    schema_name: str = "FAB"
    definition: str = ""
    input_tables: list[str] = Field(default_factory=list)
    output_tables: list[str] = Field(default_factory=list)
    description: str = ""


class SemanticHint(BaseModel):
    """SQL 分析推断出的语义提示。

    对应ResNet残差连接：每条历史 SQL 贡献一个增量语义信号，
    叠加到字段的语义推断结果上，缓解长链推断的梯度衰减。

    Attributes:
        table_name: 目标表。
        column_name: 目标字段。
        hint_type: 提示类型：join_key | filter | aggregate | alias | lineage。
        hint_value: 提示值（如关联表名、聚合函数）。
        confidence: 本提示的置信度 [0,1]。
        source_sql: 来源 SQL 文本（或指纹）。
        inferred_by_llm: 是否由 LLM 推断。
        extra: 额外上下文。
    """

    table_name: str
    column_name: str
    hint_type: str
    hint_value: str = ""
    confidence: float = 0.5
    source_sql: str = ""
    inferred_by_llm: bool = False
    extra: dict[str, Any] = Field(default_factory=dict)
