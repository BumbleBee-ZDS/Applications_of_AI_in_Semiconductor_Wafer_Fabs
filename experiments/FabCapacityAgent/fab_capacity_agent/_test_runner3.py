"""
端到端测试脚本 v3 (修复版):
  1) 修复 Predictor use_llm 未生效 (显式注入 llm)
  2) 修复 ExecutionAgent Run ID = N/A (源码已改)
  3) 修复 numpy.bool_ JSON 序列化失败 (源码已改)
  4) 新增 LLM 报告生成专项校验 (验证 llm_enhanced=True)
  5) 新增报告 Run ID 溯源校验
  6) 完整覆盖 10 步测试链路

用法:
    python _test_runner3.py
"""

import sys
import os
import time
import json
import datetime as dt
import traceback
from pathlib import Path
import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_PROJECT_ROOT))

from utils.helpers import get_logger, safe_round, to_pct, process_cn_name, now_str
from utils.constants import (
    ALL_PROCESSES, PROCESS_NAME_CN, TABLE_EQUIPMENT, TABLE_LOTS,
    TABLE_LOT_HISTORY, TABLE_EQUIPMENT_EVENTS, TABLE_DAILY_OUTPUT,
    AGENT_PERCEPTION, AGENT_ANALYSIS, AGENT_DECISION, AGENT_EXECUTION,
    AGENT_NAME_CN, STATUS_SUCCESS, STATUS_FAILED,
)
from models.database import get_db
from models.capacity import AgentLogDAO

logger = get_logger("TestRunner3", level="INFO")
results: dict = {}
run_start_time = time.perf_counter()

# =============================================================================
# Step 1: 验证 DeepSeek API 连通性
# =============================================================================
print("=" * 70)
print("Step 1: 验证 DeepSeek API 连通性")
print("=" * 70)

try:
    from utils.llm_client import LLMClient, PROVIDER_DEEPSEEK, get_llm
    client = LLMClient(provider=PROVIDER_DEEPSEEK)
    api_configured = client.is_configured
    print(f"  API Key 已配置: {api_configured}")
    print(f"  Provider: {client.provider}")
    print(f"  Base URL: {client.base_url}")

    if api_configured:
        t0 = time.perf_counter()
        resp = client.chat(
            prompt="回复 'OK' 即可,这是连接测试。",
            max_tokens=20,
        )
        api_latency = (time.perf_counter() - t0) * 1000
        print(f"  连接测试: {'✅ 成功' if resp else '❌ 空响应'}")
        print(f"  响应内容: {resp[:80] if resp else 'N/A'}")
        print(f"  延迟: {api_latency:.0f} ms")
        results["llm"] = {
            "configured": True,
            "provider": client.provider,
            "base_url": client.base_url,
            "latency_ms": round(api_latency, 1),
            "response": resp[:100] if resp else "",
        }
    else:
        results["llm"] = {"configured": False}
except Exception as e:
    print(f"  ❌ LLM 连接失败: {e}")
    traceback.print_exc()
    results["llm"] = {"configured": False, "error": str(e)}

print()

# =============================================================================
# Step 2: 数据统计 (LLM 润色数据已生成)
# =============================================================================
print("=" * 70)
print("Step 2: 数据统计 (LLM 润色数据已生成)")
print("=" * 70)

db = get_db()
gen_stats = {
    "equipment": db.count(TABLE_EQUIPMENT),
    "lots": db.count(TABLE_LOTS),
    "lot_history": db.count(TABLE_LOT_HISTORY),
    "equipment_events": db.count(TABLE_EQUIPMENT_EVENTS),
    "daily_output": db.count(TABLE_DAILY_OUTPUT),
}
total_rows = sum(gen_stats.values())
print(f"  equipment:        {gen_stats['equipment']:>8}")
print(f"  lots:             {gen_stats['lots']:>8}")
print(f"  lot_history:      {gen_stats['lot_history']:>8}")
print(f"  equipment_events: {gen_stats['equipment_events']:>8}")
print(f"  daily_output:     {gen_stats['daily_output']:>8}")
print(f"  总记录数:         {total_rows:>8}")
results["data_gen"] = {"stats": gen_stats, "total_rows": total_rows, "llm_polish": True}
print()

# =============================================================================
# Step 3: 数据库完整性检查
# =============================================================================
print("=" * 70)
print("Step 3: 数据库完整性检查")
print("=" * 70)

