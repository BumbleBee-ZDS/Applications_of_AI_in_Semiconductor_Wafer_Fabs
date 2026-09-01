# -*- coding: utf-8 -*-
"""
ontology.py —— 语义层（Semantic Layer）+ 动力层（Kinetic Layer）
=================================================================

Palantir Ontology 三层架构映射
-------------------------------
┌──────────────────────────────────────────────────────────────────┐
│ 语义层（Semantic Layer）：OntologyDictionary                        │
│   - 本体字典 ontology_dict.json：业务概念 <-> 字段 的映射            │
│   - Schema 解析器 filter_for_query()：只把「与问题相关」的本体片段    │
│     注入给 LLM，避免 Token 浪费（核心思想，对应 Palantir 语义映射）  │
├──────────────────────────────────────────────────────────────────┤
│ 动力层（Kinetic Layer）：FabQueryAgent                              │
│   - LLM 仅负责「意图识别 + 参数提取」，输出结构化 JSON 计划           │
│   - 根据计划从「预定义模板库 sql_templates/*.sql」选择模板，          │
│     绝不把 JOIN / WHERE 写 SQL 的自由交给 LLM（核心思想）            │
│   - SQL 一律参数化绑定（防注入），设备/批次编号白名单校验             │
├──────────────────────────────────────────────────────────────────┤
│ 动态层见 mock_db.py（SQLite 数据执行）                               │
└──────────────────────────────────────────────────────────────────┘

离线可用性：未配置 LLM 或调用失败时，自动回退到本地规则引擎
（_extract_intent_rules），保证 `streamlit run app.py` 开箱即跑。
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

from mock_db import DB_PATH, get_connection, init_db

BASE_DIR = Path(__file__).resolve().parent
ONTOLOGY_PATH = BASE_DIR / "ontology_dict.json"
TEMPLATE_DIR = BASE_DIR / "sql_templates"

# ---------------------------------------------------------------------------
# 模型配置
# ---------------------------------------------------------------------------
@dataclass
class LLMConfig:
    """OpenAI SDK 兼容配置（可指向云端 API 或本地 vLLM / Ollama 等）。"""
    enabled: bool = True
    model: str = os.getenv("LLM_MODEL", "deepseek-chat")
    base_url: str = os.getenv("DEEPSEEK_BASE_URL", "")
    api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    temperature: float = 0.0
    timeout: float = 60.0


@dataclass
class TraceData:
    """一次完整查询的「思考链」记录，供 Streamlit Trace 面板展示。"""
    question: str
    extraction_mode: str                       # llm | rule | llm_failed→rule
    plan: dict                                 # 动力层结构化查询计划
    matched_concepts: list[dict]               # ① 语义层命中的本体概念
    injected_fragments: list[str]              # ① 注入给 LLM 的本体片段
    template_name: str                         # ③ 动力层模板名
    sql: str                                   # ③ 最终执行的 SQL
    params: list                               # ③ 绑定参数（参数化查询）
    result: Optional[pd.DataFrame] = None      # ④ 动态层执行结果
    error: Optional[str] = None
    elapsed_ms: int = 0


# LLM 意图提取的系统提示词：只做意图识别与参数提取，绝不写 SQL
INTENT_SYSTEM_PROMPT = """你是半导体晶圆厂（FAB）的查询规划器。你的职责是【意图识别 + 参数提取】，而不是编写 SQL。
根据用户的中文问题，输出且只输出一个 JSON 对象（不要任何解释、代码块标记之外的内容，不要写 SQL）：

{
  "object": "equipment | lot | wafer | process | null",
  "metric": "yield | film_thickness | defect_count | null",
  "trend": true | false,
  "equipment": "EQP-003 | null",
  "lot": "LOT-2026-001 | null",
  "condition": "film_abnormal | defect_high | null",
  "time_range": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"} | null
}

