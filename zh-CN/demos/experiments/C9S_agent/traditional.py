import time
import random
from typing import List, Dict
from models import WaferLot, ProcessStep


def run_traditional_pipeline(lots_data: List[Dict]) -> Dict:
    """
    传统命令式管道模式 - 与 K8s 声明式调谐循环对比
    
    特点：
    1. 固定顺序执行，无状态回退
    2. 同步阻塞等待每个步骤完成
    3. 失败立即终止，无重试机制
    4. 不考虑资源分配优化
    
    Args:
        lots_data: 批次数据列表（从 K8s 模式复制的初始状态）
    
    Returns:
        执行结果统计
    """
    results = []
    start_time = time.time()
    
    # 转换数据格式为内部使用
    lots = []
    for lot_data in lots_data:
        steps = []
        for i in range(lot_data.get("total_steps", 3)):
            # 根据索引生成对应的步骤类型
            step_types = ["Photolithography", "Etch", "Deposition", "Cleaning"]
            tool_type = step_types[i % len(step_types)]
            steps.append(ProcessStep(
                name=f"Step{i+1}-{tool_type}",
                tool_type=tool_type,
                duration_sec=3  # 每个步骤固定耗时3秒
            ))
        
        lots.append(WaferLot(
            id=lot_data["id"],
            product_type=lot_data.get("product_type", "Unknown"),
            steps=steps,
            steps_remaining=steps.copy(),
            current_step_index=0,
            status="pending",
            assigned_tool="",
            error_count=0,
            start_time=time.time()
        ))
    
    # 命令式执行：按顺序处理每个批次
    for lot in lots:
        lot.start_time = time.time()
        lot.status = "running"
        
        # 顺序执行每个步骤
        for step_index, step in enumerate(lot.steps):
            lot.current_step_index = step_index
            
            # 模拟步骤执行（同步等待）
            time.sleep(step.duration_sec)
            
            # 模拟随机失败（与 K8s 模式相同的失败概率）
            if random.random() < 0.1:
                lot.status = "failed"
                lot.error_count = 1
                lot.end_time = time.time()
                break
            
            # 更新进度
            lot.progress_percent = int((step_index + 1) / len(lot.steps) * 100)
        
        # 如果所有步骤都成功完成
        if lot.status == "running":
            lot.status = "completed"
            lot.end_time = time.time()
            lot.progress_percent = 100
        
        results.append({
            "id": lot.id,
            "product_type": lot.product_type,
            "status": lot.status,
            "error_count": lot.error_count,
            "duration": round(lot.end_time - lot.start_time, 2)
        })
    
    total_time = round(time.time() - start_time, 2)
    completed_count = sum(1 for r in results if r["status"] == "completed")
    failed_count = sum(1 for r in results if r["status"] == "failed")
    avg_duration = sum(r["duration"] for r in results) / len(results) if results else 0
    
    return {
        "results": results,
        "total_lots": len(results),
        "completed_lots": completed_count,
        "failed_lots": failed_count,
        "completion_rate": round(completed_count / len(results) * 100, 1) if results else 0,
        "failure_rate": round(failed_count / len(results) * 100, 1) if results else 0,
        "average_duration": round(avg_duration, 2),
        "total_execution_time": total_time
    }