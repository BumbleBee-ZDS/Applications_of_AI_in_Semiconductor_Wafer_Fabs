"""工艺知识库 + RAG 检索（千问 Embedding + 余弦相似度）。

启动时对全部知识文档做一次向量化（约 1~2 次 API 调用），查询时对 query
向量化并与文档向量做余弦相似度检索。未配置千问 Key 或 API 失败时自动回退
到"哈希伪向量"，保证演示流程离线可用。
"""

from __future__ import annotations

import hashlib
from typing import Any, Optional

import numpy as np

from utils.llm_client import EMBEDDING_DIM, embed_texts

# ---------- 预置工艺知识文档（10 条，满足 ≥8 条要求） ----------
KNOWLEDGE_DOCS: list[dict[str, str]] = [
    {
        "doc_id": "KB-001",
        "title": "CVD 温度漂移处理 SOP",
        "category": "CVD / 薄膜",
        "content": "当 CVD 腔体温度偏离配方中心值 ≥0.5°C 时，应立即触发 HOLD：① 停止该腔体进片并挂起当前批次；② 核对 FDC 温控趋势，判断为热电偶漂移、加热器老化或气流扰动；③ 运行空炉补偿（dummy run）验证温控精度；④ 复测 3 次温控偏差 <0.5°C 后恢复生产，并在 SPC 记录放行。派工约束：HOLD 期间禁止向该设备派入任何新批次。",
    },
    {
        "doc_id": "KB-002",
        "title": "CVD 压力异常根因与处置",
        "category": "CVD / 薄膜",
        "content": "CVD 腔体压力偏离配方中心值 ≥15% 时，常见根因包括 MFC（质量流量控制器）漂移、真空泵能力下降、腔体漏气或节气阀故障。处置：① 停止进片并转 HOLD；② 检查 MFC 设定值 vs 实际流量、泵组电流；③ 做 30 分钟泄漏率测试；④ 更换异常部件后以 dummy run 验证压力稳定再复机。若压力波动伴随颗粒上升，需考虑腔体清洁后恢复。",
    },
    {
        "doc_id": "KB-003",
        "title": "光刻 Overlay 超差分析与返工决策",
        "category": "光刻",
        "content": "Overlay 超出规格（如 3nm spec 超差）会影响层间对准精度，可能造成器件电性失效。处置流程：① 立即对受影响批次转 HOLD 并冻结在制品；② 通过 ADC 自动缺陷分类与量测复测确认超差范围；③ 判断为机台漂移（stage 定位、heating 效应）则执行机台校准；④ 返工决策需工程审批，超过 spec 2 倍的批次建议报废评估。派工约束：超差机台校准完成前禁止派入新批次。",
    },
    {
        "doc_id": "KB-004",
        "title": "刻蚀 EPD 丢失处置流程",
        "category": "刻蚀",
        "content": "刻蚀终点检测（EPD）信号丢失时，蚀刻时间无法自动终止，存在过蚀刻损伤器件风险。处置：① 立即暂停该腔体加工并转 HOLD；② 对照 FDC 检查 OES 发射光谱探头状态、窗口污染与信号基线；③ 用测试片（monitor wafer）验证终点判定；④ 确认恢复后重跑 SPC 数据；⑤ 已受影响批次需按 over-etch 时长评估报废或返工。派工约束：EPD 未恢复前禁止派入刻蚀批次。",
    },
    {
        "doc_id": "KB-005",
        "title": "设备 PM 与派工冲突规避规则",
        "category": "设备管理",
        "content": "RTD 派工必须考虑 PM（预防性维护）计划：① 距 PM 到期剩余时间 <120min 的设备不派入长时程批次；② 已逾期（OVERDUE）PM 的设备直接置 HOLD，禁止派工；③ 同区域避免同时安排多台设备 PM，防止产能骤降；④ PM 完成后需执行 qual run（确认片）通过才能恢复自动派工。候选设备排序时 PM 窗口为硬约束。",
    },
    {
        "doc_id": "KB-006",
        "title": "Q-Time 违例风险与紧急派工规则",
        "category": "派工规则",
        "content": "Q-Time（队列时间）是批次在工序间可停留的最长时间，超时会导致颗粒、氧化或膜质劣化甚至报废。RTD 规则：① q_time_remaining_min < 0（已超时）的批次提升为最高派工优先级，并触发告警与人工确认；② 剩余时间 <30min 的批次优先派往最近可用的兼容设备；③ 无法满足 Q-Time 的批次转 HOLD 评估报废风险；④ URGENT 批次优先占用瓶颈设备产能。",
    },
    {
        "doc_id": "KB-007",
        "title": "FDC+SPC 联动监测规则",
        "category": "过程控制",
        "content": "FDC（故障检测与分类）采集设备传感器高频数据，SPC 对工艺参数做统计过程控制。联动规则：① FDC 检出单点超限（温度、压力、RF 功率等）时立即触发告警并冻结相关设备派工；② SPC 检出 Cpk<1.33 或连续漂移时下发工艺参数复核任务；③ 两系统共同标记的异常事件优先进入根因分析队列；④ 恢复生产需 FDC 与 SPC 双通道同时绿灯。",
    },
    {
        "doc_id": "KB-008",
        "title": "瓶颈设备派工与 RTD 优先级规则",
        "category": "派工规则",
        "content": "瓶颈设备（利用率 >90% 的区域设备）决定整条产线吞吐。RTD 派工优先级规则：① URGENT 批次 > Q-Time 超时批次 > HIGH > NORMAL > LOW；② 瓶颈设备优先分配给交期最紧（OTD 压力最大）的批次；③ 设备在制品队列超过阈值时，将部分批次转派到可互换的非瓶颈设备；④ 派工后需评估对下游设备负载的影响，避免瓶颈转移。",
    },
    {
        "doc_id": "KB-009",
        "title": "设备宕机降级与产能再平衡",
        "category": "设备管理",
        "content": "设备宕机（DOWN）时：① 更新区域有效产能并触发产能再平衡计算；② 将宕机设备上的在制批次转移至同 recipe 兼容的替代设备；③ 替代产能不足时按 OTD 紧迫度调整优先级并知会计划部门；④ 宕机时长超过 4 小时启动跨区域借片评估；⑤ 恢复后做 qual run 验证再恢复自动派工。",
    },
    {
        "doc_id": "KB-010",
        "title": "批次 HOLD 与放行审批流程",
        "category": "质量管理",
        "content": "批次 HOLD 与放行遵循双人复核原则：① 工艺异常触发的 HOLD 需工程师在 2 小时内给出处置决定（返工/报废/继续）；② L3 级风险放行需 2 人审批，L4 级需 3 人审批并记录审计日志；③ 放行后批次进入优先派工队列，并在 Lot 档案中留存放行依据；④ 所有 HOLD/放行动作必须可追溯（trace_id 贯穿全链路日志）。",
    },
]

