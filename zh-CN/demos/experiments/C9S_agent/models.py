from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ProcessStep:
    """
    工艺步骤模型 - 对应 K8s 中的 Pod 容器规格
    
    每个晶圆批次需要经过多个工艺步骤，类似于 Pod 包含多个容器
    """
    name: str                    # 步骤名称，如 'Photolithography', 'Etch'
    tool_type: str               # 所需设备类型，决定调度到哪个 ToolGroup
    duration_sec: int            # 模拟耗时（秒）
    required_params: Dict = field(default_factory=dict)  # 工艺参数


@dataclass
class WaferLot:
    """
    晶圆批次模型 - 对应 K8s 中的 Pod 资源
    
    代表一个正在加工或等待加工的晶圆批次，包含其完整生命周期状态
    """
    id: str                      # 批次号，唯一标识符
    product_type: str            # 产品类型，如 'Logic', 'Memory'
    steps: List[ProcessStep]     # 所有工艺步骤
    steps_remaining: List[ProcessStep]  # 剩余工艺步骤
    current_step_index: int      # 当前执行步骤索引
    status: str                  # 状态: pending/running/completed/failed
    assigned_tool: str           # 当前分配的设备名称
    error_count: int             # 失败次数，超过阈值则标记 failed
    start_time: float = 0        # 开始时间戳
    end_time: float = 0          # 完成时间戳
    progress_percent: int = 0    # 整体进度百分比


@dataclass
class ToolGroup:
    """
    设备组模型 - 对应 K8s 中的 Node 节点资源
    
    代表一类设备的集合，类似于 Node 上的 CPU/内存资源
    """
    name: str                    # 设备组名称
    tool_type: str               # 设备类型，与 ProcessStep.tool_type 匹配
    available_tools: int         # 可用设备数量
    busy_tools: int              # 繁忙设备数量
    
    @property
    def total_tools(self) -> int:
        """总设备数 = 可用 + 繁忙"""
        return self.available_tools + self.busy_tools
    
    @property
    def utilization(self) -> float:
        """设备利用率 = 繁忙数 / 总数"""
        if self.total_tools == 0:
            return 0.0
        return self.busy_tools / self.total_tools