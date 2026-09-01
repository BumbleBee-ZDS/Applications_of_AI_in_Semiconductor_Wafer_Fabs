import time
import random
import logging
from threading import Thread, RLock
from typing import Dict, List
from models import WaferLot, ToolGroup, ProcessStep
from scheduler import SchedulerAgent


class FabController:
    """
    晶圆厂控制器 - 对应 K8s 中的 Controller Manager + Kubelet
    
    运行调谐循环（Reconcile Loop），持续观察当前状态，与期望状态对比，
    执行必要操作使系统收敛到期望状态（所有 Lot 完成）
    
    K8s 控制论思想体现：
    1. 声明式期望状态：所有 WaferLot 的期望状态都是 completed
    2. 调谐循环：每 2 秒运行一次 reconcile() 函数
    3. 观察-决策-执行：扫描状态 -> 计算差异 -> 执行操作
    4. 自愈能力：失败自动重试（最多3次），超过阈值标记失败
    """
    
    # 失败重试最大次数
    MAX_RETRY_COUNT = 3
    # 步骤失败概率（模拟设备故障）
    FAILURE_PROBABILITY = 0.1
    
    def __init__(self):
        # 全局状态存储 - 对应 K8s etcd
        self.lots: Dict[str, WaferLot] = {}
        self.tool_groups: List[ToolGroup] = []
        self.logs: List[Dict] = []
        self._sample_initialized = False
        
        # 线程锁 - 保证并发安全（使用可重入锁支持嵌套调用）
        self.lock = RLock()
        
        # 调度器 - 对应 K8s Scheduler
        self.scheduler = None
        
        # 步骤耗时追踪（用于模拟时间流逝）
        self.step_start_time: Dict[str, float] = {}
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def init_tool_groups(self):
        """
        初始化设备组 - 对应 K8s 集群初始化时注册 Node
        
        创建模拟的半导体晶圆厂设备：
        - 光刻设备组（Photolithography）：2台
        - 刻蚀设备组（Etch）：3台
        - 沉积设备组（Deposition）：2台
        - 清洗设备组（Cleaning）：2台
        """
        self.tool_groups = [
            ToolGroup(name="Photolithography-Group-A", tool_type="Photolithography", available_tools=2, busy_tools=0),
            ToolGroup(name="Etch-Group-A", tool_type="Etch", available_tools=3, busy_tools=0),
            ToolGroup(name="Deposition-Group-A", tool_type="Deposition", available_tools=2, busy_tools=0),
            ToolGroup(name="Cleaning-Group-A", tool_type="Cleaning", available_tools=2, busy_tools=0),
        ]
        self.scheduler = SchedulerAgent(self.tool_groups)
        self.add_log("INFO", "设备组初始化完成", "Controller")
    
    def add_log(self, level: str, message: str, source: str):
        """
        添加日志记录 - 对应 K8s Events
        
        Args:
            level: 日志级别（INFO/WARNING/ERROR）
            message: 日志内容
            source: 来源组件
        """
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "message": message,
            "source": source
        }
        with self.lock:
            self.logs.append(log_entry)
            # 保留最近 50 条日志
            if len(self.logs) > 50:
                self.logs = self.logs[-50:]
        
        # 同时输出到控制台
        if level == "INFO":
            self.logger.info(f"[{source}] {message}")
        elif level == "WARNING":
            self.logger.warning(f"[{source}] {message}")
        elif level == "ERROR":
            self.logger.error(f"[{source}] {message}")
    
    def add_lot(self, lot: WaferLot):
        """
        添加新批次到系统 - 对应 K8s 创建 Pod
        
        Args:
            lot: 要添加的 WaferLot 对象
        """
        with self.lock:
            self.lots[lot.id] = lot
            lot.start_time = time.time()
        self.add_log("INFO", f"新批次创建: {lot.id} ({lot.product_type})", "Controller")
    
    def remove_lot(self, lot_id: str) -> bool:
        """
        移除批次 - 对应 K8s 删除 Pod
        
        Args:
            lot_id: 要移除的批次 ID
        
        Returns:
            是否成功移除
        """
        with self.lock:
            if lot_id in self.lots:
                lot = self.lots[lot_id]
                # 如果正在运行，释放设备
                if lot.status == "running" and lot.assigned_tool:
                    self.scheduler.release_tool(lot.assigned_tool)
                del self.lots[lot_id]
                self.add_log("INFO", f"批次已删除: {lot_id}", "Controller")
                return True
            return False
    
    def reconcile(self):
        """
        调谐循环核心函数 - 对应 K8s Controller Reconcile
        
        执行"观察-决策-执行"循环：
        1. 观察：扫描所有 WaferLot 的当前状态
        2. 决策：对比期望状态（completed），计算需要执行的操作
        3. 执行：分配设备、模拟时间流逝、处理失败、推进步骤
        """
        with self.lock:
            active_lots = [lot for lot in self.lots.values() if lot.status not in ["completed", "failed"]]
            if active_lots:
                self.logger.info(f"[Reconcile] 扫描到 {len(active_lots)} 个活跃批次")
            
            for lot_id, lot in list(self.lots.items()):
                # 跳过已完成或已失败的批次
                if lot.status in ["completed", "failed"]:
                    continue
                
                self._reconcile_lot(lot)
    
    def _reconcile_lot(self, lot: WaferLot):
        """
        单个批次的调谐逻辑 - 对应 K8s Kubelet 管理单个 Pod
        
        Args:
            lot: 要调谐的 WaferLot
        """
        # ========== 阶段1：观察当前状态 ==========
        current_status = lot.status
        
        # 如果索引越界，说明批次已经完成，跳过处理
        if lot.current_step_index >= len(lot.steps):
            return
        
        current_step = lot.steps[lot.current_step_index]
        
        # ========== 阶段2：决策与执行 ==========
        
        # Case 1: pending 状态 - 需要分配设备启动执行
        if current_status == "pending":
            self._handle_pending(lot, current_step)
        
        # Case 2: running 状态 - 检查是否完成当前步骤
        elif current_status == "running":
            self._handle_running(lot, current_step)
    
    def _handle_pending(self, lot: WaferLot, step: ProcessStep):
        """
        处理 pending 状态的批次 - 对应 K8s Pod 调度阶段
        
        尝试分配设备，分配成功则转为 running 状态
        """
        # 调用调度器分配设备（对应 K8s Scheduler）
        tool_name = self.scheduler.find_best_tool(step.tool_type)
        
        if tool_name:
            lot.assigned_tool = tool_name
            lot.status = "running"
            self.step_start_time[lot.id] = time.time()
            self.add_log("INFO", f"批次 {lot.id} 已分配设备 {tool_name}，开始执行 {step.name}", "Scheduler")
        else:
            self.add_log("WARNING", f"批次 {lot.id} 等待设备: {step.tool_type} 暂无可用", "Scheduler")
    
    def _handle_running(self, lot: WaferLot, step: ProcessStep):
        """
        处理 running 状态的批次 - 对应 K8s Kubelet 监控 Pod
        
        模拟时间流逝，检查步骤是否完成，处理失败情况
        """
        elapsed = time.time() - self.step_start_time[lot.id]
        
        # 检查步骤是否完成
        if elapsed >= step.duration_sec:
            # 步骤完成，模拟随机失败
            if random.random() < self.FAILURE_PROBABILITY:
                self._handle_step_failure(lot, step)
            else:
                self._handle_step_success(lot, step)
        else:
            # 更新进度
            progress = int((elapsed / step.duration_sec) * 100)
            total_progress = int((lot.current_step_index / len(lot.steps)) * 100 + progress / len(lot.steps))
            lot.progress_percent = min(total_progress, 99)
    
    def _handle_step_success(self, lot: WaferLot, step: ProcessStep):
        """
        处理步骤执行成功 - 推进到下一步或标记完成
        
        Args:
            lot: WaferLot 对象
            step: 刚完成的步骤
        """
        # 释放当前设备
        self.scheduler.release_tool(lot.assigned_tool)
        self.add_log("INFO", f"批次 {lot.id} 完成步骤 {step.name}", "Worker")
        
        # 推进到下一步
        lot.current_step_index += 1
        
        # 检查是否所有步骤都完成
        if lot.current_step_index >= len(lot.steps):
            lot.status = "completed"
            lot.end_time = time.time()
            lot.progress_percent = 100
            lot.assigned_tool = ""
            self.add_log("INFO", f"批次 {lot.id} 全部完成!", "Controller")
        else:
            # 进入下一步，重置为 pending 等待重新调度
            lot.status = "pending"
            lot.assigned_tool = ""
    
    def _handle_step_failure(self, lot: WaferLot, step: ProcessStep):
        """
        处理步骤执行失败 - 实现自愈能力
        
        Args:
            lot: WaferLot 对象
            step: 失败的步骤
        """
        lot.error_count += 1
        self.add_log("ERROR", f"批次 {lot.id} 步骤 {step.name} 失败，重试次数: {lot.error_count}/{self.MAX_RETRY_COUNT}", "Worker")
        
        # 释放当前设备
        self.scheduler.release_tool(lot.assigned_tool)
        
        # 判断是否继续重试
        if lot.error_count < self.MAX_RETRY_COUNT:
            # 自愈：重置为 pending 状态等待重新调度
            lot.status = "pending"
            lot.assigned_tool = ""
            self.add_log("INFO", f"批次 {lot.id} 将进行第 {lot.error_count} 次重试", "Controller")
        else:
            # 超过最大重试次数，标记为失败
            lot.status = "failed"
            lot.end_time = time.time()
            lot.assigned_tool = ""
            self.add_log("ERROR", f"批次 {lot.id} 达到最大重试次数，标记为失败", "Controller")
    
    def start_reconcile_loop(self, interval: int = 2):
        """
        启动调谐循环后台线程 - 对应 K8s Controller Manager 启动
        
        Args:
            interval: 调谐循环间隔（秒）
        """
        def loop():
            while True:
                try:
                    self.reconcile()
                except Exception as e:
                    self.logger.error(f"调谐循环异常: {e}")
                time.sleep(interval)
        
        # 创建守护线程，主进程退出时自动终止
        t = Thread(target=loop, daemon=True)
        t.start()
        self.add_log("INFO", f"调谐循环已启动，间隔 {interval} 秒", "Controller")
    
    def get_lots(self) -> List[Dict]:
        """
        获取所有批次的状态列表（用于 API 返回）
        
        Returns:
            批次列表，每个批次转换为字典
        """
        with self.lock:
            result = []
            for lot in self.lots.values():
                # 获取当前步骤名称，处理完成状态时索引越界的情况
                if lot.status == "completed":
                    current_step_name = lot.steps[-1].name if lot.steps else "Completed"
                    step_index = len(lot.steps)
                else:
                    current_step_name = lot.steps[lot.current_step_index].name if lot.steps and lot.current_step_index < len(lot.steps) else ""
                    step_index = lot.current_step_index
                
                result.append({
                    "id": lot.id,
                    "product_type": lot.product_type,
                    "current_step": current_step_name,
                    "current_step_index": step_index,
                    "total_steps": len(lot.steps),
                    "status": lot.status,
                    "assigned_tool": lot.assigned_tool,
                    "error_count": lot.error_count,
                    "progress_percent": lot.progress_percent,
                    "duration": round(lot.end_time - lot.start_time, 2) if lot.end_time else 0
                })
            return result
    
    def get_tools(self) -> List[Dict]:
        """
        获取所有设备组状态（用于 API 返回）
        
        Returns:
            设备组列表，每个转换为字典
        """
        with self.lock:
            result = []
            for tg in self.tool_groups:
                result.append({
                    "name": tg.name,
                    "tool_type": tg.tool_type,
                    "available_tools": tg.available_tools,
                    "busy_tools": tg.busy_tools,
                    "total_tools": tg.total_tools,
                    "utilization": round(tg.utilization * 100, 1)
                })
            return result
    
    def get_logs(self) -> List[Dict]:
        """
        获取最近的日志列表
        
        Returns:
            日志列表
        """
        with self.lock:
            return list(self.logs[-10:])  # 返回最近10条
    
    def get_metrics(self) -> Dict:
        """
        获取统计指标
        
        Returns:
            包含总批次、完成率、平均耗时、失败率等指标的字典
        """
        with self.lock:
            total = len(self.lots)
            completed = sum(1 for lot in self.lots.values() if lot.status == "completed")
            failed = sum(1 for lot in self.lots.values() if lot.status == "failed")
            running = sum(1 for lot in self.lots.values() if lot.status == "running")
            
            avg_duration = 0
            if completed > 0:
                avg_duration = sum(
                    lot.end_time - lot.start_time 
                    for lot in self.lots.values() 
                    if lot.status == "completed"
                ) / completed
            
            return {
                "total_lots": total,
                "completed_lots": completed,
                "failed_lots": failed,
                "running_lots": running,
                "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
                "failure_rate": round(failed / total * 100, 1) if total > 0 else 0,
                "average_duration": round(avg_duration, 2)
            }