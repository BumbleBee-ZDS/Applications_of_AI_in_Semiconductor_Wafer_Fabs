"""
FabCapacityAgent - 轻量LLM客户端模块 (Agent的"大脑")

纯 requests + python-dotenv 实现,不依赖 LangChain/重型框架。
支持两种 Provider,均走 OpenAI 兼容 /chat/completions 协议:
  - DeepSeek  (DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL)
  - 阿里云DashScope Qwen兼容端口 (DASHSCOPE_API_KEY / DASHSCOPE_BASE_URL)

功能:
  1) 文本生成/聊天补全 (chat)
  2) 文本向量化 (embeddings, 使用 qwen3.7-text-embedding)
  3) 结构化JSON抽取 (chat + JSON Mode / 解析兜底)
  4) 产能领域专用接口: generate_capacity_report / predict_with_llm / summarize_trend

调用失败/Key缺失时,全部有兜底默认值返回,保证纯本地也能跑通。
"""

import os
import re
import json
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

# 第三方
try:
    import requests
except ImportError:  # pragma: no cover - 极端兜底,安装阶段就应该有requests
    requests = None  # type: ignore

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None  # type: ignore

# 本地工具
from .helpers import get_logger, try_except, get_project_root, safe_div
from .constants import (
    PROCESS_NAME_CN,
    PRODUCT_NAME_CN,
    KPI_NAME_CN,
    ALL_PROCESSES,
)

# =============================================================================
# 基础配置 & 环境加载
# =============================================================================

logger = get_logger("LLMClient", level="INFO")

# 加载.env: 优先从 fab_capacity_agent/.env,其次上一级(仓库根)
if load_dotenv is not None:
    for env_candidate in [
        get_project_root() / ".env",
        get_project_root().parent / ".env",
    ]:
        if Path(env_candidate).exists():
            load_dotenv(dotenv_path=env_candidate, override=False)
            logger.info(f"已加载 .env: {env_candidate}")
            break
else:
    logger.warning("python-dotenv 未安装,跳过.env加载")


# =============================================================================
# Provider 枚举 & 默认模型
# =============================================================================

PROVIDER_DEEPSEEK = "deepseek"
PROVIDER_QWEN = "qwen"
PROVIDERS = [PROVIDER_DEEPSEEK, PROVIDER_QWEN]

DEFAULT_MODELS = {
    PROVIDER_DEEPSEEK: {
        "chat": "deepseek-chat",
        "embed": "deepseek-embed",  # deepseek目前文本嵌入走独立model,失败则回退qwen
    },
    PROVIDER_QWEN: {
        "chat": "qwen-plus",
        "embed": os.environ.get("QWEN_EMBEDDING_MODEL", "qwen3.7-text-embedding"),
    },
}


# =============================================================================
# LLMClient 主类
# =============================================================================

