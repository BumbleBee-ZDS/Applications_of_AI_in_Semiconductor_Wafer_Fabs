"""
用 DeepSeek 合成训练数据 (纯合成策略)
============================================================
任务: 基于晶圆厂知识库, 让 DeepSeek 批量生成
      <口语问题, 三种模式输出> 的训练样本

三种模式 (一条样本同时产出三种标注, 高效):
  mode_a 领域感知查询增强: intent + entities + domain_hints + enhanced_query
  mode_b 术语翻译:        口语/缩写 -> 专业表述
  mode_c SQL模板路由:     问题 -> template_id + reason + params

输出: data/train.jsonl, data/eval.jsonl
"""
import os
import json
import re
import time
import random
import argparse
from dotenv import load_dotenv
from openai import OpenAI
from fab_mvp.knowledge_base import get_all_knowledge_text, SQL_TEMPLATES

load_dotenv()

# ResNet Step 1: DeepSeek 客户端 (兼容 OpenAI API)
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
MODEL = "deepseek-chat"

# 意图类别 (与知识库场景对齐, 让 DeepSeek 从中选取保证一致性)
INTENTS = [
    "yield_analysis",      # 良率分析
    "equipment_abnormal",  # 设备异常
    "process_param",       # 工艺参数偏离
    "lot_trace",           # 批次追溯
    "defect_analysis",     # 缺陷分析
    "spc_alarm",           # SPC告警
    "pm_analysis",         # PM保养分析
    "hold_query",          # Hold批次查询
]

# 可用SQL模板ID (供 mode_c 路由选择)
TEMPLATE_IDS = list(SQL_TEMPLATES.keys())

# ResNet Step 2: Few-shot 示例 (质量关键, 框定输出格式与风格)
FEW_SHOT = [
    {
        "user_query": "昨天3号机良率掉的厉害咋回事",
        "mode_a_enhance": {
            "intent": "yield_analysis",
            "entities": {"equipment_id": "EQP-PHOTO-003", "time_range": "昨天", "metric": "YIELD_RATE"},
            "domain_hints": "良率分析关联 WIP_LOT/PROCESS_LOG/YIELD_SUMMARY 表; YIELD_RATE<85%或低于基线5pp视为异常; 参考SOP_YIELD_DROP; 模板SQL_TMPL_YIELD_01",
            "enhanced_query": "分析设备EQP-PHOTO-003昨日CP良率下降原因: 查YIELD_SUMMARY找YIELD_RATE低于BASELINE_YIELD的批次, 关联PROCESS_LOG看是否集中在该设备, 查DEFECT_DATA与OOC_ALARM辅助归因"
        },
        "mode_b_translate": "请分析设备EQP-PHOTO-003在昨日的晶圆探针测试(CP)良率下降原因, 关联查询在制品批次表(WIP_LOT)、工艺日志表(PROCESS_LOG)与良率汇总表(YIELD_SUMMARY)",
        "mode_c_route": {
            "template_id": "SQL_TMPL_YIELD_01",
            "reason": "问题核心是良率下降, 需查YIELD_SUMMARY中YIELD_RATE低于基线的异常批次",
            "params": {"start_date": "昨天"}
        }
    },
    {
        "user_query": "L28那批货卡在hold好几天了啥情况",
        "mode_a_enhance": {
            "intent": "hold_query",
            "entities": {"product_id": "PROD-L28", "lot_status": "HOLD", "duration": "数天"},
            "domain_hints": "Hold查询用WIP_LOT表, LOT_STATUS='HOLD', HOLD_TIME超阈值; HOLD_CODE标识原因; 参考SOP; 模板SQL_TMPL_HOLD_01",
            "enhanced_query": "查询产品PROD-L28中LOT_STATUS为HOLD且HOLD_TIME较长的批次, 返回HOLD_CODE原因与OWNER_ID负责人"
        },
        "mode_b_translate": "请查询产品型号PROD-L28中处于扣留(HOLD)状态且停滞时间较长的批次, 返回扣留原因代码与负责工程师",
        "mode_c_route": {
            "template_id": "SQL_TMPL_HOLD_01",
            "reason": "问题涉及批次扣留停滞, 需查WIP_LOT中HOLD状态批次及原因",
            "params": {"threshold": "较长时长"}
        }
    },
    {
        "user_query": "刻蚀那台设备有OOC没处理完的",
        "mode_a_enhance": {
            "intent": "spc_alarm",
            "entities": {"eqp_type": "ETCH", "alarm_type": "OOC", "disposition": "OPEN"},
            "domain_hints": "SPC告警查OOC_ALARM表, DISPOSITION='OPEN'为未关闭; 关联EQUIPMENT按EQP_TYPE过滤; 参考SOP_OOC_HANDLE; 模板SQL_TMPL_SPC_01",
            "enhanced_query": "查询刻蚀(ETCH)类型设备中DISPOSITION为OPEN的OOC告警记录, 返回ALARM_ID/EQP_ID/PARAM_ID/ALARM_TIME"
        },
        "mode_b_translate": "请查询刻蚀(ETCH)类型设备中尚未处置关闭(DISPOSITION=OPEN)的统计过程控制(SPC)失控(OOC)告警记录",
        "mode_c_route": {
            "template_id": "SQL_TMPL_SPC_01",
            "reason": "问题涉及未关闭的SPC OOC告警, 需查OOC_ALARM表OPEN状态告警",
            "params": {"start_date": "近期", "eqp_type": "ETCH"}
        }
    },
]

