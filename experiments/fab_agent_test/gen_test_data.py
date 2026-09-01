"""
测试数据生成器
================
读取 .env 中的 DeepSeek API Key，调用 deepseek-chat 生成：
1. 多批次晶圆数据（覆盖 CD超标 / CD偏小 / 厚度异常 / 正常 等场景）
2. 对应工艺配方
3. 一组测试问题

输出：fab_test_data.json
供 app.py 加载后扩展 Mock 数据库，用于测试多 Agent 系统。

说明：使用标准库 urllib，无需额外依赖。
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path


# =====================================================================
# 读取 .env（手动解析，不依赖 python-dotenv）
# =====================================================================
def load_env(env_path: Path) -> dict:
    env = {}
    if not env_path.exists():
        return env
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


# =====================================================================
# 调用 DeepSeek（OpenAI 兼容接口）
# =====================================================================
def call_deepseek(
    prompt: str,
    api_key: str,
    base_url: str,
    model: str = "deepseek-chat",
    temperature: float = 0.8,
    timeout: int = 90,
) -> str:
    """通过 urllib 调用 DeepSeek chat completions，返回文本内容"""
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是半导体晶圆制造工艺数据生成助手，只输出合法 JSON。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
        result = json.loads(body)
        return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API HTTP {e.code}: {err}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"DeepSeek API 网络错误: {e.reason}") from None


# =====================================================================
# 提取 JSON（兼容 markdown 代码块包裹）
# =====================================================================
def extract_json(text: str) -> dict:
    text = text.strip()
    # 去掉 ```json ... ``` 包裹
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip("`").strip()
    return json.loads(text)


# =====================================================================
# 数据校验与归一化（确保字段完整、类型正确）
# =====================================================================
def normalize_lot(raw: dict, idx: int) -> dict:
    """归一化单条批次记录，补齐缺失字段"""
    lot_id = str(raw.get("lot_id") or f"W{10000 + idx}").upper()
    return {
        "lot_id": lot_id,
        "chamber_id": str(raw.get("chamber_id", "ETCH-CH-001")),
        "product": str(raw.get("product", "UnknownProduct")),
        "cd_target_nm": float(raw.get("cd_target_nm", 50.0)),
        "cd_measured_nm": float(raw.get("cd_measured_nm", 50.0)),
        "process_date": str(raw.get("process_date", "2026-08-09")),
        "status": str(raw.get("status", "未知")),
        "history": str(raw.get("history", "无历史数据")),
    }


def normalize_recipe(raw: dict, lot_id: str) -> dict:
    return {
        "recipe_id": str(raw.get("recipe_id", "RC-DEFAULT")),
        "pressure_setpoint_mtorr": float(raw.get("pressure_setpoint_mtorr", 5.0)),
        "rf_power_setpoint_w": float(raw.get("rf_power_setpoint_w", 1250)),
        "etch_time_sec": int(raw.get("etch_time_sec", 60)),
        "gas_flow_sccm": int(raw.get("gas_flow_sccm", 100)),
    }


def normalize_data(data: dict) -> dict:
    lots = {}
    for i, raw in enumerate(data.get("lots", [])):
        lot = normalize_lot(raw, i)
        lots[lot["lot_id"]] = lot

    recipes = {}
    for raw in data.get("recipes", []):
        lot_id = str(raw.get("lot_id", "")).upper()
        if lot_id:
            recipes[lot_id] = normalize_recipe(raw, lot_id)

    questions = [str(q) for q in data.get("questions", [])]
    return {"lots": lots, "recipes": recipes, "questions": questions}


# =====================================================================
# 主流程
# =====================================================================
def main():
    project_dir = Path(__file__).parent
    env = load_env(project_dir / ".env")

    api_key = env.get("DEEPSEEK_API_KEY")
    base_url = env.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    if not api_key:
        print("✗ 未在 .env 中找到 DEEPSEEK_API_KEY", file=sys.stderr)
        sys.exit(1)

    print(f"→ 使用 DeepSeek API: {base_url} (key=***{api_key[-4:]})")

    # —— 构造生成 prompt ——
    prompt = """请为半导体晶圆厂（FAB）缺陷根因分析系统生成测试数据，输出严格合法的 JSON 对象。

