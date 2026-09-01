"""wafer-trust-guard —— CIM 可信系统工程「红蓝对抗」Demo（Streamlit 入口）。

运行方式：
    pip install -r requirements.txt
    streamlit run app.py

红蓝对抗：
- 红队 Agent（攻击方）：想偷懒/走捷径/有幻觉的工艺工程师，生成表面合规、暗藏风险的 Recipe；
- 蓝队 Verifier（防御方）：历史失效库匹配 → L1 静态门禁 → Embedding 意图对齐 → LLM-as-Judge；
- 每一次被拦截的违规都会自动写入失效分析知识库（FA Report），下次遇到类似需求立刻告警 ——
  Verifier 拥有『记忆』：上次扩散炉超温炸过，这次就别再犯。

核心信念：Design is cheap, Verification is everything.
"""

import hashlib
import json
from datetime import datetime

import streamlit as st

from failure import fa_store
from generator.mock_agent import generate_recipe_with_note
from generator.redteam_agent import generate_redteam_recipe_with_note
from schemas.recipe import TEMP_MAX, TEMP_MIN, VALID_GASES, VALID_STEPS, WaferRecipe
from verifier.alignment_embedding import SIMILARITY_THRESHOLD, judge_alignment_embedding
from verifier.llm_judge import judge_with_llm
from verifier.static_rules import check_static

st.set_page_config(page_title="Wafer Trust Guard — 红蓝对抗版", page_icon="🛡️", layout="wide")

# ---------------- 页面标题 ----------------
st.title("🛡️ Wafer Trust Guard —— CIM 可信工程「红蓝对抗」Demo")
st.caption("红队 Agent 负责偷工减料，蓝队 Verifier 拥有绝对否决权与『历史记忆』 ｜ 验证比生成重要")

# ---------------- 侧边栏：验证哲学 + 数据契约 + FA 知识库 ----------------
with st.sidebar:
    st.header("🧠 验证哲学")
    st.markdown("> **Design is cheap, Verification is everything.**")
    st.caption("写 Recipe 很容易，验证才是决定流片生死的一环 —— 验证比生成重要。")
    st.divider()
    st.header("📜 Recipe 数据契约（Pydantic 严格定义）")
    st.json(WaferRecipe.model_json_schema())
    st.caption(
        f"温度物理极限：{TEMP_MIN}~{TEMP_MAX}°C　气体白名单：{' / '.join(VALID_GASES)}　"
        f"意图对齐阈值：≥ {SIMILARITY_THRESHOLD}"
    )
    st.divider()
    st.header("📚 失效分析知识库（FA 记忆）")
    st.caption(f"已收录 {fa_store.count()} 条 FA 记录 —— 每一次被拦截的违规都会入库，下次自动告警。")

# ---------------- 会话状态 ----------------
if "recipe" not in st.session_state:
    st.session_state.recipe = None
    st.session_state.agent_note = ""
    st.session_state.requirement = ""
    st.session_state.mode = ""
    st.session_state.verdicts = None
    st.session_state.kb = []
if "fa_log" not in st.session_state:
    st.session_state.fa_log = []
if "last_sig" not in st.session_state:
    st.session_state.last_sig = None


def run_blue_team(requirement: str, recipe: dict) -> dict:
    """蓝队验证流水线：L1 静态 → Embedding 对齐 → LLM Judge → 汇总裁决。"""
    l1 = check_static(recipe)
    embed = judge_alignment_embedding(requirement, recipe)
    judge = judge_with_llm(requirement, recipe)
    final_pass = bool(l1.passed and embed["pass"] and judge["pass"])
    reasons = []
    if not l1.passed:
        reasons.extend(l1.reasons)
    if not embed["pass"]:
        reasons.append(embed["reason"])
    if not judge["pass"]:
        reasons.append(judge["reason"])
    return {"l1": l1, "embed": embed, "judge": judge, "final_pass": final_pass, "reasons": reasons}


def first_fail_layer(l1, embed, judge) -> str:
    """返回第一个失败的验证层名称（用于 FA 归档标注）。"""
    if not l1.passed:
        return "L1静态门禁"
    if not embed["pass"]:
        return "L2意图偏离"
    if not judge["pass"]:
        return "LLM_Judge"
    return "Unknown"


# ---------------- 顶部：对抗模式选择 ----------------
mode = st.radio(
    "选择对抗模式：",
    options=["正常 Agent（mock）", "红队攻击模式（DeepSeek）"],
    horizontal=True,
)

left, mid, right = st.columns(3)

with left:
    st.subheader("1️⃣ 工艺需求输入（自然语言）")
    requirement = st.text_area(
        "描述你想要的工艺",
        value="给批次 A 做高温扩散，需要冷却",
        height=140,
        placeholder="红队模式示例：做高温扩散，要安全",
    )
    st.caption("红队模式建议输入：『做高温扩散，要安全』—— 看 Agent 如何把风险藏进参数。")

