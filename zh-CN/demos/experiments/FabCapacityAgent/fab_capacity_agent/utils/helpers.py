"""
FabCapacityAgent - 通用工具函数模块

提供配置加载、日期/时间处理、数值格式化、日志配置、错误处理等跨模块辅助方法。
"""

import os
import sys
import logging
import time
import datetime as dt
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
from functools import wraps
from decimal import Decimal, ROUND_HALF_UP

import yaml
import numpy as np
import pandas as pd

# 本地常量导入
from .constants import (
    FILE_SETTINGS,
    FORMAT_PCT,
    FORMAT_NUM_2,
    FORMAT_NUM_INT,
    FORMAT_DATETIME,
    FORMAT_DATE,
    FORMAT_TIME,
    KPI_UNIT,
    KPI_NAME_CN,
    PROCESS_NAME_CN,
    EQUIP_STATUS_NAME_CN,
    PRODUCT_NAME_CN,
)

# =============================================================================
# 路径与项目根定位
# =============================================================================

def get_project_root() -> Path:
    """
    获取fab_capacity_agent项目根目录绝对路径。
    
    策略: 以当前helpers.py所在目录向上回溯一层作为项目根。
    这样无论脚本是从哪个cwd启动,路径引用都不会出错。
    
    Returns:
        Path: fab_capacity_agent目录的绝对Path对象
    """
    return Path(__file__).resolve().parent.parent


