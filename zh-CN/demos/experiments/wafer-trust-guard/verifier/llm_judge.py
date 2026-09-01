"""L3 LLM-as-Judge 验证层：DeepSeek 担任晶圆厂资深 PE 做 Tape-out 前审核。

System Prompt 只检查三件事：
1. 温度是否违反物理极限
2. 冷却步骤是否缺失
3. 气体是否匹配步骤

输出 JSON：{"pass": bool, "reason": str}

升级（FA 记忆版 v3）：注入『失效分析知识库』历史案例作为 Few-Shot ——
每次审核前先查 FA 库（fa_store.search），把相似历史事故塞进 System Prompt，
并在 reason 里标注是否『命中历史失效模式』。让 Verifier 拥有『记忆』：
『上次扩散炉超温炸过，这次别重犯。』

可靠性约定：所有调用均 try/except —— 失败时用本地规则
（L1 静态门禁 + L3 属性不变量）兜底，保证 Demo 不崩。
"""

import json
import re

import config

from failure import fa_store
from verifier.invariants import check_invariants
from verifier.static_rules import check_static

JUDGE_SYSTEM_PROMPT = (
    "你是晶圆厂资深 PE（工艺工程师），负责 Tape-out 前审核。你只检查：\n"
    "1. 温度是否违反物理极限\n"
    "2. 冷却步骤是否缺失\n"
    "3. 气体是否匹配步骤\n"
    '输出 JSON: {"pass": bool, "reason": str}，不要输出其他内容，不要解释。'
)


def judge_with_llm(user_requirement: str, recipe: dict) -> dict:
    """LLM 审核 Recipe（带历史失效案例 Few-Shot）。

    返回：{"pass": bool, "reason": str, "source": "llm"|"local",
           "history_hit": bool, "history_refs": list}
    """
    context, hits = _build_fewshot(user_requirement)
    system = JUDGE_SYSTEM_PROMPT + ("\n\n" + context if context else "")
    try:
        client = config.deepseek_client
        if client is None:
            raise RuntimeError("未配置 DEEPSEEK_API_KEY（请检查 .env）")
        resp = client.chat.completions.create(
            model=config.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": (
                        f"用户需求：{user_requirement}\n"
                        f"待审核 Recipe JSON：\n{json.dumps(recipe, ensure_ascii=False, indent=2)}"
                    ),
                },
            ],
            temperature=0.0,
            max_tokens=200,
        )
        result = _parse_judge_json(resp.choices[0].message.content)
        result["source"] = "llm"
    except Exception as exc:
        result = _local_fallback_verdict(recipe)
        result["reason"] = f"[本地兜底] {result['reason']}（LLM 调用失败：{str(exc)[:80]}）"
        result["source"] = "local"
    return _mark_history(result, hits)


def _build_fewshot(requirement: str) -> tuple:
    """检索历史失效案例，整理成 Few-Shot 上下文。返回 (上下文文本, 命中列表)。"""
    hits = fa_store.search(requirement, top_k=3)
    if not hits:
        return "", []
    lines = ["你是晶圆厂资深 PE。以下是历史上因为类似需求导致的工艺事故："]
    lines += [f'需求"{h["requirement"]}" -> 原因：{h["block_reason"]}' for h in hits]
    lines.append("现在请审核当前 Recipe，重点检查是否重犯上述错误。")
    return "\n".join(lines), hits


def _mark_history(result: dict, hits: list) -> dict:
    """在审核结果上标注是否『命中历史失效模式』。"""
    result["history_hit"] = bool(hits)
    result["history_refs"] = [
        {"id": h["id"], "requirement": h["requirement"], "block_reason": h["block_reason"]}
        for h in hits
    ]
    if hits:
        ids = "、".join(h["id"] for h in hits)
        tag = "命中历史失效模式" if not result["pass"] else "未重犯历史失效模式"
        result["reason"] = f"{result['reason']}｜{tag}（{ids}）"
    return result


def _parse_judge_json(content: str) -> dict:
    """从 LLM 输出中稳健地解析 {"pass": bool, "reason": str}。"""
    text = (content or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE)
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError("LLM 输出中没有 JSON 对象")
    data = json.loads(m.group(0))
    if not isinstance(data, dict):
        raise ValueError("LLM 输出不是 JSON 对象")
    passed = data.get("pass")
    if not isinstance(passed, bool):
        raise ValueError("pass 字段不是布尔值")
    return {"pass": passed, "reason": str(data.get("reason", "无说明"))}


def _local_fallback_verdict(recipe: dict) -> dict:
    """本地兜底：用 L1 静态门禁 + L3 属性不变量替代 LLM 检查三件事。"""
    reasons = []
    l1 = check_static(recipe)
    if not l1.passed:
        reasons.extend(l1.reasons)
    l3 = check_invariants(recipe)
    if not l3.passed:
        reasons.extend(l3.reasons)
    if reasons:
        return {"pass": False, "reason": "；".join(reasons)}
    return {"pass": True, "reason": "温度、冷却、气体均未发现异常（本地规则兜底通过）"}