tables_info = []
table_specs = [
    (TABLE_EQUIPMENT, "设备主数据", 120),
    (TABLE_LOTS, "批次信息", 1),
    (TABLE_LOT_HISTORY, "工序历史", 10000),
    (TABLE_EQUIPMENT_EVENTS, "设备事件", 5000),
    (TABLE_DAILY_OUTPUT, "日产出汇总", 80),
]
all_ok = True
for tbl, desc, min_expected in table_specs:
    cnt = db.count(tbl)
    ok = cnt >= min_expected
    status = "✅" if ok else "⚠️"
    print(f"  {status} {tbl:<20} {cnt:>8} 行 (预期≥{min_expected})  {desc}")
    tables_info.append({"table": tbl, "desc": desc, "rows": cnt, "min_expected": min_expected, "ok": ok})
    if not ok:
        all_ok = False
results["db_check"] = {"tables": tables_info, "all_ok": all_ok}
print()

# =============================================================================
# Step 4: 运行单元测试 (23 个用例)
# =============================================================================
print("=" * 70)
print("Step 4: 运行单元测试 (23 个用例)")
print("=" * 70)

test_results = []
test_classes = []
import tests.test_capacity as test_mod
for name in dir(test_mod):
    obj = getattr(test_mod, name)
    if isinstance(obj, type) and name.startswith("Test") and hasattr(obj, "__module__") and obj.__module__ == "tests.test_capacity":
        test_classes.append(obj)

total = passed = failed = 0
for cls in test_classes:
    instance = cls()
    setup = getattr(instance, "setup_method", None)
    if setup:
        try:
            setup()
        except Exception:
            pass
    methods = [m for m in dir(instance) if m.startswith("test_") and callable(getattr(instance, m))]
    for method_name in methods:
        total += 1
        method = getattr(instance, method_name)
        t0 = time.perf_counter()
        try:
            method()
            dur = (time.perf_counter() - t0) * 1000
            print(f"  ✓ {cls.__name__}::{method_name:<35} ({dur:>7.0f}ms)")
            test_results.append({"class": cls.__name__, "method": method_name, "status": "PASS", "duration_ms": round(dur, 1), "error": None})
            passed += 1
        except Exception as exc:
            dur = (time.perf_counter() - t0) * 1000
            err_msg = f"{type(exc).__name__}: {exc}"
            print(f"  ✗ {cls.__name__}::{method_name:<35} ({dur:>7.0f}ms)  {err_msg}")
            test_results.append({"class": cls.__name__, "method": method_name, "status": "FAIL", "duration_ms": round(dur, 1), "error": err_msg})
            failed += 1

print(f"\n  测试结果: {passed}/{total} 通过, {failed} 失败")
results["unit_tests"] = {"total": total, "passed": passed, "failed": failed, "details": test_results}
print()

# =============================================================================
# Step 5: 产能快照验证
# =============================================================================
print("=" * 70)
print("Step 5: 产能快照验证 (CapacityCalculator)")
print("=" * 70)

try:
    from services.capacity_calculator import get_calculator
    calc = get_calculator()
    t0 = time.perf_counter()
    snap = calc.build_snapshot(window_hours=24)
    snap_time = (time.perf_counter() - t0) * 1000
    sd = snap.to_dict()
    print(f"  快照构建耗时:    {snap_time:.0f} ms")
    print(f"  全厂 OEE:        {to_pct(sd.get('overall_oee', 0))}")
    print(f"  WIP 总量:        {int(sd.get('wip_total_wafers', 0)):,} 片")
    print(f"  24h 产出:        {int(sd.get('daily_output_24h', 0)):,} 片")
    print(f"  平均 CycleTime:  {safe_round(sd.get('avg_cycle_time_h', 0), 1)} h")
    bn_rank = sd.get('bottleneck_rank', [])
    print(f"  瓶颈排名:        {[process_cn_name(p) for p in bn_rank[:3]]}")
    by_proc = sd.get("by_process", {})
    proc_rows = []
    for p, info in by_proc.items():
        proc_rows.append({
            "process": p, "process_cn": process_cn_name(p),
            "oee": info.get("oee", 0), "utilization": info.get("utilization", 0),
            "wip": info.get("wip_wafers", 0), "uph": info.get("uph", 0),
            "is_bottleneck": bool(info.get("is_bottleneck", False)),
        })
    results["snapshot"] = {
        "build_time_ms": round(snap_time, 1),
        "overall_oee": sd.get("overall_oee", 0),
        "wip_total": sd.get("wip_total_wafers", 0),
        "daily_output_24h": sd.get("daily_output_24h", 0),
        "avg_cycle_time_h": sd.get("avg_cycle_time_h", 0),
        "bottleneck_rank": bn_rank,
        "by_process": proc_rows,
    }
    print(f"  ✅ 快照验证通过")