要求：
1. lots: 8 条批次记录，覆盖以下场景各至少1条：
   - CD（关键尺寸）超标
   - CD 偏小（低于目标）
   - 厚度异常
   - 正常批次
   - 同一腔体多次异常（关联性场景）
   批次号格式 W + 5位数字（如 W12345），腔体号格式 ETCH-CH-NNN，
   产品名真实化（如 LogicChip-A、DRAM-B、NAND-C），
   cd_target_nm 与 cd_measured_nm 用合理数值（nm），status 简短中文，
   history 给一句30天内关联性描述。

2. recipes: 与每个 lot 一一对应的工艺配方，recipe_id 格式 RC-2024-ETCH-VN，
   pressure_setpoint_mtorr 用 4.0~6.0 之间数值，
   异常批次的配方设定值保持正常（用于与机台实测形成冲突）。

3. questions: 6 条工艺工程师可能提出的分析问题，覆盖不同批次与缺陷类型，
   问题中包含批次号，语言自然。

输出 JSON 结构：
{
  "lots": [
    {"lot_id":"W12345","chamber_id":"ETCH-CH-007","product":"LogicChip-A",
     "cd_target_nm":50.0,"cd_measured_nm":52.8,"process_date":"2026-08-09",
     "status":"CD超标","history":"近30天该产品CD超标2次，均关联ETCH-CH-007"}
  ],
  "recipes": [
    {"lot_id":"W12345","recipe_id":"RC-2024-ETCH-V3",
     "pressure_setpoint_mtorr":5.0,"rf_power_setpoint_w":1250,
     "etch_time_sec":60,"gas_flow_sccm":100}
  ],
  "questions": ["批次 W12345 的关键尺寸（CD）超标，分析原因。"]
}
"""

    print("→ 调用 DeepSeek 生成数据中（可能需 10~30 秒）...")
    try:
        raw_text = call_deepseek(prompt, api_key, base_url)
    except RuntimeError as e:
        print(f"✗ 调用失败: {e}", file=sys.stderr)
        sys.exit(1)

    print("→ 解析返回 JSON ...")
    try:
        data = extract_json(raw_text)
    except json.JSONDecodeError as e:
        print(f"✗ JSON 解析失败: {e}", file=sys.stderr)
        print("原始返回前 500 字符:", raw_text[:500], file=sys.stderr)
        sys.exit(1)

    # 归一化
    normalized = normalize_data(data)
    lots = normalized["lots"]
    recipes = normalized["recipes"]
    questions = normalized["questions"]

    # 保留原有 W12345 / W67890（避免覆盖已验证数据），用生成的数据补充
    # 这里直接写入生成数据；app.py 会做"生成数据优先，否则用硬编码"的合并
    out_path = project_dir / "fab_test_data.json"
    output = {
        "source": "deepseek-chat",
        "generated_at": "2026-08-10",
        "lots": lots,
        "recipes": recipes,
        "questions": questions,
    }
    out_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n✓ 已生成: {out_path}")
    print(f"  批次数: {len(lots)}")
    print(f"  配方数: {len(recipes)}")
    print(f"  问题数: {len(questions)}")
    print("\n—— 生成的测试问题 ——")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")

    print("\n—— 批次概览 ——")
    for lot_id, lot in lots.items():
        delta = lot["cd_measured_nm"] - lot["cd_target_nm"]
        print(f"  {lot_id} | {lot['product']:14s} | {lot['chamber_id']} | "
              f"CD {lot['cd_target_nm']}→{lot['cd_measured_nm']} (Δ{delta:+.1f}) | {lot['status']}")


if __name__ == "__main__":
    main()