class LLMClient:
    """
    轻量LLM客户端,负责与DeepSeek/Qwen API交互。

    典型用法:
        llm = LLMClient(provider="deepseek")
        text  = llm.chat("请简述半导体制程中光刻工序的作用", max_tokens=256)
        emb   = llm.embed(["晶圆产能", "OEE优化"])    # 返回list[list[float]]
        data  = llm.chat_json("返回3种Logic产品的预计良率", schema=...)  # 返回dict
    """

    # ----------------------------------------------------------------- 初始化
    def __init__(
        self,
        provider: str = PROVIDER_DEEPSEEK,
        timeout: int = 30,
        max_retries: int = 2,
        temperature: float = 0.3,
    ) -> None:
        if provider not in PROVIDERS:
            raise ValueError(f"不支持的LLM Provider: {provider}, 可选 {PROVIDERS}")
        self.provider = provider
        self.timeout = timeout
        self.max_retries = max_retries
        self.temperature = temperature
        self.session = requests.Session() if requests is not None else None

        # 读取凭据
        self.api_key: str = ""
        self.base_url: str = ""
        self._load_credentials()

        # 健康状态(首次真正调用时再校验,避免构造函数慢)
        self._available: Optional[bool] = None

    # ----------------------------------------------------------------- 凭据
    def _load_credentials(self) -> None:
        """从环境变量加载对应Provider的API Key / Base URL。"""
        try:
            if self.provider == PROVIDER_DEEPSEEK:
                self.api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
                self.base_url = os.environ.get(
                    "DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"
                ).rstrip("/")
            else:  # qwen
                self.api_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
                self.base_url = os.environ.get(
                    "DASHSCOPE_BASE_URL",
                    "https://dashscope.aliyuncs.com/compatible-mode/v1",
                ).rstrip("/")
        except Exception as exc:
            logger.error(f"加载LLM凭据失败: {exc}")
            self.api_key, self.base_url = "", ""

    @property
    def is_configured(self) -> bool:
        """是否已经配置了API Key (不代表网络可达)。"""
        return bool(self.api_key and self.base_url and self.session is not None)

    # ----------------------------------------------------------------- 健康检查
    def check_available(self, force: bool = False) -> bool:
        """
        发送一个最小请求验证LLM是否可用,结果缓存。
        失败不会抛异常,仅返回False并记录日志。
        """
        if self._available is not None and not force:
            return self._available

        if not self.is_configured:
            logger.warning(f"LLM[{self.provider}] 未配置API Key,切换到纯本地模式。")
            self._available = False
            return False

        try:
            self.chat("你好,请只回复OK", max_tokens=4)
            self._available = True
            logger.info(f"LLM[{self.provider}] 连接正常 ✓")
        except Exception as exc:
            self._available = False
            logger.warning(f"LLM[{self.provider}] 连接失败: {exc}, 切换到纯本地模式。")
        return self._available

    # ----------------------------------------------------------------- Chat
    @try_except(default_return="")
    def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
    ) -> str:
        """
        文本补全接口。失败返回空串(由装饰器兜底)。

        Args:
            prompt: 用户提问/指令
            system: 可选System Prompt
            max_tokens: 最大生成长度
            temperature: 不传则使用实例默认值
            model: 不传则使用Provider默认聊天模型
        """
        if not self.is_configured:
            return ""

        model = model or DEFAULT_MODELS[self.provider]["chat"]
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": int(max_tokens),
            "temperature": float(temperature if temperature is not None else self.temperature),
            "stream": False,
        }
        return self._request_with_retry(
            f"{self.base_url}/chat/completions",
            payload,
            extract_fn=lambda r: r["choices"][0]["message"]["content"],
        )

    # ----------------------------------------------------------------- JSON抽取
    @try_except(default_return=None)
    def chat_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        schema_hint: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1500,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        让LLM输出可解析的JSON对象。失败/解析错误返回None。

        策略:
        1) 在Prompt里强制要求JSON,并附上schema示例
        2) 对返回文本做正则截取 ```json ... ``` 或第一个 {...}
        3) 解析失败返回None,由调用方兜底。
        """
        # 拼接强制JSON的指令
        force_json = (
            "\n\n请严格只输出一个可被json.loads解析的JSON对象,不要任何解释文字、Markdown标记。"
        )
        if schema_hint is not None:
            force_json += f"\nSchema 参考示例(按此结构返回):\n{json.dumps(schema_hint, ensure_ascii=False)}"

        combined_prompt = prompt + force_json
        combined_system = (system or "") + "\n你是一个半导体晶圆厂产能领域的专业AI助手,擅长输出结构化JSON。"

        text = self.chat(
            prompt=combined_prompt,
            system=combined_system.strip() or None,
            max_tokens=max_tokens,
            **kwargs,
        )
        if not text:
            return None

        return self._parse_json_robust(text)

    # ----------------------------------------------------------------- Embedding
    @try_except(default_return=[])
    def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        """
        文本向量化,默认用 qwen3.7-text-embedding (强制走DashScope,因为DeepSeek嵌入能力偏弱)。

        如果未配置Qwen Key或调用失败,返回空列表(上游可以用TF-IDF等替代方案兜底)。
        """
        if not texts:
            return []

        # 强制走Qwen(除非Provider不是qwen且用户手动传了model)
        use_provider = self.provider
        use_model = model or DEFAULT_MODELS[use_provider]["embed"]
        api_key = self.api_key
        base_url = self.base_url

        if use_provider != PROVIDER_QWEN:
            # 没有单独model指定时,切换到Qwen的嵌入
            qwen_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
            qwen_base = os.environ.get(
                "DASHSCOPE_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ).rstrip("/")
            if qwen_key:
                api_key, base_url, use_provider = qwen_key, qwen_base, PROVIDER_QWEN
                use_model = os.environ.get("QWEN_EMBEDDING_MODEL", "qwen3.7-text-embedding")

        if not (api_key and base_url and self.session is not None):
            return []

        # DashScope embeddings 的 input 格式兼容 OpenAI: string / array[string]
        payload = {
            "model": use_model,
            "input": texts if len(texts) > 1 else texts[0],
            "encoding_format": "float",
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        def _extract(resp: Dict[str, Any]) -> List[List[float]]:
            data = resp.get("data") or []
            # 原接口可能不按输入顺序返回,根据index重新排序
            data_sorted = sorted(data, key=lambda x: x.get("index", 0))
            return [list(d["embedding"]) for d in data_sorted if "embedding" in d]

        return self._request_with_retry(
            f"{base_url}/embeddings",
            payload,
            headers=headers,
            extract_fn=_extract,
        )

    # =========================================================================
    # 产能领域专用接口 (Domain-Specific APIs)
    # 这些接口即使在LLM不可用时,也会返回基于规则的"假"结构化答案,确保链路不中断。
    # =========================================================================

    # ----------------------------------------------------------------- 趋势摘要
    def summarize_trend(
        self,
        kpi_data: Dict[str, List[float]],
        period_desc: str = "近30天",
    ) -> str:
        """
        让LLM用自然语言总结一段KPI趋势。LLM不可用时走本地模板兜底。

        Args:
            kpi_data: {kpi_key: [数值序列]} ,如 {"oee":[0.82,0.83,...], "daily_output":[...]}
            period_desc: 描述时段的文案,如 "近30天"
        """
        # 构造摘要数据(只取首尾、均值、趋势方向,控制输入token量)
        digest = {}
        for k, seq in kpi_data.items():
            if not seq:
                continue
            first, last = float(seq[0]), float(seq[-1])
            avg = sum(seq) / len(seq)
            trend = "上升" if last > first * 1.02 else ("下降" if last < first * 0.98 else "平稳")
            name = KPI_NAME_CN.get(k, k)
            digest[name] = {
                "起始": round(first, 3),
                "最新": round(last, 3),
                "平均": round(avg, 3),
                "趋势": trend,
            }

        prompt = (
            f"以下是半导体晶圆厂{period_desc}的关键产能KPI统计摘要(比例类已为0~1小数):\n"
            f"{json.dumps(digest, ensure_ascii=False, indent=2)}\n"
            "请用不超过200字的专业中文,从产能健康度、瓶颈风险、改善方向三个角度给出简洁分析结论。"
        )
        text = self.chat(prompt, system="你是资深半导体Fab工业工程师,擅长用简洁专业语言分析产能数据。")

        if text:
            return text
        # ===== 本地兜底模板 =====
        lines = [f"【{period_desc}产能趋势本地分析】"]
        for name, info in digest.items():
            lines.append(f"· {name}: 最新{info['最新']}, 平均{info['平均']}, 趋势{info['趋势']}")
        lines.append("· 结论: 建议重点关注下降/波动较大指标,核查对应工序设备OEE与PM执行情况。")
        return "\n".join(lines)

    # ----------------------------------------------------------------- LLM增强产能预测
    def predict_with_llm(
        self,
        history_daily: List[Dict[str, Any]],
        horizon_days: int = 7,
    ) -> Dict[str, List[float]]:
        """
        用LLM增强产能预测,输出 horizon_days 天的日产出预测与置信区间[lower,upper]。

        LLM不可用时返回空字典,交由 Predictor 回退到纯统计模型(LinearRegression + MA)。

        Args:
            history_daily: [{"date": "2026-08-01", "output": 1200, "oee": 0.81}, ...]
            horizon_days: 预测天数

        Returns:
            {"predicted": [...], "lower": [...], "upper": [...]} 长度等于horizon_days
        """
        if not self.check_available() or not history_daily:
            return {}

        # 控制token量: 只取最近30条 + 5条一条汇总
        recent = history_daily[-30:]
        prompt = (
            f"以下是半导体Fab最近{len(recent)}天的日产出(单位:片,300mm晶圆)和OEE数据:\n"
            + "\n".join(
                f"- {d['date']}: 产出{int(d.get('output',0))}片, OEE={float(d.get('oee',0)):.3f}"
                for d in recent
            )
            + f"\n\n请基于半导体行业周期性(周内波动、良率爬坡、PM计划)专业知识,预测未来{horizon_days}天的日产出。"
            "输出严格JSON,结构: "
            '{"predicted":[按天的产出数值],"lower":[置信下限],"upper":[置信上限]}。'
            "每个数组长度必须等于" + str(horizon_days) + "。"
        )
        result = self.chat_json(prompt)
        if not result:
            return {}

        # 格式校验 & 裁剪
        out = {}
        for k in ("predicted", "lower", "upper"):
            arr = result.get(k)
            if isinstance(arr, list) and len(arr) >= horizon_days:
                out[k] = [float(x) for x in arr[:horizon_days]]
        if len(out) == 3:
            return out
        return {}

    # ----------------------------------------------------------------- 生成产能分析报告
    def generate_capacity_report(
        self,
        snapshot: Dict[str, Any],
        bottlenecks: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]],
    ) -> str:
        """
        生成一份完整Markdown格式产能分析报告。LLM不可用时走本地模板。
        """
        # default=str 兜底: 任何非原生类型(numpy.bool_/int64/float64/Timestamp)转字符串,避免序列化失败
        prompt = (
            "请基于以下Fab当前状态快照、瓶颈分析、异常列表,生成一份结构化Markdown产能分析报告,"
            "包含:1)执行摘要 2)关键KPI看板 3)瓶颈诊断 4)异常预警 5)行动建议。字数800字内,专业且可操作。\n\n"
            f"[状态快照]\n{json.dumps(snapshot, ensure_ascii=False, indent=2, default=str)}\n\n"
            f"[瓶颈工序]\n{json.dumps(bottlenecks, ensure_ascii=False, indent=2, default=str)}\n\n"
            f"[异常告警]\n{json.dumps(anomalies, ensure_ascii=False, indent=2, default=str)}\n"
        )
        text = self.chat(
            prompt,
            system="你是半导体Fab资深产能规划专家,熟悉8寸/12寸晶圆厂OEE、瓶颈分析、WIP控制与排产优化。",
            max_tokens=1500,
        )
        if text:
            return text
        # ===== 本地兜底模板 =====
        md = ["# 📋 Fab产能分析报告 (本地模板兜底)", ""]
        md.append("## 1. 执行摘要")
        md.append(f"- 当前全厂OEE: **{snapshot.get('overall_oee','N/A')}**")
        md.append(f"- 在制品WIP: **{snapshot.get('wip_total','N/A')}** 片")
        md.append(f"- 24h产出: **{snapshot.get('daily_output','N/A')}** 片")
        md.append("")
        md.append("## 2. 瓶颈诊断")
        for b in bottlenecks[:3]:
            md.append(f"- **{PROCESS_NAME_CN.get(b.get('process','?'),b.get('process','?'))}** "
                      f"利用率 {b.get('utilization','?')}%, 建议: 增加设备或调整PM窗口")
        if not bottlenecks:
            md.append("- 暂无明显瓶颈工序,产线负载均衡。")
        md.append("")
        md.append("## 3. 异常预警")
        for a in anomalies[:5]:
            md.append(f"- {a.get('message','未知异常')} (工序:{a.get('process','全站')})")
        if not anomalies:
            md.append("- 未检测到显著异常。")
        md.append("")
        md.append("## 4. 行动建议")
        md.append("1. 持续跟踪瓶颈工序OEE三要素(A/P/Q),分解改进空间。")
        md.append("2. 针对异常设备,核查Down事件频率与MTTR。")
        md.append("3. WIP若偏高,建议检查前道工序节拍匹配度。")
        return "\n".join(md)

    # =========================================================================
    # 内部实现
    # =========================================================================

    def _request_with_retry(
        self,
        url: str,
        payload: Dict[str, Any],
        extract_fn,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        发送HTTP POST + 指数退避重试 + 解析返回。
        任何网络/解析错误都会抛异常(由上层@try_except兜底)。
        """
        if self.session is None:
            raise RuntimeError("requests 未安装,无法发送LLM请求")

        headers = headers or {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                if resp.status_code == 429 or resp.status_code >= 500:
                    # 限流/服务端错误 -> 重试
                    raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                resp.raise_for_status()
                data = resp.json()
                if "error" in data:
                    raise RuntimeError(f"API返回错误: {data['error']}")
                return extract_fn(data)
            except Exception as exc:
                last_exc = exc
                wait_sec = 2 ** (attempt - 1)
                logger.warning(
                    f"LLM请求第{attempt}次失败: {type(exc).__name__}: {exc}. "
                    f"{attempt < self.max_retries and f'{wait_sec}s后重试...' or '已耗尽重试。'}"
                )
                if attempt < self.max_retries:
                    time.sleep(wait_sec)
        # 所有重试耗尽
        raise last_exc or RuntimeError("LLM请求未知失败")

    @staticmethod
    def _parse_json_robust(text: str) -> Optional[Dict[str, Any]]:
        """
        尽力从LLM返回的任意文本中解析出一个JSON对象。
        策略: 优先 ```json ... ``` -> 其次最大 {...} 匹配 -> 最后全串loads
        """
        if not text:
            return None
        s = text.strip()
        # 1) Markdown 代码块
        m = re.search(r"```(?:json)?\s*(.+?)\s*```", s, flags=re.DOTALL | re.IGNORECASE)
        if m:
            candidate = m.group(1)
            try:
                return json.loads(candidate)
            except Exception:
                pass
        # 2) 最外层大括号
        first, last = s.find("{"), s.rfind("}")
        if first != -1 and last != -1 and last > first:
            candidate = s[first : last + 1]
            try:
                return json.loads(candidate)
            except Exception:
                pass
        # 3) 整体loads
        try:
            return json.loads(s)
        except Exception:
            return None


# =============================================================================
# 便捷单例 (全项目共用一个LLM Client,减少重复初始化)
# =============================================================================

_llm_instance: Optional[LLMClient] = None


def get_llm(provider: str = PROVIDER_DEEPSEEK, **kwargs) -> LLMClient:
    """获取/创建全局单例LLM客户端。"""
    global _llm_instance
    if _llm_instance is None or _llm_instance.provider != provider:
        _llm_instance = LLMClient(provider=provider, **kwargs)
    return _llm_instance


# =============================================================================
# 模块快速自检
# =============================================================================

if __name__ == "__main__":
    client = get_llm(provider=PROVIDER_DEEPSEEK)
    print(f"Provider: {client.provider}")
    print(f"已配置Key: {'YES' if client.is_configured else 'NO'}")
    ok = client.check_available()
    print(f"实际可达: {'YES' if ok else 'NO (本地模式)'}")

    # 领域接口兜底测试(即使LLM不可用,也应有输出)
    sample_kpi = {
        "oee": [0.80, 0.82, 0.83, 0.81, 0.85],
        "daily_output": [1100, 1150, 1200, 1120, 1250],
    }
    print("\n== 趋势摘要 ==")
    print(client.summarize_trend(sample_kpi, period_desc="最近5天"))

    print("\n== 嵌入维度(前2个) ==")
    emb = client.embed(["光刻工序是产能瓶颈"])
    if emb:
        print(f"维度: {len(emb[0])}, 前5值: {emb[0][:5]}")
    else:
        print("(嵌入未返回,属正常兜底)")