with mid:
    st.subheader("2️⃣ Generator（Agent 写代码）")
    if st.button("⚙️ 生成 Recipe", type="primary", use_container_width=True):
        if mode.startswith("红队"):
            recipe, note = generate_redteam_recipe_with_note(requirement)
        else:
            recipe, note = generate_recipe_with_note(requirement)
        st.session_state.recipe = recipe
        st.session_state.agent_note = note
        st.session_state.requirement = requirement
        st.session_state.mode = mode
        # 先查历史失效库（PE 开工前先翻档案），再做三层验证
        st.session_state.kb = fa_store.search(requirement, top_k=3)
        st.session_state.verdicts = run_blue_team(requirement, recipe)

    if st.session_state.recipe is None:
        st.info("尚未生成 Recipe，点击上方按钮开始。")
    else:
        st.error("🚨 未经验证的 Generator 输出 ——『流片前的代码』，可能暗藏风险")
        st.json(st.session_state.recipe, expanded=True)
        st.caption(f"{st.session_state.agent_note}　[生成器：{st.session_state.mode}]")

with right:
    st.subheader("3️⃣ 蓝队 Verifier（芯片级验证）")
    recipe = st.session_state.recipe
    verdicts = st.session_state.verdicts
    if recipe is None or verdicts is None:
        st.info("生成 Recipe 后，这里将展示：历史失效匹配 → L1 静态门禁 → Embedding 意图对齐 → LLM-as-Judge → 最终裁决。")
    else:
        l1 = verdicts["l1"]
        embed = verdicts["embed"]
        judge = verdicts["judge"]
        kb_matches = st.session_state.kb or []

        # ---- 历史失效库匹配（FA 记忆：PE 开工前先翻档案）----
        st.markdown("### 📚 历史失效库匹配")
        if kb_matches:
            st.warning(f"⚠️ 检测到 {len(kb_matches)} 条相似工艺曾在历史中被拦截")
            with st.expander("查看历史失效案例（FA Report）"):
                for m in kb_matches:
                    st.markdown(f"**{m['id']}** ｜ 相似度 **{m['similarity']:.3f}** ｜ 拦截层：{m['verifier_layer']}")
                    st.markdown(f"- 需求：`{m['requirement']}`")
                    st.markdown(f"- 原因：{m['block_reason']}")
        elif verdicts["final_pass"]:
            st.success("✅ 历史相似工艺均安全，可下发")
        else:
            st.caption("知识库暂无相似历史（本次事故将被记录为新失效模式）")

        # ---- L1 静态门禁（物理极限 + 气体白名单 + Pydantic 类型）----
        st.markdown("### ✅ L1 静态门禁" if l1.passed else "### ❌ L1 静态门禁")
        if l1.passed:
            st.caption(l1.reasons[0] if l1.reasons else "通过")
        else:
            for reason in l1.reasons:
                st.error(reason)

        # ---- Embedding 意图对齐（千问，显示相似度 + 进度条）----
        st.markdown("### 🎯 意图对齐（Embedding）")
        sim = float(embed["similarity"])
        st.progress(max(0.0, min(1.0, sim)))
        st.caption(f"意图对齐分：{sim:.4f}　（{embed['source']}，阈值 ≥ {SIMILARITY_THRESHOLD}）")
        if embed["pass"]:
            st.success(embed["reason"])
        else:
            st.error(embed["reason"])

        # ---- LLM-as-Judge（资深 PE 审核，带历史 Few-Shot）----
        st.markdown("### ⚖️ LLM-as-Judge（资深 PE 审核）")
        if judge["pass"]:
            st.success(f"审核通过：{judge['reason']}（{judge['source']}）")
        else:
            st.error(f"审核不通过：{judge['reason']}（{judge['source']}）")
        if judge.get("history_hit"):
            st.caption(f"🔔 记忆命中：{'、'.join(h['id'] for h in judge.get('history_refs', []))}")

        # ---- 最终裁决 ----
        st.divider()
        if verdicts["final_pass"]:
            st.success("#### 🟢 允许下发机台（Tape-out ALLOWED）")
        else:
            st.error("#### 🔴 拦截（防止晶圆报废）—— Recipe 被蓝队否决")
            if st.session_state.mode.startswith("红队"):
                st.error("⛔ 红队攻击被蓝队拦住了！")

            # 自动归档：本次事故写入失效分析知识库（FA Report），防重复用 sig 守卫
            sig = hashlib.md5(json.dumps(recipe, sort_keys=True).encode()).hexdigest()
            if st.session_state.last_sig != sig:
                layer = first_fail_layer(l1, embed, judge)
                reason = "；".join(verdicts["reasons"])
                new_case = fa_store.add_case(st.session_state.requirement, recipe, reason, layer)
                st.session_state.fa_log.append(
                    {
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "requirement": st.session_state.requirement,
                        "mode": st.session_state.mode,
                        "reasons": verdicts["reasons"],
                        "fa_id": new_case["id"],
                    }
                )
                st.session_state.last_sig = sig
                st.info(f"📝 已记录为 {new_case['id']}，加入工艺黑名单（下次遇到类似需求将触发历史告警）")

        # ---- 本机拦截记录（模拟 FA Report 台账）----
        with st.expander("🔬 本机拦截记录（模拟 FA Report 台账）"):
            if not st.session_state.fa_log:
                st.caption("暂无拦截记录（一切顺利）。")
            else:
                st.caption(f"共记录 {len(st.session_state.fa_log)} 次拦截 —— 蓝队正在守护晶圆。")
                for i, fa in enumerate(reversed(st.session_state.fa_log), 1):
                    mark = f"｜ {fa['fa_id']}" if fa.get("fa_id") else ""
                    st.markdown(f"**#{i}** {fa['time']} ｜ {fa['mode']} ｜ 需求：`{fa['requirement']}`{mark}")
                    st.code("\n".join(fa["reasons"]), language="text")