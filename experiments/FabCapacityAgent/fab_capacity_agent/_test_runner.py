"""
端到端测试脚本: 用 DeepSeek LLM 生成数据 → 运行单元测试 → 运行全链路 Pipeline → 收集结果
生成 TEST_REPORT.md 所需的全部数据。
"""
import sys, os, time, json, datetime as dt, traceback
from pathlib import Path

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

logger = get_logger("TestRunner", level="INFO")

results = {}

# =============================================================================
# Step 1: 验证 DeepSeek API 连通性
# =============================================================================
print("=" * 70)
print("Step 1: 验证 DeepSeek API 连通性")
print("=" * 70)

try:
    from utils.llm_client import LLMClient, PROVIDER_DEEPSEEK
    client = LLMClient(provider=PROVIDER_DEEPSEEK)
    api_configured = client.is_configured()
    print(f"  API Key 已配置: {api_configured}")
    print(f"  Provider: {client.provider}")
    print(f"  Model: {getattr(client, 'model', 'N/A')}")

    if api_configured:
        t0 = time.perf_counter()
        resp = client.chat(
            messages=[{"role": "user", "content": "回复 'OK' 即可,这是连接测试。"}],
            max_tokens=20,
        )
        api_latency = (time.perf_counter() - t0) * 1000
        print(f"  连接测试: {'✅ 成功' if resp else '❌ 空响应'}")
        print(f"  响应内容: {resp[:80] if resp else 'N/A'}")
        print(f"  延迟: {api_latency:.0f} ms")
        results["llm"] = {
            "configured": True,
            "provider": client.provider,
            "model": getattr(client, 'model', 'N/A'),
            "latency_ms": round(api_latency, 1),
            "response": resp[:100] if resp else "",
        }
    else:
        print("  ⚠️ API Key 未配置,跳过 LLM 测试")
        results["llm"] = {"configured": False}
except Exception as e:
    print(f"  ❌ LLM 连接失败: {e}")
    traceback.print_exc()
    results["llm"] = {"configured": False, "error": str(e)}

print()

# =============================================================================
# Step 2: 用 LLM 润色重新生成测试数据
# =============================================================================
print("=" * 70)
print("Step 2: 用 DeepSeek LLM 润色重新生成测试数据")
print("=" * 70)

try:
    from data.generator import MESDataGenerator
    t0 = time.perf_counter()
    gen = MESDataGenerator(
        history_days=90,
        lots_per_day=60,
        seed=42,
        use_llm_polish=True,
    )
    gen.run(force=True)
    gen_time = time.perf_counter() - t0
    stats = getattr(gen, "stats", {})
    print(f"  ✅ 数据生成完成 (耗时 {gen_time:.1f}s)")
    print(f"  设备数: {stats.get('equipment', 'N/A')}")
    print(f"  批次数: {stats.get('lots', 'N/A')}")
    print(f"  工序历史: {stats.get('lot_history', 'N/A')}")
    print(f"  设备事件: {stats.get('equipment_events', 'N/A')}")
    print(f"  日产出: {stats.get('daily_output', 'N/A')}")
    results["data_gen"] = {
        "duration_s": round(gen_time, 1),
        "stats": stats,
        "llm_polish": True,
    }
except Exception as e:
    print(f"  ❌ 数据生成失败: {e}")
    traceback.print_exc()
    results["data_gen"] = {"error": str(e)}

print()

# =============================================================================
# Step 3: 数据库完整性检查
# =============================================================================
print("=" * 70)
print("Step 3: 数据库完整性检查")
print("=" * 70)

