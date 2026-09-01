"""
FabCapacityAgent - 产能预测服务 (Predictor)

预测组合策略 (Hybrid Ensemble):
  1) 移动平均 MA(window)     - 平滑短期波动, 捕捉周内季节性
  2) 线性回归 LinearRegression - 捕捉长期趋势 (sklearn)
  3) LLM 增强 predict_with_llm  - 结合行业先验给出置信区间
  4) 三者加权融合 -> 最终 predicted / lower / upper (置信区间)

支持两个时间维度:
  forecast_short_days = 7  (短期, 用于生产排产)
  forecast_long_days  = 30 (中长期, 用于产能规划)
"""

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
except Exception:  # pragma: no cover - sklearn 缺失时降级为纯 numpy polyfit
    LinearRegression = None  # type: ignore

from models.capacity import DailyOutputDAO, DailyOutputRow
from utils.helpers import (
    get_logger,
    try_except,
    safe_div,
    safe_round,
    get_config,
    date_range,
)
from utils.llm_client import get_llm, PROVIDER_DEEPSEEK, LLMClient

logger = get_logger("Predictor", level="INFO")


# =============================================================================
# 预测结果数据类
# =============================================================================

@dataclass
class ForecastResult:
    """结构化预测结果。"""
    target: str = "output_wafers"                   # 预测的目标列名
    horizon_days: int = 7                           # 预测天数
    history_days: int = 30                          # 使用的历史天数
    method: str = "hybrid"                          # hybrid/ma/lr/llm

    # 时间轴
    history_dates: List[dt.date] = field(default_factory=list)     # 历史日期
    history_values: List[float] = field(default_factory=list)      # 历史真实值
    future_dates: List[dt.date] = field(default_factory=list)      # 未来日期
    predicted: List[float] = field(default_factory=list)           # 预测值(中值)
    lower_ci: List[float] = field(default_factory=list)            # 置信区间下界
    upper_ci: List[float] = field(default_factory=list)            # 置信区间上界

    # 方法明细(便于调试/展示)
    ma_predicted: List[float] = field(default_factory=list)        # 移动平均预测
    lr_predicted: List[float] = field(default_factory=list)        # 线性回归预测
    llm_predicted: List[float] = field(default_factory=list)       # LLM预测(若无则空)

    # 评估指标 (回测)
    mape: float = 0.0                                              # 平均绝对百分比误差
    used_llm: bool = False

    def to_dataframe(self) -> pd.DataFrame:
        """转 DataFrame, 便于直接传给 Plotly 绘图。"""
        rows = []
        # 历史段
        for d, v in zip(self.history_dates, self.history_values):
            rows.append({
                "date": d, "value": float(v), "type": "历史实际",
                "lower": None, "upper": None,
            })
        # 预测段
        for i, d in enumerate(self.future_dates):
            rows.append({
                "date": d,
                "value": float(self.predicted[i]),
                "type": "预测值",
                "lower": float(self.lower_ci[i]) if i < len(self.lower_ci) else None,
                "upper": float(self.upper_ci[i]) if i < len(self.upper_ci) else None,
            })
        return pd.DataFrame(rows)

    def summary(self) -> Dict[str, Any]:
        """聚合摘要(给 Agent 决策用)。"""
        total_pred = safe_round(sum(self.predicted), 0)
        avg_pred = safe_round(safe_div(total_pred, max(1, len(self.predicted))), 2)
        return {
            "target": self.target,
            "horizon_days": self.horizon_days,
            "history_days": self.history_days,
            "method": self.method,
            "used_llm": self.used_llm,
            "total_predicted_wafers": int(total_pred),
            "avg_daily_predicted": avg_pred,
            "min_predicted": safe_round(min(self.predicted) if self.predicted else 0, 0),
            "max_predicted": safe_round(max(self.predicted) if self.predicted else 0, 0),
            "avg_confidence_width_pct": safe_round(
                safe_div(
                    np.mean([u - l for u, l in zip(self.upper_ci, self.lower_ci)]) if self.upper_ci else 0,
                    max(1, avg_pred),
                    default=0,
                ) * 100,
                1,
            ),
            "mape_pct": safe_round(self.mape * 100, 2),
        }


# =============================================================================
# Predictor 主类
# =============================================================================