def resolve_path(relative_path: str) -> Path:
    """
    将相对路径(相对于项目根)解析为绝对Path。
    
    Args:
        relative_path: 相对路径,如 "config/settings.yaml"
    
    Returns:
        解析后的绝对Path
    """
    return get_project_root() / relative_path


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在,不存在则递归创建。
    
    Args:
        path: 目录路径
    
    Returns:
        处理后的Path对象
    """
    p = Path(path)
    if not p.is_absolute():
        p = resolve_path(str(p))
    p.mkdir(parents=True, exist_ok=True)
    return p


# =============================================================================
# 配置加载 (YAML settings)
# =============================================================================

_settings_cache: Optional[Dict[str, Any]] = None


def load_settings(force_reload: bool = False) -> Dict[str, Any]:
    """
    加载并缓存config/settings.yaml配置。
    
    Args:
        force_reload: 是否忽略缓存强制重新加载
    
    Returns:
        完整配置字典
    
    Raises:
        FileNotFoundError: 配置文件不存在时抛出
    """
    global _settings_cache
    if _settings_cache is not None and not force_reload:
        return _settings_cache

    settings_path = resolve_path(FILE_SETTINGS)
    if not settings_path.exists():
        raise FileNotFoundError(
            f"配置文件不存在: {settings_path}. 请确认项目结构是否正确。"
        )

    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            _settings_cache = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"配置文件YAML解析失败: {exc}") from exc

    return _settings_cache


def get_config(*keys: str, default: Any = None) -> Any:
    """
    按层级键安全读取配置,不存在时返回default。
    
    使用示例:
        db_path = get_config("database", "path", default="data/fab.db")
    
    Args:
        *keys: 配置层级键序列
        default: 找不到时的默认值
    
    Returns:
        配置值或default
    """
    cfg = load_settings()
    cur: Any = cfg
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur


# =============================================================================
# 日志工具
# =============================================================================

_logger_cache: Dict[str, logging.Logger] = {}


def get_logger(name: str = "FabCapacityAgent", level: str = "INFO") -> logging.Logger:
    """
    获取命名Logger,带StreamHandler,避免重复添加Handler。
    
    Args:
        name: Logger名称
        level: 日志级别(DEBUG/INFO/WARNING/ERROR/CRITICAL)
    
    Returns:
        配置好的Logger实例
    """
    if name in _logger_cache:
        return _logger_cache[name]

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    _logger_cache[name] = logger
    return logger


# =============================================================================
# 时间与日期工具
# =============================================================================

def now() -> dt.datetime:
    """获取当前时间(本地timezone-naive,与模拟数据保持一致)。"""
    return dt.datetime.now()


def today_str() -> str:
    """获取今日日期字符串 YYYY-MM-DD。"""
    return dt.date.today().strftime(FORMAT_DATE)


def now_str() -> str:
    """获取当前日期时间字符串 YYYY-MM-DD HH:MM:SS。"""
    return now().strftime(FORMAT_DATETIME)


def parse_datetime(s: Any) -> Optional[dt.datetime]:
    """
    宽容地解析多种日期时间格式为datetime。
    
    支持: datetime/date/np.datetime64/pd.Timestamp/常见字符串格式
    """
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return None
    if isinstance(s, dt.datetime):
        return s
    if isinstance(s, dt.date):
        return dt.datetime(s.year, s.month, s.day)
    if isinstance(s, pd.Timestamp):
        return s.to_pydatetime()
    if isinstance(s, np.datetime64):
        try:
            return pd.Timestamp(s).to_pydatetime()
        except Exception:
            return None
    if isinstance(s, str):
        for fmt in [FORMAT_DATETIME, "%Y-%m-%d %H:%M", FORMAT_DATE, "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"]:
            try:
                return dt.datetime.strptime(s.strip(), fmt)
            except (ValueError, AttributeError):
                continue
    return None


def days_between(a: Any, b: Any) -> float:
    """计算两个时间点之间的天数差(b - a),失败则返回NaN。"""
    da, db = parse_datetime(a), parse_datetime(b)
    if da is None or db is None:
        return float("nan")
    return (db - da).total_seconds() / 86400.0


def hours_between(a: Any, b: Any) -> float:
    """计算两个时间点之间的小时差(b - a),失败则返回NaN。"""
    da, db = parse_datetime(a), parse_datetime(b)
    if da is None or db is None:
        return float("nan")
    return (db - da).total_seconds() / 3600.0


def date_range(start: Any, end: Any, freq: str = "D") -> pd.DatetimeIndex:
    """生成安全的pd.date_range,参数容错。"""
    s = parse_datetime(start) or now() - dt.timedelta(days=1)
    e = parse_datetime(end) or now()
    return pd.date_range(s, e, freq=freq)


# =============================================================================
# 数值格式化与舍入
# =============================================================================

def safe_round(value: Any, digits: int = 2) -> float:
    """
    安全的四舍五入,处理None/NaN/字符串。
    
    使用Decimal实现真正的四舍五入(ROUND_HALF_UP),避免Python bankers rounding偏差。
    """
    try:
        if value is None:
            return 0.0
        if isinstance(value, float) and np.isnan(value):
            return 0.0
        d = Decimal(str(value)).quantize(Decimal(f"0.{'0'*digits}"), rounding=ROUND_HALF_UP)
        return float(d)
    except (ValueError, TypeError, ArithmeticError):
        return 0.0


def to_pct(value: Any, digits: int = 2) -> str:
    """将0~1之间的小数格式化为百分比字符串,如 0.852 -> '85.20%'。"""
    return FORMAT_PCT.format(safe_round(value, digits + 2))


def format_kpi(kpi_key: str, value: Any) -> str:
    """
    根据KPI类型自动格式化显示字符串。
    
    Args:
        kpi_key: KPI常量Key(见constants.KPI_*)
        value: 原始数值
    
    Returns:
        格式化后的带单位字符串,如 "85.20%" / "1,234 片/h"
    """
    v = safe_round(value, 2)
    unit = KPI_UNIT.get(kpi_key, "")
    if kpi_key in ("availability", "performance", "quality", "oee",
                   "utilization", "bottleneck_rate"):
        # 百分比类KPI: 原始存0~1小数,显示乘以100
        return f"{safe_round(v * 100, 2):.2f}%"
    if kpi_key in ("wip", "throughput", "move", "daily_output"):
        # 整数类
        return f"{int(round(v)):,} {unit}".strip()
    return f"{v:.2f} {unit}".strip()


def kpi_cn_name(kpi_key: str) -> str:
    """获取KPI中文名,找不到则回退Key本身。"""
    return KPI_NAME_CN.get(kpi_key, kpi_key)


def process_cn_name(process_key: str) -> str:
    """获取工序中文名。"""
    return PROCESS_NAME_CN.get(process_key, process_key)


def equip_status_cn(status: str) -> str:
    """获取设备状态中文名。"""
    return EQUIP_STATUS_NAME_CN.get(status, status)


def product_cn_name(product_key: str) -> str:
    """获取产品中文名。"""
    return PRODUCT_NAME_CN.get(product_key, product_key)


# =============================================================================
# 统计与数学辅助
# =============================================================================

def safe_div(numerator: Any, denominator: Any, default: float = 0.0) -> float:
    """
    安全除法,避免除零错误。
    
    Args:
        numerator: 分子
        denominator: 分母
        default: 分母<=0时返回的默认值
    
    Returns:
        除法结果或default
    """
    try:
        n = float(numerator)
        d = float(denominator)
        if abs(d) < 1e-12:
            return default
        return n / d
    except (ValueError, TypeError):
        return default


def z_score(series: pd.Series) -> pd.Series:
    """
    计算Series的Z-score(标准化),处理std=0的退化情况。
    
    Args:
        series: 输入Series
    
    Returns:
        Z-score Series,索引对齐
    """
    mu = series.mean()
    sigma = series.std()
    if pd.isna(sigma) or sigma < 1e-12:
        return pd.Series(0.0, index=series.index)
    return (series - mu) / sigma


def detect_anomalies(series: pd.Series, threshold: float = 2.0) -> pd.Series:
    """
    基于Z-score检测异常值。
    
    Args:
        series: 输入时序数据
        threshold: Z-score阈值,默认±2σ
    
    Returns:
        布尔Series,True表示对应位置为异常点
    """
    zs = z_score(series)
    return zs.abs() > threshold


def percentile(values: List[float], p: float) -> float:
    """安全的分位数计算,空列表返回0。"""
    if not values:
        return 0.0
    return float(np.percentile(values, p))


# =============================================================================
# 装饰器: 计时 & 异常兜底
# =============================================================================

def timer(func):
    """
    计时装饰器,记录函数耗时(毫秒),通过logger输出。
    
    被装饰函数可以通过 __duration_ms 属性访问耗时(仅限最近一次调用)。
    """
    logger = get_logger("timer")

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            dur_ms = (time.perf_counter() - start) * 1000
            wrapper.__duration_ms = dur_ms  # type: ignore[attr-defined]
            logger.debug(f"{func.__qualname__} 耗时 {dur_ms:.2f}ms")

    wrapper.__duration_ms = 0.0  # type: ignore[attr-defined]
    return wrapper


def try_except(default_return: Any = None, log_level: str = "ERROR"):
    """
    带兜底返回值的异常捕获装饰器工厂。
    
    Args:
        default_return: 发生异常时返回的默认值
        log_level: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
    
    使用示例:
        @try_except(default_return={})
        def risky_call(): ...
    """
    logger = get_logger("try_except")

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                lvl = getattr(logging, log_level.upper(), logging.ERROR)
                logger.log(
                    lvl,
                    f"函数 {func.__qualname__} 执行失败: {type(exc).__name__}: {exc}",
                    exc_info=(lvl >= logging.ERROR),
                )
                return default_return

        return wrapper

    return decorator


# =============================================================================
# DataFrame 辅助
# =============================================================================

def df_safe(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """将None/非DataFrame转为空DataFrame,保证下游链式调用不报错。"""
    if isinstance(df, pd.DataFrame):
        return df.copy()
    return pd.DataFrame()


def df_empty(columns: List[str], dtypes: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    创建指定列名的空DataFrame,可选指定dtype。
    
    Args:
        columns: 列名列表
        dtypes: {列名: dtype}字典
    
    Returns:
        空DataFrame
    """
    df = pd.DataFrame({c: pd.Series(dtype=dtypes.get(c, "object") if dtypes else "object") for c in columns})
    return df


