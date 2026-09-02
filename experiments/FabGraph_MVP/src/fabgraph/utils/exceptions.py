"""自定义异常体系。

所有业务异常均根植于 :class:`FabGraphError`，
API 层捕获后统一返回结构化 JSON 错误响应。
对应ResNet中的"错误信号"：异常在层间传播，
顶层异常处理器统一归约（pooling）为对外错误。
"""
from __future__ import annotations


class FabGraphError(Exception):
    """所有 FabGraph 业务异常的根。

    Attributes:
        message: 人类可读错误描述。
        code: 机器可读错误码，用于 API 响应。
        details: 附加上下文信息。
    """

    code: str = "FABGRAPH_ERROR"

    def __init__(self, message: str = "", *, code: str | None = None,
                 details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        self.details = details or {}

    def to_dict(self) -> dict:
        """转换为结构化字典，供 API 错误响应使用。

        Returns:
            包含 code/message/details 的字典。
        """
        return {"code": self.code, "message": self.message, "details": self.details}


class ConfigError(FabGraphError):
    """配置加载或校验错误。"""
    code = "CONFIG_ERROR"


class MetadataError(FabGraphError):
    """元数据（表/字段/过程）访问或校验错误。"""
    code = "METADATA_ERROR"


class GraphError(FabGraphError):
    """图谱构建或查询错误。"""
    code = "GRAPH_ERROR"


class SQLAnalysisError(FabGraphError):
    """SQL 解析与分析错误。"""
    code = "SQL_ANALYSIS_ERROR"


class SearchError(FabGraphError):
    """语义搜索错误。"""
    code = "SEARCH_ERROR"


class EmbeddingError(FabGraphError):
    """向量嵌入生成或加载错误。"""
    code = "EMBEDDING_ERROR"


class LLMError(FabGraphError):
    """LLM 调用错误。"""
    code = "LLM_ERROR"


class NL2SQLError(FabGraphError):
    """NL2SQL 生成错误。"""
    code = "NL2SQL_ERROR"