# ---------- 向量索引（模块级缓存，进程内复用） ----------
_KB_VECTORS: Optional[np.ndarray] = None
_INDEX_INFO: dict[str, Any] = {"mode": "未初始化", "docs": 0, "error": "", "dim": 0}


def _pseudo_embedding(text: str, dim: int = EMBEDDING_DIM) -> np.ndarray:
    """确定性哈希伪向量（离线降级用）：字符级哈希累加后归一化。"""
    vec = np.zeros(dim, dtype=np.float32)
    for i, ch in enumerate(text):
        h = int(hashlib.md5(f"{ch}{i}".encode("utf-8")).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec /= norm
    return vec


def ensure_indexed(force: bool = False) -> dict[str, Any]:
    """确保知识文档已向量化（幂等，首次调用时执行 API 向量化）。

    Args:
        force: 是否强制重新向量化。

    Returns:
        索引状态信息：模式 / 文档数 / 错误 / 向量维度。
    """
    global _KB_VECTORS, _INDEX_INFO
    if _KB_VECTORS is not None and not force:
        return dict(_INDEX_INFO)

    docs = KNOWLEDGE_DOCS
    try:
        vectors = embed_texts([d["content"] for d in docs], text_type="document")
        _KB_VECTORS = np.array(vectors, dtype=np.float32)
        _INDEX_INFO = {
            "mode": "qwen3.7-text-embedding（千问）",
            "docs": len(docs),
            "error": "",
            "dim": int(_KB_VECTORS.shape[1]),
        }
    except Exception as exc:  # 无 Key / 网络异常 → 伪向量降级
        _KB_VECTORS = np.array([_pseudo_embedding(d["content"]) for d in docs], dtype=np.float32)
        _INDEX_INFO = {
            "mode": "本地哈希伪向量（降级）",
            "docs": len(docs),
            "error": str(exc)[:200],
            "dim": int(_KB_VECTORS.shape[1]),
        }
    return dict(_INDEX_INFO)


def retrieve(query: str, top_k: int = 3) -> list[tuple[dict[str, str], float]]:
    """对 query 做 RAG 检索，返回 Top-K（文档, 相似度）列表，按相似度降序。

    Args:
        query: 查询文本（如事件描述 / 用户问题）。
        top_k: 返回条数。

    Returns:
        [(文档字典, 余弦相似度), ...]。
    """
    ensure_indexed()
    try:
        query_vec = np.array(embed_texts([query], text_type="query")[0], dtype=np.float32)
    except Exception:  # 查询向量化失败 → 伪向量降级
        query_vec = _pseudo_embedding(query)
    sims = _KB_VECTORS @ query_vec  # 向量均已归一化 → 点积即余弦相似度
    idx = np.argsort(sims)[::-1][:top_k]
    return [(KNOWLEDGE_DOCS[int(i)], float(sims[int(i)])) for i in idx]