字段含义与规则：
- object：用户关注的对象（设备/批次/晶圆/工艺）。涉及设备良率、膜厚、缺陷时多为 equipment 或 wafer。
- metric：关注的指标；问题中没有具体指标时为 null。
- trend：出现「趋势/走势/变化/曲线」语义时为 true。
- condition：膜厚异常=film_abnormal；缺陷偏高/缺陷多=defect_high。
- time_range：上周→最近7天；昨天→最近1天；本月→最近30天；明确给出日期范围则原样给出；否则 null（系统会自动补默认时间窗）。
- equipment / lot：设备编号、批次编号必须从问题中提取，问题里没有就填 null，绝不臆造编号。
"""


# ---------------------------------------------------------------------------
# 语义层：本体字典 + Schema 解析器
# ---------------------------------------------------------------------------
class OntologyDictionary:
    """语义层本体字典。

    从 ontology_dict.json 加载「业务概念 <-> 字段」映射，并提供：
    - filter_for_query():  Schema 解析器，仅保留与问题相关的本体片段；
    - render_fragments():  把命中片段渲染成紧凑文本（注入 LLM）；
    - match_concepts():    返回命中的概念明细（供 Trace 面板展示）。
    """

    def __init__(self, path: str | os.PathLike = ONTOLOGY_PATH):
        self.path = Path(path)
        with open(self.path, encoding="utf-8") as f:
            self.raw = json.load(f)
        self.total_concepts = (len(self.raw.get("objects", []))
                               + len(self.raw.get("metrics", []))
                               + len(self.raw.get("conditions", []))
                               + len(self.raw.get("equipment_aliases", []))
                               + len(self.raw.get("time_expressions", [])))

    # ---------- Schema 解析器：关键词命中式过滤 ----------
    def filter_for_query(self, question: str) -> dict:
        """只返回与问题相关的本体概念片段（语义层核心，省 Token）。"""
        q = question.lower()

        def hit(concept: dict) -> bool:
            return any(str(k).lower() in q for k in concept.get("keywords", []))

        matched = {
            "objects":          [o for o in self.raw["objects"] if hit(o)],
            "metrics":          [m for m in self.raw["metrics"] if hit(m)],
            "conditions":       [c for c in self.raw["conditions"] if hit(c)],
            "aliases":          [a for a in self.raw["equipment_aliases"] if a["keyword"] in question],
            "time_expressions": [t for t in self.raw["time_expressions"] if hit(t)],
        }
        matched["_anything"] = any(matched.values())
        return matched

    def render_fragments(self, matched: dict) -> list[str]:
        """把命中的本体片段渲染为紧凑文本（按行），供 LLM 提示词使用。"""
        lines = []
        # 相关表结构（仅命中概念涉及的表；无命中时全量兜底）
        if matched["_anything"]:
            table_names = {m["table"] for m in matched["metrics"]} | \
                          {o["table"] for o in matched["objects"]} | \
                          {c["table"] for c in matched["conditions"]}
            tables = [t for t in self.raw["tables"] if t["name"] in table_names]
        else:
            tables = self.raw["tables"]
        for t in tables:
            fields = "、".join(f"{f['name']}({f['label']})" for f in t["fields"])
            lines.append(f"表 {t['name']}（{t['comment']}）：{fields}")

        for m in matched["metrics"]:
            lines.append(f"指标「{m['label']}」→ {m['table']}.{m['field']}"
                         f"（聚合 {m['aggregation']}，单位 {m['unit']}，{m['explain']}）")
        for c in matched["conditions"]:
            lines.append(f"条件「{c['label']}」→ {c['sql_condition']}（{c['explain']}）")
        for a in matched["aliases"]:
            lines.append(f"设备别名「{a['keyword']}」→ {a['value']}")
        for t in matched["time_expressions"]:
            lines.append(f"时间槽「{t['label']}」→ {t['explain']}")

        # 无命中时兜底注入全部指标，保证 LLM 有最小上下文
        if not matched["_anything"]:
            for m in self.raw["metrics"]:
                lines.append(f"指标「{m['label']}」→ {m['table']}.{m['field']}"
                             f"（聚合 {m['aggregation']}，单位 {m['unit']}）")
        return lines

    def match_concepts(self, question: str) -> list[dict]:
        """返回命中的本体概念明细（供 Trace 展示「匹配的本体概念」）。"""
        q = question.lower()
        hits: list[dict] = []

        def first_keyword(concept: dict) -> str | None:
            for k in concept.get("keywords", []):
                if str(k).lower() in q:
                    return str(k)
            return None

        for o in self.raw["objects"]:
            kw = first_keyword(o)
            if kw:
                hits.append({"type": "对象", "label": o["label"], "keyword": kw,
                             "explain": f"业务对象「{o['label']}」→ 表 {o['table']}.{o['default_field']}"})
        for m in self.raw["metrics"]:
            kw = first_keyword(m)
            if kw:
                hits.append({"type": "指标", "label": m["label"], "keyword": kw,
                             "explain": f"指标「{m['label']}」→ {m['table']}.{m['field']}"})
        for c in self.raw["conditions"]:
            kw = first_keyword(c)
            if kw:
                hits.append({"type": "条件", "label": c["label"], "keyword": kw,
                             "explain": f"条件「{c['label']}」→ {c['sql_condition']}"})
        for a in self.raw["equipment_aliases"]:
            if a["keyword"] in question:
                hits.append({"type": "别名", "label": a["keyword"], "keyword": a["keyword"],
                             "explain": a["explain"]})
        for t in self.raw["time_expressions"]:
            kw = first_keyword(t)
            if kw:
                hits.append({"type": "时间", "label": t["label"], "keyword": kw,
                             "explain": t["explain"]})
        return hits

    # ---------- 业务黑话 -> 结构化值 的底层转换工具 ----------
    def normalize_equipment(self, question: str) -> Optional[str]:
        """识别「3号机 / EQP-003 / eqp003」等写法 -> EQP-003。"""
        m = re.search(r"EQP[-_ ]?(\d{1,3})", question, re.IGNORECASE)
        if m:
            return f"EQP-{int(m.group(1)):03d}"
        m = re.search(r"(\d{1,2})\s*号机", question)
        if m:
            return f"EQP-{int(m.group(1)):03d}"
        for a in self.raw.get("equipment_aliases", []):
            if a["keyword"] in question:
                return a["value"]
        return None

    def normalize_lot(self, question: str) -> Optional[str]:
        """识别 LOT-2026-001 / LOT2026001 -> LOT-2026-001。"""
        m = re.search(r"LOT[-_ ]?(\d{4})[-_ ]?(\d{3})", question, re.IGNORECASE)
        if m:
            return f"LOT-{m.group(1)}-{m.group(2)}"
        return None

    def parse_time_range(self, question: str) -> Optional[tuple[str, str]]:
        """解析相对时间/绝对日期 -> (start, end) ISO 日期串。"""
        today = dt.date.today()
        # 显式日期范围：2026-08-01 到 2026-08-07 / 2026-08-01~2026-08-07
        m = re.search(r"(\d{4}-\d{2}-\d{2})\s*(?:到|至|~|～|—)\s*(\d{4}-\d{2}-\d{2})", question)
        if m:
            try:
                s, e = dt.date.fromisoformat(m.group(1)), dt.date.fromisoformat(m.group(2))
                if s <= e:
                    return s.isoformat(), e.isoformat()
            except ValueError:
                pass
        # 单日：2026-08-01
        m = re.search(r"(\d{4}-\d{2}-\d{2})", question)
        if m:
            try:
                d = dt.date.fromisoformat(m.group(1))
                return d.isoformat(), d.isoformat()
            except ValueError:
                pass
        # 最近N天
        m = re.search(r"最近\s*(\d+)\s*天", question)
        if m:
            n = int(m.group(1))
            return (today - dt.timedelta(days=n)).isoformat(), today.isoformat()
        # 本体字典时间槽（上周/昨天/本月…）
        q = question.lower()
        for t in self.raw.get("time_expressions", []):
            if any(str(k).lower() in q for k in t["keywords"]):
                n = t["days_offset"]
                return (today - dt.timedelta(days=n)).isoformat(), today.isoformat()
        return None

    @staticmethod
    def clean_json(text: str) -> str:
        """剥离 LLM 输出中可能的 ```json 代码块包围。"""
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return text.strip()


# ---------------------------------------------------------------------------
# 动力层：FabQueryAgent
# ---------------------------------------------------------------------------
class FabQueryAgent:
    """动力层 Agent：意图提取（LLM/规则）→ 模板选择 → 参数化 SQL → 执行。

    核心原则：LLM 只输出结构化 JSON 计划；SQL 永远来自本地模板库，
    参数一律白名单校验 + 参数化绑定，杜绝自由写 SQL 带来的注入/幻觉风险。
    """

    _ALLOWED_OBJECTS = {"equipment", "lot", "wafer", "process"}
    _ALLOWED_METRICS = {"yield", "film_thickness", "defect_count"}
    _ALLOWED_CONDITIONS = {"film_abnormal", "defect_high"}

    def __init__(self, ontology: Optional[OntologyDictionary] = None,
                 db_path: str = DB_PATH,
                 llm_config: Optional[LLMConfig] = None):
        self.ontology = ontology or OntologyDictionary()
        self.db_path = db_path
        self.llm_config = llm_config or LLMConfig()
        self.templates: dict[str, str] = self._load_templates()
        self._client = None          # OpenAI 兼容客户端（懒加载）

    # ---------- 基础设施 ----------
    def _load_templates(self) -> dict[str, str]:
        """加载动力层模板库 sql_templates/*.sql。"""
        templates = {}
        if TEMPLATE_DIR.exists():
            for f in sorted(TEMPLATE_DIR.glob("*.sql")):
                templates[f.stem] = f.read_text(encoding="utf-8")
        return templates

    def _get_client(self):
        """懒加载 OpenAI 兼容客户端（支持本地 vLLM/Ollama 或云端）。"""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                return None
            try:
                self._client = OpenAI(
                    api_key=self.llm_config.api_key or "EMPTY",
                    base_url=self.llm_config.base_url or None,
                    timeout=self.llm_config.timeout,
                )
            except Exception:
                return None
        return self._client

    # ---------- 主入口 ----------
    def ask(self, question: str) -> TraceData:
        """执行一次完整的「自然语言 -> 结果」流水线。"""
        t0 = time.time()
        init_db()                                     # 幂等，确保动态层数据存在

        # ① 语义层：Schema 解析器只取相关片段
        fragments = self.ontology.filter_for_query(question)
        injected = self.ontology.render_fragments(fragments)
        matched = self.ontology.match_concepts(question)

        # ② 意图提取：优先 LLM，失败/未启用则规则引擎兜底
        plan: Optional[dict] = None
        mode = "rule"
        if self.llm_config.enabled:
            plan = self._extract_intent_llm(question, injected)
            mode = "llm" if plan is not None else "llm失败→rule"
        if plan is None:
            plan = self._extract_intent_rules(question)
            if not self.llm_config.enabled:
                mode = "rule(离线)"

        # 统一 time_range 结构：(start, end) 元组 -> {"start": ..., "end": ...}
        if isinstance(plan.get("time_range"), (tuple, list)):
            s, e = plan["time_range"]
            plan["time_range"] = {"start": s, "end": e}

        # 补默认时间窗（未指定时取最近 30 天）
        if plan.get("time_range") is None:
            today = dt.date.today()
            plan["time_range"] = {
                "start": (today - dt.timedelta(days=30)).isoformat(),
                "end": today.isoformat(),
            }

        # ③ 动力层：模板选择 + 参数化 SQL
        try:
            template_name, params = self._select_template(plan)
            sql = self.templates[template_name].strip()
            df = self._execute(sql, params)
            error = None
        except Exception as e:                        # 执行失败也完整返回 Trace
            template_name, params, df = "—", [], pd.DataFrame()
            sql = "—"
            error = str(e)

        return TraceData(
            question=question,
            extraction_mode=mode,
            plan=plan,
            matched_concepts=matched,
            injected_fragments=injected,
            template_name=template_name,
            sql=sql,
            params=params,
            result=None if error else df,
            error=error,
            elapsed_ms=int((time.time() - t0) * 1000),
        )

    # ---------- ② 意图提取：LLM ----------
    def _extract_intent_llm(self, question: str, injected: list[str]) -> Optional[dict]:
        """调用 OpenAI 兼容接口提取结构化查询计划（JSON）。失败返回 None。"""
        try:
            client = self._get_client()
            if client is None:
                return None
            frag_text = "\n".join(f"- {line}" for line in injected)
            today = dt.date.today()
            last7 = (today - dt.timedelta(days=7)).isoformat()
            user = (
                f"【今天是 {today.isoformat()}。所有相对时间必须以此为准解析，例如："
                f"上周 = 最近7天，即 {last7} 至 {today.isoformat()}】\n\n"
                f"【可用本体概念（已按问题相关性过滤，只有这些片段）】\n{frag_text}\n\n"
                f"【用户问题】\n{question}"
            )
            kwargs = dict(
                model=self.llm_config.model,
                temperature=self.llm_config.temperature,
                messages=[
                    {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": user},
                ],
            )
            try:
                resp = client.chat.completions.create(**kwargs,
                                                      response_format={"type": "json_object"})
            except Exception:
                resp = client.chat.completions.create(**kwargs)   # 部分后端不支持 json_object
            content = resp.choices[0].message.content or ""
            plan = json.loads(self.ontology.clean_json(content))
            validated = self._validate_plan(plan)
            if validated and any(validated.values()):
                return validated
            return None
        except Exception:
            return None

    def _validate_plan(self, plan: dict) -> Optional[dict]:
        """白名单校验 LLM 输出：非法值一律置空（绝不信任模型自由发挥）。"""
        if not isinstance(plan, dict):
            return None
        out = {
            "object":   plan.get("object") if plan.get("object") in self._ALLOWED_OBJECTS else None,
            "metric":   plan.get("metric") if plan.get("metric") in self._ALLOWED_METRICS else None,
            "trend":    bool(plan.get("trend")),
            "condition": None,
            "equipment": None,
            "lot":      None,
            "time_range": None,
        }
        if plan.get("condition") in self._ALLOWED_CONDITIONS:
            out["condition"] = plan["condition"]
        eqp = plan.get("equipment")
        if isinstance(eqp, str) and re.fullmatch(r"EQP-\d{3}", eqp.strip().upper()):
            out["equipment"] = eqp.strip().upper()
        lot = plan.get("lot")
        if isinstance(lot, str) and re.fullmatch(r"LOT-\d{4}-\d{3}", lot.strip().upper()):
            out["lot"] = lot.strip().upper()
        tr = plan.get("time_range")
        if isinstance(tr, dict):
            try:
                s = dt.date.fromisoformat(str(tr.get("start", ""))[:10])
                e = dt.date.fromisoformat(str(tr.get("end", ""))[:10])
                if s <= e:
                    out["time_range"] = {"start": s.isoformat(), "end": e.isoformat()}
            except (TypeError, ValueError):
                pass
        return out

    # ---------- ② 意图提取：本地规则引擎（离线兜底） ----------
    def _extract_intent_rules(self, question: str) -> dict:
        """基于本体字典关键词 + 正则的确定性提取，保证离线可用。"""
        q = question.lower()
        plan = {
            "object":   None,
            "metric":   None,
            "trend":    any(k in q for k in ("趋势", "走势", "变化", "曲线")),
            "condition": None,
            "equipment": self.ontology.normalize_equipment(question),
            "lot":      self.ontology.normalize_lot(question),
            "time_range": self.ontology.parse_time_range(question),
        }

        def first_hit_keyword(concepts) -> tuple | None:
            for c in concepts:
                for k in c.get("keywords", []):
                    if str(k).lower() in q:
                        return c["id"], c
            return None

        # 指标、条件
        hit = first_hit_keyword(self.ontology.raw["metrics"])
        if hit:
            plan["metric"] = hit[0]
        hit = first_hit_keyword(self.ontology.raw["conditions"])
        if hit:
            plan["condition"] = hit[0]

        # 对象判定
        if any(k in q for k in ("工艺", "制程", "工序", "日志", "process")):
            plan["object"] = "process"
        elif plan["lot"]:
            plan["object"] = "lot"
        elif plan["equipment"] or any(k in q for k in ("设备", "机台", "机器", "号机")):
            plan["object"] = "equipment"
        elif plan["metric"]:
            plan["object"] = "wafer"
        else:
            plan["object"] = "equipment"
        return plan

    # ---------- ③ 动力层：模板选择 ----------
    def _select_template(self, plan: dict) -> tuple[str, list]:
        """根据结构化计划选择预定义模板并生成绑定参数（不拼接任意 SQL）。"""
        m, obj, trend = plan["metric"], plan["object"], plan["trend"]
        eqp, lot, cond = plan["equipment"], plan["lot"], plan["condition"]
        tr = plan["time_range"]
        start, end = tr["start"], tr["end"]

        # 工艺日志
        if obj == "process":
            if lot:
                return "get_process_log_by_lot", [lot]
            return "get_process_log_by_equipment", [eqp, start, end]

        # 批次
        if obj == "lot":
            if lot:
                return "get_lot_status", [lot]
            return "get_lot_list", []

        # 无指标 -> 设备状态
        if m is None:
            return "get_equipment_status", [eqp]

        # 良率
        if m == "yield":
            if trend:
                return "get_yield_trend", [start, end, eqp]
            return "get_equipment_yield", [start, end, eqp]

        # 膜厚
        if m == "film_thickness":
            if cond == "film_abnormal":
                return "get_film_abnormal", [start, end, eqp]
            if trend:
                return "get_film_thickness_trend", [start, end, eqp]
            return "get_film_stats", [start, end, eqp]

        # 缺陷
        if m == "defect_count":
            if cond == "defect_high":
                return "get_defect_high", [start, end, eqp]
            return "get_defect_stats", [start, end, eqp]

        return "get_equipment_status", [eqp]

    # ---------- ④ 动态层：执行 ----------
    def _execute(self, sql: str, params: list) -> pd.DataFrame:
        """参数化查询（? 占位符），返回 Pandas DataFrame。"""
        conn = get_connection()
        try:
            return pd.read_sql_query(sql, conn, params=list(params))
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# 命令行冒烟测试
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ontology = OntologyDictionary()
    agent = FabQueryAgent(ontology=ontology, llm_config=LLMConfig(enabled=False))
    for q in [
        "帮我查一下 3号机 上周的良率趋势",
        "膜厚异常的晶圆有哪些？",
        "各设备的平均良率排名",
        f"LOT-{dt.date.today().year}-001 的工艺日志",
        "缺陷偏高的晶圆有哪些",
        "当前所有设备的状态",
    ]:
        t = agent.ask(q)
        print("=" * 80)
        print(f"问题: {q}")
        print(f"模式: {t.extraction_mode} | 模板: {t.template_name} | 行数: "
              f"{'—' if t.error else len(t.result)}")
        print(f"计划: {t.plan}")
        print(f"SQL : {t.sql[:120]}...")
        if t.error:
            print(f"错误: {t.error}")