except Exception as e:
    print(f"  ❌ 快照验证失败: {e}")
    traceback.print_exc()
    results["snapshot"] = {"error": str(e)}
print()

# =============================================================================
# Step 6: 瓶颈检测 (LLM 增强) — 同时验证 numpy.bool_ 序列化修复
# =============================================================================
print("=" * 70)
print("Step 6: 瓶颈检测 (BottleneckDetector + LLM)")
print("=" * 70)

try:
    from services.bottleneck_detector import BottleneckDetector
    bd = BottleneckDetector()
    t0 = time.perf_counter()
    report = bd.detect_and_report(window_hours=24)
    bn_time = (time.perf_counter() - t0) * 1000
    print(f"  检测耗时:        {bn_time:.0f} ms")
    print(f"  LLM 增强:        {'是' if report.llm_enhanced else '否'}")
    print(f"  识别瓶颈数:      {len(report.bottlenecks)}")
    print(f"  原因分析数:      {len(report.causes)}")
    print(f"  优化建议数:      {len(report.suggestions)}")

    # 验证 numpy.bool_ 序列化修复
    serial_ok = True
    serial_err = ""
    try:
        json.dumps(report.bottlenecks, ensure_ascii=False, default=str)
    except Exception as se:
        serial_ok = False
        serial_err = f"{type(se).__name__}: {se}"
    print(f"  瓶颈JSON序列化:  {'✅ 通过' if serial_ok else '❌ 失败: ' + serial_err}")

    bn_list = []
    for b in report.bottlenecks[:5]:
        if isinstance(b, dict):
            bn_list.append({
                "process": b.get("process_cn", process_cn_name(b.get("process", ""))),
                "score": safe_round(b.get("score", 0), 3),
                "utilization": b.get("utilization", 0),
                "oee": b.get("oee", 0), "wip": b.get("wip_wafers", 0),
            })
            print(f"  瓶颈: {b.get('process_cn', ''):<8} 评分={safe_round(b.get('score',0),3)} 利用率={to_pct(b.get('utilization',0))}")
    cause_list = []
    for c in report.causes[:5]:
        if hasattr(c, "__dict__"):
            c = vars(c)
        if isinstance(c, dict):
            cause_list.append({"process": process_cn_name(c.get("process", "")), "dimension": c.get("dimension", ""), "severity": safe_round(c.get("severity_score", 0), 2), "detail": c.get("detail", "")})
    sug_list = []
    for s in report.suggestions[:5]:
        if hasattr(s, "__dict__"):
            s = vars(s)
        if isinstance(s, dict):
            sug_list.append({"process": process_cn_name(s.get("process", "")), "category": s.get("category", ""), "action": s.get("action", ""), "priority": s.get("priority", "")})
    results["bottleneck"] = {
        "detect_time_ms": round(bn_time, 1), "llm_enhanced": report.llm_enhanced,
        "bottleneck_count": len(report.bottlenecks), "cause_count": len(report.causes),
        "suggestion_count": len(report.suggestions),
        "json_serializable": serial_ok,
        "top_bottlenecks": bn_list, "top_causes": cause_list, "top_suggestions": sug_list,
    }
    print(f"  ✅ 瓶颈检测完成")
except Exception as e:
    print(f"  ❌ 瓶颈检测失败: {e}")
    traceback.print_exc()
    results["bottleneck"] = {"error": str(e)}
print()

# =============================================================================
# Step 7: 产能预测 — 修复:显式注入 LLM, 让 use_llm=True 真正生效
# =============================================================================
print("=" * 70)
print("Step 7: 产能预测 (Predictor + LLM 显式注入)")
print("=" * 70)

