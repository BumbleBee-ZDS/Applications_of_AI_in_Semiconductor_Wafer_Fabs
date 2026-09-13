"""一键建库 + seed（与 Streamlit 首页"一键初始化"共用同一套逻辑）。

用法：
    python scripts/init_db.py            # 建库 seed（幂等）
    python scripts/init_db.py --drop     # 重建后再 seed
    python scripts/init_db.py --extract  # 建库后顺带抽取 L1
    python scripts/init_db.py --all      # 建库 + 抽取 + Mock 编译（完整演示数据准备）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 保证从项目根目录可导入 config / core（无论从 fabwiki/ 还是 scripts/ 启动）
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def run(drop: bool = False, extract: bool = True, compile_: bool = True) -> None:
    """同步 init_db 与首页一键初始化：建库 → 抽取 → 编译（Mock/LLM）。

    默认全量执行，保证裸跑 `init_db.py` 后知识库即完整可用；
    --no-extract / --no-compile 可仅做子步骤。
    """
    from core import db

    print("=" * 50)
    print("  建库 + seed ...")
    conn = db.init_db(drop_existing=drop)
    for t in db.table_names():
        print(f"    - {t:<16} {db.row_count(conn, t):>4} 行")
    print(f"    - meta_fk             {db.row_count(conn, 'meta_fk'):>4} 条外键")
    print(f"  数据库就绪: {db.get_db_path()}")
    conn.close()

    if extract:
        print("  抽取 L1 数据字典 ...")
        from core import extractor
        extractor.extract_all()

    if compile_:
        print("  编译 L2 知识（Mock / 真实 LLM）...")
        from core import compiler
        compiler.compile_all()


def main() -> None:
    ap = argparse.ArgumentParser(description="构建 FabWiki 演示数仓")
    ap.add_argument("--drop", action="store_true", help="重建已存在的表再 seed")
    ap.add_argument("--no-extract", action="store_true", help="跳过 L1 抽取")
    ap.add_argument("--no-compile", action="store_true", help="跳过 L2 编译")
    ap.add_argument("--extract", action="store_true", help="（兼容）仅抽取 L1")
    ap.add_argument("--all", action="store_true", help="（兼容）全量 = 默认行为")
    args = ap.parse_args()
    run(drop=args.drop,
        extract=not args.no_extract and not (args.extract and args.no_compile),
        compile_=not args.no_compile)


if __name__ == "__main__":
    main()