try:
    db = get_db()
    tables_info = []
    table_specs = [
        (TABLE_EQUIPMENT, "设备主数据", 120),
        (TABLE_LOTS, "批次信息", None),
        (TABLE_LOT_HISTORY, "工序历史", 50000),
        (TABLE_EQUIPMENT_EVENTS, "设备事件", 5000),
        (TABLE_DAILY_OUTPUT, "日产出汇总", 80),
    ]
    all_ok = True
    for tbl, desc, min_expected in table_specs:
        cnt = db.count(tbl)
        ok = cnt > 0 and (min_expected is None or cnt >= min_expected)
        status = "✅" if ok else "⚠️"
        min_str = f" (预期≥{min_expected})" if min_expected else ""
        print(f"  {status} {tbl}: {cnt} 行{min_str}")
        tables_info.append({"table": tbl, "desc": desc, "rows": cnt, "min_expected": min_expected, "ok": ok})
        if not ok:
            all_ok = False
    results["db_check"] = {"tables": tables_info, "all_ok": all_ok}
except Exception as e:
    print(f"  ❌ 数据库检查失败: {e}")
    results["db_check"] = {"error": str(e)}

print()

# =============================================================================
# Step 4: 运行单元测试
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

total = 0
passed = 0
failed = 0
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
            print(f"  ✓ {cls.__name__}::{method_name}  ({dur:.0f}ms)")
            test_results.append({
                "class": cls.__name__, "method": method_name,
                "status": "PASS", "duration_ms": round(dur, 1), "error": None,
            })
            passed += 1
        except Exception as exc:
            dur = (time.perf_counter() - t0) * 1000
            err_msg = f"{type(exc).__name__}: {exc}"
            print(f"  ✗ {cls.__name__}::{method_name}  ({dur:.0f}ms)")
            print(f"      {err_msg}")
            test_results.append({
                "class": cls.__name__, "method": method_name,
                "status": "FAIL", "duration_ms": round(dur, 1), "error": err_msg,
            })
            failed += 1

print(f"\n  测试结果: {passed}/{total} 通过, {failed} 失败")
results["unit_tests"] = {
    "total": total, "passed": passed, "failed": failed,
    "details": test_results,
}
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

    print(f"  快照构建耗时: {snap_time:.0f} ms")
    print(f"  全厂 OEE: {to_pct(sd.get('overall_oee', 0))}")
    print(f"  WIP 总量: {int(sd.get('wip_total_wafers', 0)):,} 片")
    print(f"  24h 产出: {int(sd.get('daily_output_24h', 0)):,} 片")
    print(f"  平均 CycleTime: {safe_round(sd.get('avg_cycle_time_h', 0), 1)} h")
    print(f"  瓶颈排名: {[process_cn_name(p) for p in sd.get('bottleneck_rank', [])[:3]]}")

    # 工序明细
    by_proc = sd.get("by_process", {})
    proc_rows = []
    for p, info in by_proc.items():
        proc_rows.append({
            "process": p,
            "process_cn": process_cn_name(p),
            "oee": info.get("oee", 0),
            "utilization": info.get("utilization", 0),
            "wip": info.get("wip_wafers", 0),
            "uph": info.get("uph", 0),
            "is_bottleneck": info.get("is_bottleneck", False),
        })

    results["snapshot"] = {
        "build_time_ms": round(snap_time, 1),
        "overall_oee": sd.get("overall_oee", 0),
        "wip_total": sd.get("wip_total_wafers", 0),
        "daily_output_24h": sd.get("daily_output_24h", 0),
        "avg_cycle_time_h": sd.get("avg_cycle_time_h", 0),
        "bottleneck_rank": sd.get("bottleneck_rank", []),
        "by_process": proc_rows,
    }
    print(f"  ✅ 快照验证通过")
except Exception as e:
    print(f"  ❌ 快照验证失败: {e}")
    traceback.print_exc()
    results["snapshot"] = {"error": str(e)}

print()

# =============================================================================
# Step 6: 瓶颈检测
# =============================================================================
print("=" * 70)
print("Step 6: 瓶颈检测 (BottleneckDetector)")
print("=" * 70)