# =============================================================================
# ID / 随机字符串生成
# =============================================================================

def generate_id(prefix: str, seq: Optional[int] = None) -> str:
    """
    生成带前缀的ID字符串,用于批次号、设备号、事件号等。
    
    Args:
        prefix: 前缀,如 'LOT' / 'EQ' / 'EVT'
        seq: 可选序号,未指定时使用时间戳+随机数
    
    Returns:
        形如 'LOT-A20260812-00015' 的ID
    """
    date_part = dt.datetime.now().strftime("%Y%m%d")
    if seq is not None:
        return f"{prefix}-{date_part}-{int(seq):05d}"
    ts = int(time.time() * 1000) % 100000
    rnd = int.from_bytes(os.urandom(2), "big") % 1000
    return f"{prefix}-{date_part}-{ts:05d}{rnd:03d}"


# =============================================================================
# 模块快速自检
# =============================================================================

if __name__ == "__main__":
    print("=== helpers 自检 ===")
    print(f"项目根: {get_project_root()}")
    print(f"配置加载: {'OK' if load_settings() else 'FAIL'}")
    print(f"当前时间: {now_str()}")
    print(f"UPH 1234.567 格式化: {format_kpi('uph', 1234.567)}")
    print(f"OEE 0.85234 格式化: {format_kpi('oee', 0.85234)}")
    print(f"安全除法 1/0 = {safe_div(1, 0)}")
    print(f"工序PHOTO中文名: {process_cn_name('PHOTO')}")