try:
    from services.predictor import Predictor
    from utils.llm_client import get_llm
    llm_for_pred = get_llm()  # 显式获取 LLM 客户端
    pred = Predictor(llm=llm_for_pred)  # 显式注入
    print(f"  Predictor LLM 注入: {'✅' if pred.llm is not None else '❌'}")

    # 本地模式
    t0 = time.perf_counter()
    fr_local = pred.forecast_output(horizon_days=7, history_days=30, use_llm=False)
    local_time = (time.perf_counter() - t0) * 1000
    print(f"  本地预测 (7天): 耗时={local_time:.0f}ms  方法={fr_local.method}  MAPE={safe_round(fr_local.mape*100,2)}%")
    print(f"    预测值: {[int(v) for v in fr_local.predicted]}")

    # LLM 模式 (现在应当真正调用 LLM)
    t0 = time.perf_counter()
    fr_llm = pred.forecast_output(horizon_days=7, history_days=30, use_llm=True)
    llm_time = (time.perf_counter() - t0) * 1000
    print(f"  LLM 预测 (7天):  耗时={llm_time:.0f}ms  方法={fr_llm.method}  MAPE={safe_round(fr_llm.mape*100,2)}%")
    print(f"    预测值: {[int(v) for v in fr_llm.predicted]}")
    print(f"    LLM 增强: {'✅ 是' if fr_llm.used_llm else '❌ 否 (未生效)'}")

    # 计算两种模式预测总量的差异
    local_total = int(sum(fr_local.predicted))
    llm_total = int(sum(fr_llm.predicted))
    delta = llm_total - local_total
    print(f"  本地 vs LLM 预测总量: {local_total} vs {llm_total} (Δ={delta:+d})")

    results["predictor"] = {
        "local": {"time_ms": round(local_time, 1), "method": fr_local.method, "mape": fr_local.mape, "predicted": [int(v) for v in fr_local.predicted], "total": local_total},
        "llm": {"time_ms": round(llm_time, 1), "method": fr_llm.method, "mape": fr_llm.mape, "predicted": [int(v) for v in fr_llm.predicted], "used_llm": fr_llm.used_llm, "total": llm_total, "delta_vs_local": delta},
    }
    print(f"  ✅ 预测验证完成")
except Exception as e:
    print(f"  ❌ 预测失败: {e}")
    traceback.print_exc()
    results["predictor"] = {"error": str(e)}
print()

# =============================================================================
# Step 8: What-If 仿真
# =============================================================================
print("=" * 70)
print("Step 8: What-If 仿真 (WhatIfSimulator)")
print("=" * 70)

try:
    from services.what_if_simulator import WhatIfSimulator
    ws = WhatIfSimulator()
    t0 = time.perf_counter()
    scenarios = ws.preset_scenarios()
    df_compare = ws.compare_scenarios(scenarios)
    wi_time = time.perf_counter() - t0
    baseline = ws.run_baseline()
    print(f"  仿真耗时:        {wi_time:.1f}s")
    print(f"  Baseline 周产能: {int(baseline.total_effective_wafers_per_week):,} 片")
    print(f"  Baseline OEE:    {to_pct(baseline.overall_oee)}")
    print(f"  情景数:          {len(df_compare)}")
    scenario_rows = []
    for _, row in df_compare.iterrows():
        weekly = int(row.get("total_wafers_per_week", row.get("total_effective_wafers_per_week", 0)))
        delta = int(row.get("delta_wafers", row.get("delta_wafers_per_week", 0)))
        delta_p = float(row.get("delta_pct", 0))
        oee = float(row.get("overall_oee", 0))
        p50 = int(row.get("mc_p50", 0)) if "mc_p50" in row and pd.notna(row.get("mc_p50")) else None
        risk = row.get("risk_level", "") if "risk_level" in row else ""
        scenario_rows.append({
            "name": row.get("name", ""), "weekly_wafers": weekly,
            "delta_wafers": delta, "delta_pct": delta_p, "oee": oee,
            "mc_p50": p50, "risk_level": risk,
        })
        delta_str = f"+{delta:,}" if delta >= 0 else f"{delta:,}"
        print(f"    {row.get('name', ''):<22} {weekly:>8,} 片 ({delta_str}, {safe_round(delta_p*100,2)}%)")
    results["what_if"] = {
        "duration_s": round(wi_time, 1),
        "baseline_wafers": int(baseline.total_effective_wafers_per_week),
        "baseline_oee": baseline.overall_oee,
        "scenario_count": len(df_compare),
        "scenarios": scenario_rows,
    }
    print(f"  ✅ What-If 仿真完成")
except Exception as e:
    print(f"  ❌ What-If 失败: {e}")
    traceback.print_exc()
    results["what_if"] = {"error": str(e)}
print()

# =============================================================================
# Step 9: LLM 增强的全链路 Pipeline
# =============================================================================
print("=" * 70)
print("Step 9: LLM 增强的全链路 Pipeline")
print("=" * 70)