try:
    from services.bottleneck_detector import BottleneckDetector
    bd = BottleneckDetector()
    t0 = time.perf_counter()
    report = bd.detect_and_report(window_hours=24)
    bn_time = (time.perf_counter() - t0) * 1000

    print(f"  检测耗时: {bn_time:.0f} ms")
    print(f"  LLM 增强: {'是' if report.llm_enhanced else '否'}")
    print(f"  识别瓶颈数: {len(report.bottlenecks)}")
    print(f"  原因分析数: {len(report.causes)}")
    print(f"  优化建议数: {len(report.suggestions)}")

    bn_list = []
    for b in report.bottlenecks[:5]:
        if isinstance(b, dict):
            bn_list.append({
                "process": b.get("process_cn", process_cn_name(b.get("process", ""))),
                "score": safe_round(b.get("score", 0), 3),
                "utilization": b.get("utilization", 0),
                "oee": b.get("oee", 0),
                "wip": b.get("wip_wafers", 0),
            })
            print(f"  瓶颈: {b.get('process_cn', '')} 评分={safe_round(b.get('score',0),3)} 利用率={to_pct(b.get('utilization',0))}")

    cause_list = []
    for c in report.causes[:5]:
        if hasattr(c, "__dict__"):
            c = vars(c)
        if isinstance(c, dict):
            cause_list.append({
                "process": process_cn_name(c.get("process", "")),
                "dimension": c.get("dimension", ""),
                "severity": safe_round(c.get("severity_score", 0), 2),
                "detail": c.get("detail", ""),
            })

    sug_list = []
    for s in report.suggestions[:5]:
        if hasattr(s, "__dict__"):
            s = vars(s)
        if isinstance(s, dict):
            sug_list.append({
                "process": process_cn_name(s.get("process", "")),
                "category": s.get("category", ""),
                "action": s.get("action", ""),
                "priority": s.get("priority", ""),
            })

    results["bottleneck"] = {
        "detect_time_ms": round(bn_time, 1),
        "llm_enhanced": report.llm_enhanced,
        "bottleneck_count": len(report.bottlenecks),
        "cause_count": len(report.causes),
        "suggestion_count": len(report.suggestions),
        "top_bottlenecks": bn_list,
        "top_causes": cause_list,
        "top_suggestions": sug_list,
    }
    print(f"  ✅ 瓶颈检测完成")
except Exception as e:
    print(f"  ❌ 瓶颈检测失败: {e}")
    traceback.print_exc()
    results["bottleneck"] = {"error": str(e)}

print()

# =============================================================================
# Step 7: 产能预测
# =============================================================================
print("=" * 70)
print("Step 7: 产能预测 (Predictor)")
print("=" * 70)