# ResNet Step 3: Prompt 构造
SYSTEM_PROMPT = (
    "你是晶圆厂(半导体制造)资深MES工程师兼数据标注专家, 熟悉Oracle数据库与领域黑话。"
    "任务: 基于给定知识库, 生成【工程师真实口语提问】样本, 并给出三种预处理输出。"
    "要求:\n"
    "1. user_query 必须口语化、含缩写/黑话/模糊指代(如'3号机''那批货''掉得厉害'), 模拟工程师日常提问;\n"
    "2. 三种模式输出必须严格遵循示例格式, 字段完整;\n"
    "3. mode_a 的 intent 只能从给定意图列表选, entities 提取关键实体, domain_hints 引用真实表名/字段/SOP/模板, enhanced_query 是给强模型的专业重写;\n"
    "4. mode_b 把口语和缩写翻译为含表名/专业术语的表述;\n"
    "5. mode_c 的 template_id 只能从给定模板列表选, params 给出绑定参数;\n"
    "6. 样本要多样: 覆盖不同意图、设备类型、产品、时间表达, 不要重复。\n"
    "输出严格为JSON: {\"samples\": [...]}, 不要输出任何额外文字。"
)


def build_user_prompt(n: int) -> str:
    """构造 user prompt: 知识库 + 意图/模板列表 + few-shot + 生成指令"""
    kb = get_all_knowledge_text()
    few_shot_str = json.dumps(FEW_SHOT, ensure_ascii=False, indent=2)
    return (
        f"{kb}\n\n"
        f"## 可用意图列表\n{INTENTS}\n\n"
        f"## 可用SQL模板ID\n{TEMPLATE_IDS}\n\n"
        f"## 标注示例(few-shot, 仅供格式与风格参考, 不要复制)\n{few_shot_str}\n\n"
        f"## 任务\n"
        f"请生成 {n} 条全新的样本, 覆盖不同意图与场景。"
        f"输出JSON: {{\"samples\": [{{\"user_query\":..., \"mode_a_enhance\":{{...}}, \"mode_b_translate\":..., \"mode_c_route\":{{...}}}}]}}"
    )


# ResNet Step 4: 调用 DeepSeek 生成一批样本
def gen_batch(n: int = 6, retries: int = 2) -> list:
    """调用 DeepSeek 生成 n 条样本, 带重试"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(n)},
    ]
    for attempt in range(retries + 1):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=1.1,        # 高温度保证多样性
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            data = json.loads(content)
            samples = data.get("samples", [])
            if samples:
                return samples
        except Exception as e:
            print(f"  [重试 {attempt+1}/{retries+1}] 生成失败: {e}")
            time.sleep(2)
    return []


# ResNet Step 5: 样本校验 (过滤格式不合格的)
def validate_sample(s: dict) -> bool:
    if not s.get("user_query"):
        return False
    a = s.get("mode_a_enhance")
    if not isinstance(a, dict) or not a.get("intent") or not a.get("enhanced_query"):
        return False
    if not s.get("mode_b_translate"):
        return False
    c = s.get("mode_c_route")
    if not isinstance(c, dict) or c.get("template_id") not in TEMPLATE_IDS:
        return False
    if a["intent"] not in INTENTS:
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", type=int, default=120, help="训练集目标条数")
    ap.add_argument("--eval", type=int, default=30, help="验证集目标条数")
    ap.add_argument("--batch", type=int, default=6, help="每批生成条数")
    ap.add_argument("--quick", action="store_true", help="快速模式: 只生成1批并打印, 用于验证质量")
    args = ap.parse_args()

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)

    # quick 模式: 生成1批打印展示
    if args.quick:
        print("=== QUICK 模式: 生成1批验证质量 ===")
        samples = gen_batch(args.batch)
        valid = [s for s in samples if validate_sample(s)]
        print(f"生成 {len(samples)} 条, 校验通过 {len(valid)} 条\n")
        for i, s in enumerate(valid[:3]):
            print(f"--- 样本 {i+1} ---")
            print(json.dumps(s, ensure_ascii=False, indent=2))
            print()
        return

    # 全量生成
    total_target = args.train + args.eval
    all_samples = []
    seen_queries = set()
    batch_size = args.batch
    n_batches = (total_target // batch_size) + 2  # 多生成几批兜底

    print(f"=== 全量生成: 目标 {total_target} 条 (train={args.train}, eval={args.eval}) ===")
    for b in range(n_batches):
        if len(all_samples) >= total_target:
            break
        samples = gen_batch(batch_size)
        added = 0
        for s in samples:
            if validate_sample(s) and s["user_query"] not in seen_queries:
                seen_queries.add(s["user_query"])
                all_samples.append(s)
                added += 1
        print(f"批次 {b+1}/{n_batches}: 生成 {len(samples)}, 新增有效 {added}, 累计 {len(all_samples)}")
        time.sleep(0.5)

    # 打乱并切分 train/eval
    random.seed(42)
    random.shuffle(all_samples)
    all_samples = all_samples[:total_target]
    split = min(args.train, len(all_samples))
    train = all_samples[:split]
    ev = all_samples[split:]

    train_path = os.path.join(data_dir, "train.jsonl")
    eval_path = os.path.join(data_dir, "eval.jsonl")
    with open(train_path, "w", encoding="utf-8") as f:
        for s in train:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    with open(eval_path, "w", encoding="utf-8") as f:
        for s in ev:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"\n完成: train={len(train)} -> {train_path}")
    print(f"      eval ={len(ev)} -> {eval_path}")


if __name__ == "__main__":
    main()