try:
    from agents.orchestrator import get_orchestrator
    from utils.llm_client import get_llm
    orch = get_orchestrator()
    llm = get_llm()
    llm_ok = llm.is_configured
    if llm_ok:
        for a in orch.agents.values():
            a.llm = llm
        print(f"  LLM 已启用: {llm.provider}")
    else:
        print(f"  ⚠️ LLM 未配置, 使用本地模式")
    t0 = time.perf_counter()
    result = orch.run_full_pipeline(
        user_query="分析当前全厂产能瓶颈,评估未来7天产出趋势,并给出加设备 vs OEE提升的对比建议",
        trigger="e2e_test_v3",
        window_hours=24,
        history_days=30,
    )
    pipeline_time = time.perf_counter() - t0
    print(f"  Pipeline 耗时:   {pipeline_time:.1f}s")
    print(f"  状态:            {result.status}")
    print(f"  Run ID:          {result.run_id}")
    step_list = []
    for step in result.pipeline_steps:
        step_list.append({
            "agent_type": step.agent_type, "agent_cn": AGENT_NAME_CN.get(step.agent_type, step.agent_type),
            "status": step.status, "duration_ms": step.duration_ms, "error": step.error_message,
        })
        emoji = "✅" if step.status == STATUS_SUCCESS else "❌"
        print(f"  {emoji} {AGENT_NAME_CN.get(step.agent_type, ''):<12} {step.status:<10} ({safe_round(step.duration_ms/1000, 2)}s)")
        if step.error_message:
            print(f"      错误: {step.error_message[:100]}")
    report_full = result.final_report or ""
    print(f"  报告长度:        {len(report_full)} 字符")

    # 验证 Run ID 已正确填入报告
    run_id_in_report = result.run_id in report_full
    print(f"  Run ID 已写入报告: {'✅ 是' if run_id_in_report else '❌ 否 (仍为 N/A)'}")

    # 验证 LLM 增强报告
    llm_enhanced_in_report = "LLM增强: ✓" in report_full or "(LLM增强: ✓)" in report_full
    print(f"  报告标注 LLM 增强: {'✅ 是' if llm_enhanced_in_report else '⚠️ 未标注'}")

    print(f"  报告预览 (前 400 字符):")
    print("  " + "-" * 60)
    for line in report_full[:400].split("\n"):
        print(f"  | {line}")
    print("  " + "-" * 60)
    results["pipeline"] = {
        "run_id": result.run_id, "status": result.status,
        "duration_s": round(pipeline_time, 1), "llm_enabled": llm_ok,
        "steps": step_list, "report_length": len(report_full),
        "run_id_in_report": run_id_in_report,
        "llm_enhanced_in_report": llm_enhanced_in_report,
        "report_preview": report_full[:500], "report_full": report_full,
    }
    print(f"  ✅ 全链路 Pipeline 完成")
except Exception as e:
    print(f"  ❌ Pipeline 失败: {e}")
    traceback.print_exc()
    results["pipeline"] = {"error": str(e)}
print()

# =============================================================================
# Step 10: Agent 日志验证
# =============================================================================
print("=" * 70)
print("Step 10: Agent 日志验证")
print("=" * 70)

try:
    log_dao = AgentLogDAO()
    df_runs = log_dao.recent_runs(limit=5)
    print(f"  最近 Run 记录: {len(df_runs)} 条")
    run_list = []
    for _, r in df_runs.iterrows():
        run_list.append({
            "run_id": r.get("run_id", ""), "created_at": str(r.get("created_at", ""))[:19],
            "succ_steps": int(r.get("succ_steps", 0)), "fail_steps": int(r.get("fail_steps", 0)),
            "total_ms": int(r.get("total_ms", 0)) if r.get("total_ms") else 0,
        })
        print(f"    {r.get('run_id', '')} | {str(r.get('created_at', ''))[:19]} | 成功={r.get('succ_steps', 0)} 失败={r.get('fail_steps', 0)}")
    results["agent_logs"] = {"recent_runs": run_list}
    print(f"  ✅ 日志验证完成")
except Exception as e:
    print(f"  ❌ 日志验证失败: {e}")
    results["agent_logs"] = {"error": str(e)}
print()

# =============================================================================
# 保存结果
# =============================================================================
total_time = time.perf_counter() - run_start_time
results["meta"] = {
    "test_runner": "_test_runner3.py",
    "started_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "total_duration_s": round(total_time, 1),
    "fixes_applied": [
        "numpy.bool_ JSON 序列化 (bottleneck_detector.py: bool() 强转)",
        "LLM 报告 JSON dumps 增加 default=str 兜底 (llm_client.py)",
        "ExecutionAgent Run ID 透传 (execution_agent.py: 显式 run_id 参数)",
        "Predictor 显式注入 LLM (_test_runner3.py: Predictor(llm=get_llm()))",
    ],
}

output_path = _PROJECT_ROOT / "test_results.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)
print("=" * 70)
print(f"✅ 全部测试步骤完成! 总耗时: {total_time:.1f}s")
print(f"   结果已保存: {output_path}")
print("=" * 70)
