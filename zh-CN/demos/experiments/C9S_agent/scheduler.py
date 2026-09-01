from typing import List, Optional
from models import ToolGroup


class SchedulerAgent:
    """
    调度器 Agent - 对应 K8s 中的 Scheduler 组件
    
    负责将 WaferLot（Pod）调度到合适的 ToolGroup（Node）上
    使用最少负载策略：选择 busy_tools 最少的 ToolGroup
    """
    
    def __init__(self, tool_groups: List[ToolGroup]):
        self.tool_groups = tool_groups
    
    def find_best_tool(self, tool_type: str) -> Optional[str]:
        """
        找到可用设备数最多的 ToolGroup（最少负载策略）
        
        Args:
            tool_type: 所需设备类型
        
        Returns:
            分配的设备名称（ToolGroup.name），若无可用设备则返回 None
        """
        # 筛选出匹配的 ToolGroup 且有可用设备
        candidates = [
            tg for tg in self.tool_groups 
            if tg.tool_type == tool_type and tg.available_tools > 0
        ]
        
        if not candidates:
            return None
        
        # 选择繁忙设备最少的 ToolGroup（最少负载）
        best_group = min(candidates, key=lambda tg: tg.busy_tools)
        
        # 更新设备状态：分配一个设备
        best_group.busy_tools += 1
        best_group.available_tools -= 1
        
        return best_group.name
    
    def release_tool(self, tool_name: str) -> None:
        """
        释放设备资源，将设备从繁忙状态改为可用状态
        
        Args:
            tool_name: 要释放的设备组名称
        """
        for tg in self.tool_groups:
            if tg.name == tool_name and tg.busy_tools > 0:
                tg.busy_tools -= 1
                tg.available_tools += 1
                break