try:
    from services.predictor import Predictor
    pred = Predictor()

    # 本地模式
    t0 = time.perf_counter()
    fr_local = pred.forecast_output(horizon_days=7, history_days=30, use_llm=False)
    local_time = (time.perf_counter() - t0) * 1000
    print(f"  本地预测 (7天): 耗时={local_time:.0f}ms  方法={fr_local.method}  MAPE={safe_round(fr_local.mape*100,2)}%")
    print(f"    预测值: {[int(v) for v in fr_local.predicted]}")

    # LLM 模式
    t0 = time.perf_counter()
    fr_llm = pred.forecast_output(horizon_days=7, history_days=30, use_llm=True)
    llm_time = (time.perf_counter() - t0) * 1000
    print(f"  LLM 预测 (7天): 耗时={llm_time:.0f}ms  方法={fr_llm.method}  MAPE={safe_round(fr_llm.mape*100,2)}%")
    print(f"    预测值: {[int(v) for v in fr_llm.predicted]}")
    print(f"    LLM 增强: {'是' if fr_llm.used_llm else '否'}")

    results["predictor"] = {
        "local": {
            "time_ms": round(local_time, 1),
            "method": fr_local.method,
            "mape": fr_local.mape,
            "predicted": [int(v) for v in fr_local.predicted],
        },
        "llm": {
            "time_ms": round(llm_time, 1),
            "method": fr_llm.method,
            "mape": fr_llm.mape,
            "predicted": [int(v) for v in fr_llm.predicted],
            "used_llm": fr_llm.used_llm,
        },
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
    print(f"  仿真耗时: {wi_time:.1f}s")
    print(f"  Baseline 周产能: {int(baseline.total_effective_wafers_per_week):,} 片")
    print(f"  Baseline OEE: {to_pct(baseline.overall_oee)}")
    print(f"  情景数: {len(df_compare)}")

    scenario_rows = []
    for _, row in df_compare.iterrows():
        scenario_rows.append({
            "name": row.get("name", ""),
            "weekly_wafers": int(row.get("total_effective_wafers_per_week", 0)),
            "delta_wafers": int(row.get("delta_wafers_per_week", 0)),
            "delta_pct": float(row.get("delta_pct", 0)),
            "oee": float(row.get("overall_oee", 0)),
            "mc_p50": int(row.get("mc_p50", 0)) if "mc_p50" in row else None,
            "risk_level": row.get("risk_level", "") if "risk_level" in row else "",
        })
        delta_str = f"+{int(row.get('delta_wafers_per_week', 0)):,}" if row.get("delta_wafers_per_week", 0) >= 0 else f"{int(row.get('delta_wafers_per_week', 0)):,}"
        print(f"    {row.get('name', '')}: {int(row.get('total_effective_wafers_per_week', 0)):,} 片 ({delta_str})")

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
    if llm.is_configured():
        for a in orch.agents.values():
            a.llm = llm
        print(f"  LLM 已启用: {llm.provider} / {getattr(llm, 'model', 'N/A')}")
    else:
        print(f"  ⚠️ LLM 未配置, 使用本地模式")

    t0 = time.perf_counter()
    result = orch.run_full_pipeline(
        user_query="分析当前全厂产能瓶颈,评估未来7天产出趋势,并给出加设备 vs OEE提升的对比建议",
        trigger="e2e_test",
        window_hours=24,
        history_days=30,
    )
    pipeline_time = time.perf_counter() - t0

    print(f"  Pipeline 耗时: {pipeline_time:.1f}s")
    print(f"  状态: {result.status}")
    print(f"  Run ID: {result.run_id}")

    step_list = []
    for step in result.pipeline_steps:
        step_list.append({
            "agent_type": step.agent_type,
            "agent_cn": AGENT_NAME_CN.get(step.agent_type, step.agent_type),
            "status": step.status,
            "duration_ms": step.duration_ms,
            "error": step.error,
        })
        emoji = "✅" if step.status == STATUS_SUCCESS else "❌"
        print(f"  {emoji} {AGENT_NAME_CN.get(step.agent_type, '')}: {step.status} ({safe_round(step.duration_ms/1000, 2)}s)")
        if step.error:
            print(f"      错误: {step.error[:100]}")

    report_preview = (result.final_report or "")[:500]
    report_full = result.final_report or ""
    print(f"  报告长度: {len(report_full)} 字符")
    print(f"  报告预览: {report_preview[:200]}...")

    results["pipeline"] = {
        "run_id": result.run_id,
        "status": result.status,
        "duration_s": round(pipeline_time, 1),
        "llm_enabled": llm.is_configured(),
        "steps": step_list,
        "report_length": len(report_full),
        "report_preview": report_preview,
        "report_full": report_full,
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
            "run_id": r.get("run_id", ""),
            "created_at": str(r.get("created_at", ""))[:19],
            "succ_steps": int(r.get("succ_steps", 0)),
            "fail_steps": int(r.get("fail_steps", 0)),
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
# 保存结果 JSON
# =============================================================================
output_path = _PROJECT_ROOT / "test_results.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)
print(f"\n结果已保存: {output_path}")
print("\n✅ 全部测试步骤完成!")