class Predictor:
    """
    日产出 / OEE 等时间序列的预测器。

    用法:
        pred = Predictor()
        r = pred.forecast_output(horizon_days=7)
        print(r.summary())
        df = r.to_dataframe()  # 直接给 Plotly
    """

    def __init__(
        self,
        daily_dao: Optional[DailyOutputDAO] = None,
        llm: Optional[LLMClient] = None,
    ) -> None:
        self.daily_dao = daily_dao or DailyOutputDAO()

        # 配置
        self.ma_window: int = int(get_config("prediction", "moving_average_window", default=7))
        self.lr_window: int = int(get_config("prediction", "linear_regression_window", default=30))
        self.seasonality: int = int(get_config("prediction", "seasonality_period", default=7))
        self.confidence_level: float = float(
            get_config("agent", "decision_agent", "confidence_level", default=0.95)
        )
        # MA / LR / LLM 融合权重 (可调)
        self.w_ma: float = 0.35
        self.w_lr: float = 0.40
        self.w_llm: float = 0.25

        # LLM 客户端 (可选, 无 Key 则自动不启用)
        self.llm = llm
        if self.llm is None and get_config("prediction", "llm_enhancement", "enabled", default=False):
            try:
                provider = get_config("prediction", "llm_enhancement", "provider", default=PROVIDER_DEEPSEEK)
                self.llm = get_llm(provider=provider)
            except Exception as exc:
                logger.warning(f"LLM初始化失败, 不启用LLM增强: {exc}")
                self.llm = None

    # =========================================================================
    # 主入口: 产出预测
    # =========================================================================

    @try_except(default_return=ForecastResult())
    def forecast_output(
        self,
        horizon_days: int = 7,
        history_days: int = 60,
        target: str = "output_wafers",
        product_type: str = "ALL",
        use_llm: bool = True,
    ) -> ForecastResult:
        """
        预测未来 N 天的日产出。

        Args:
            horizon_days: 预测天数 (通常 7 或 30)
            history_days: 用于建模的历史天数
            target: 预测目标列名 (output_wafers / avg_oee / completed_lots)
            product_type: 产品维度 ("ALL" 或 Logic_A / Logic_B / Memory_C)
            use_llm: 是否尝试 LLM 增强(若配置允许)

        Returns:
            ForecastResult 结构化结果
        """
        end = dt.date.today()
        start = end - dt.timedelta(days=history_days - 1)

        df = self.daily_dao.between(start, end, product_type=product_type)
        if df.empty:
            logger.warning("无可用日产出数据, 返回空预测")
            return ForecastResult(target=target, horizon_days=horizon_days, history_days=history_days)

        # 取目标列
        if target not in df.columns:
            target = "output_wafers"
        series = df[target].astype(float).values
        dates_hist = pd.to_datetime(df["stat_date"]).dt.date.tolist()

        # 构造未来日期轴
        last_date = dates_hist[-1] if dates_hist else end
        dates_future = [(last_date + dt.timedelta(days=i + 1)) for i in range(horizon_days)]

        result = ForecastResult(
            target=target,
            horizon_days=horizon_days,
            history_days=history_days,
            history_dates=dates_hist,
            history_values=[float(v) for v in series],
            future_dates=dates_future,
        )

        # ------- 方法1: 移动平均 MA(ma_window) 带周内季节性 -------
        ma_pred = self._predict_ma(series, horizon_days)
        result.ma_predicted = [safe_round(v, 2) for v in ma_pred]

        # ------- 方法2: 线性回归 (时间作为特征 + 周内周期性 one-hot) -------
        lr_pred = self._predict_linear(series, horizon_days)
        result.lr_predicted = [safe_round(v, 2) for v in lr_pred]

        # ------- 方法3: LLM 增强 (可选) -------
        llm_pred_dict: Dict[str, List[float]] = {}
        if use_llm and self.llm is not None:
            llm_pred_dict = self._call_llm_forecast(
                dates_hist, series, horizon_days, target
            )
            if llm_pred_dict:
                result.llm_predicted = [safe_round(v, 2) for v in llm_pred_dict.get("predicted", [])]
                result.used_llm = True

        # ------- 加权融合 -------
        fused, lower, upper = self._ensemble(
            ma=ma_pred,
            lr=lr_pred,
            llm=llm_pred_dict,
            series=series,
            horizon=horizon_days,
        )
        result.predicted = [safe_round(max(0.0, v), 2) for v in fused]
        result.lower_ci = [safe_round(max(0.0, v), 2) for v in lower]
        result.upper_ci = [safe_round(max(0.0, v), 2) for v in upper]
        if not result.llm_predicted:
            # LLM 没命中, 调整 MA+LR 权重为 1
            result.method = "hybrid(ma+lr)"
        else:
            result.method = "hybrid(ma+lr+llm)"

        # ------- 回测 MAPE (用最近 horizon_days 做 Walk Forward) -------
        result.mape = self._walk_forward_mape(series, horizon_days)

        logger.info(
            f"[{target}] {history_days}天历史 -> {horizon_days}天预测完成. "
            f"方法={result.method}, MAPE={result.mape*100:.2f}%, "
            f"预测总量={int(sum(result.predicted))}片"
        )
        return result

    # =========================================================================
    # 方法实现
    # =========================================================================

    def _predict_ma(self, series: np.ndarray, horizon: int) -> np.ndarray:
        """
        移动平均 + 周内季节性乘法因子。
        取最后 ma_window 天均值作为基准, 再乘过去 4 周同星期的季节指数。
        """
        s = np.asarray(series, dtype=float)
        if len(s) == 0:
            return np.zeros(horizon)
        # 基准 MA
        tail = s[-min(len(s), max(3, self.ma_window)):]
        base = float(np.nanmean(tail)) if np.isfinite(tail).any() else 0.0

        # 周内季节因子 (如果数据>=14天则计算, 否则=1.0)
        seasonal = np.ones(horizon)
        if len(s) >= 14:
            # 最后 28 天 (4周)
            win = s[-min(len(s), self.seasonality * 4):]
            # 按星期索引 reshape -> 每日均值 / 总体均值
            n_full_weeks = len(win) // self.seasonality
            if n_full_weeks >= 2:
                win = win[-n_full_weeks * self.seasonality:]
                weekly = win.reshape(n_full_weeks, self.seasonality)
                overall_mean = weekly.mean() or 1.0
                dow_mean = weekly.mean(axis=0) / overall_mean
                # 未来每天星期索引
                today_idx = len(s) % self.seasonality
                for i in range(horizon):
                    w = (today_idx + i + 1) % self.seasonality
                    seasonal[i] = float(dow_mean[w]) if w < len(dow_mean) else 1.0
        return np.full(horizon, base) * seasonal

    def _predict_linear(self, series: np.ndarray, horizon: int) -> np.ndarray:
        """
        线性回归: t + sin(2πt/7) + cos(2πt/7) 作为特征。
        sklearn 不可用时降级为 numpy.polyfit(deg=1)。
        """
        s = np.asarray(series, dtype=float)
        n = len(s)
        if n < 5:
            return np.full(horizon, float(np.nanmean(s)) if n else 0.0)
        # 训练窗口: 取最近 lr_window
        train_n = min(n, max(5, self.lr_window))
        y_train = s[-train_n:]
        t_train = np.arange(n - train_n, n).reshape(-1, 1).astype(float)

        t_future = np.arange(n, n + horizon).reshape(-1, 1).astype(float)

        def build_features(t: np.ndarray) -> np.ndarray:
            """特征: t + 周内正弦/余弦。"""
            feats = [t.reshape(-1).astype(float)]
            period = float(self.seasonality)
            feats.append(np.sin(2 * np.pi * t.reshape(-1) / period))
            feats.append(np.cos(2 * np.pi * t.reshape(-1) / period))
            return np.column_stack(feats)

        X_train = build_features(t_train)
        X_future = build_features(t_future)

        if LinearRegression is not None:
            try:
                pipe = Pipeline([
                    ("sc", StandardScaler()),
                    ("lr", LinearRegression()),
                ])
                pipe.fit(X_train, y_train)
                return pipe.predict(X_future).astype(float)
            except Exception as exc:
                logger.warning(f"sklearn线性回归失败, 降级为np.polyfit: {exc}")

        # Fallback: 简单一次多项式拟合 (只用t)
        coef = np.polyfit(t_train.reshape(-1), y_train, deg=1)
        return np.polyval(coef, t_future.reshape(-1)).astype(float)

    def _call_llm_forecast(
        self,
        dates: List[dt.date],
        values: np.ndarray,
        horizon: int,
        target: str,
    ) -> Dict[str, List[float]]:
        """调用 LLM (DeepSeek/Qwen) 做增强预测, 返回 dict 或 {}。"""
        try:
            if self.llm is None:
                return {}
            # 构造结构化输入
            recent_n = min(30, len(dates))
            history_daily = []
            for i in range(len(dates) - recent_n, len(dates)):
                history_daily.append({
                    "date": str(dates[i]),
                    "output": float(values[i]),
                    "oee": safe_round(float(values[i]) / max(1.0, float(max(values[-30:]) or 1.0)), 3),
                })
            return self.llm.predict_with_llm(history_daily, horizon_days=horizon) or {}
        except Exception as exc:
            logger.warning(f"LLM增强预测失败: {exc}")
            return {}

    def _ensemble(
        self,
        ma: np.ndarray,
        lr: np.ndarray,
        llm: Dict[str, List[float]],
        series: np.ndarray,
        horizon: int,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """加权融合三种预测 + 估计置信区间。"""
        # 有效方法个数, 重归一化权重
        has_llm = bool(llm and llm.get("predicted"))
        w = [self.w_ma, self.w_lr, self.w_llm if has_llm else 0.0]
        ws = sum(w) or 1.0
        w = [x / ws for x in w]

        pred = w[0] * np.asarray(ma, dtype=float)
        pred += w[1] * np.asarray(lr, dtype=float)
        if has_llm:
            llm_arr = np.asarray(llm["predicted"], dtype=float)
            # 长度对齐
            if len(llm_arr) >= horizon:
                llm_arr = llm_arr[:horizon]
            elif len(llm_arr) < horizon:
                llm_arr = np.pad(llm_arr, (0, horizon - len(llm_arr)), mode="edge")
            pred += w[2] * llm_arr

        # 置信区间: 基于历史残差标准差 × Z分位 (confidence_level)
        # 近似: 1-alpha=0.95 -> Z≈1.96
        z_map = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_map.get(round(self.confidence_level, 2), 1.96)
        # 残差: 过去30天MA+LR融合 vs 真实值 的std
        s = np.asarray(series, dtype=float)
        if len(s) >= 14:
            # 简单估算: 历史标准差 * sqrt(1+1/n) 随预测天数增长
            hist_std = float(np.nanstd(s[-min(30, len(s)):]) or 1.0)
            growth = np.sqrt(np.linspace(1.0, 1.0 + horizon / 7.0, horizon))
            half_width = z * hist_std * 0.6 * growth
        else:
            half_width = np.full(horizon, max(1.0, float(np.nanmean(s)) * 0.08))

        lower = pred - half_width
        upper = pred + half_width

        # 如果 LLM 给了置信区间, 且更可信, 则取交集合并 (更保守)
        if has_llm:
            ll_lower = np.asarray(llm.get("lower", []), dtype=float)
            ll_upper = np.asarray(llm.get("upper", []), dtype=float)
            if len(ll_lower) >= horizon:
                lower = np.minimum(lower, ll_lower[:horizon])
                upper = np.maximum(upper, ll_upper[:horizon])

        return pred, lower, upper

    def _walk_forward_mape(self, series: np.ndarray, horizon: int) -> float:
        """
        Walk-Forward 回测 MAPE (简化版):
        把最后 horizon 天作为测试集, 用之前的数据做一次 MA+LR 预测, 计算 MAPE。
        """
        s = np.asarray(series, dtype=float)
        if len(s) <= horizon * 2:
            return 0.0
        test = s[-horizon:]
        train = s[:-horizon]
        ma = self._predict_ma(train, horizon)
        lr = self._predict_linear(train, horizon)
        pred = 0.5 * ma + 0.5 * lr
        # 避免除零
        denom = np.where(np.abs(test) < 1e-6, 1.0, np.abs(test))
        ape = np.abs((pred - test) / denom)
        return safe_round(float(np.mean(ape)), 4)

    # =========================================================================
    # 便捷接口: 多目标同时预测 (给 DecisionAgent)
    # =========================================================================

    @try_except(default_return={})
    def forecast_multi(
        self,
        targets: List[str],
        horizon_days: int = 30,
        history_days: int = 90,
    ) -> Dict[str, ForecastResult]:
        """
        同时预测多个目标列。

        Args:
            targets: ["output_wafers", "completed_lots", "avg_oee"]
            horizon_days: 预测天数
            history_days: 历史天数

        Returns:
            {target: ForecastResult}
        """
        out: Dict[str, ForecastResult] = {}
        for t in targets:
            out[t] = self.forecast_output(
                horizon_days=horizon_days,
                history_days=history_days,
                target=t,
            )
        return out


# =============================================================================
# 单例
# =============================================================================

_predictor_instance: Optional[Predictor] = None


def get_predictor() -> Predictor:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = Predictor()
    return _predictor_instance


# =============================================================================
# 自检
# =============================================================================

if __name__ == "__main__":
    pred = get_predictor()
    print("=== 7天产出预测 ===")
    r7 = pred.forecast_output(horizon_days=7, history_days=60, use_llm=False)
    print(r7.to_dataframe().tail(14).to_string(index=False))
    print()
    print("7天摘要:", r7.summary())
    print()
    print("=== 30天产出预测 (含LLM若可用) ===")
    r30 = pred.forecast_output(horizon_days=30, history_days=90)
    print("30天摘要:", r30.summary())
