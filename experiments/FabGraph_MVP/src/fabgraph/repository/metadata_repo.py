"""元数据仓储层。

封装 SQLite 元数据访问：表/字段/过程/历史 SQL 的 CRUD。
所有 service 层访问元数据必须经由此处，禁止散落 raw SQL。

对应ResNet池化层：聚合下层存储特征并向上提供统一查询接口。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from fabgraph.config import Settings, get_settings, project_root
from fabgraph.models.schema import (
    Column,
    ColumnSemanticType,
    Procedure,
    Table,
)
from fabgraph.utils.exceptions import MetadataError

from ._orm import Base, ColumnORM, ProcedureORM, SqlHistoryORM, TableORM

logger = logging.getLogger(__name__)


class MetadataRepository:
    """元数据仓储：基于 SQLAlchemy 2.0 + SQLite。

    Attributes:
        engine: SQLAlchemy 引擎。
        _session_factory: Session 工厂。
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """初始化仓储。

        Args:
            settings: 配置对象，默认使用全局单例。
        """
        self._settings = settings or get_settings()
        db_path = Path(self._settings.database.sqlite_path)
        # 相对路径基于项目根解析
        if not db_path.is_absolute():
            db_path = project_root() / db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine: Engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            future=True,
        )
        self._session_factory = sessionmaker(
            bind=self.engine, expire_on_commit=False, class_=Session
        )
        logger.info("元数据仓储初始化: %s", db_path)

    def init_db(self) -> None:
        """创建所有表（幂等）。"""
        Base.metadata.create_all(self.engine)
        logger.debug("已创建元数据表结构")

    def drop_all(self) -> None:
        """删除所有表（测试用）。"""
        Base.metadata.drop_all(self.engine)

    def _session(self) -> Session:
        """返回新 Session。"""
        return self._session_factory()

    # ---------------- 写入 ----------------

    def load_from_json(self, mock_dir: Path | str | None = None) -> dict[str, int]:
        """从 mock_oracle 目录批量加载 JSON 到 SQLite。

        Args:
            mock_dir: 模拟数据目录，默认取配置中 data.mock_oracle_dir。

        Returns:
            各表写入条数统计。

        Raises:
            MetadataError: JSON 读取或写入失败。
        """
        self.init_db()
        if mock_dir is None:
            mock_dir = self._settings.data.mock_oracle_dir
        mock_path = Path(mock_dir)
        if not mock_path.is_absolute():
            mock_path = project_root() / mock_path

        counts = {
            "tables": 0,
            "columns": 0,
            "procedures": 0,
            "sql_history": 0,
        }
        try:
            with self._session() as session:
                # 幂等：先清空旧数据，避免主键冲突
                session.query(SqlHistoryORM).delete()
                session.query(ProcedureORM).delete()
                session.query(ColumnORM).delete()
                session.query(TableORM).delete()
                self._bulk_load_tables(session, mock_path, counts)
                self._bulk_load_columns(session, mock_path, counts)
                self._bulk_load_procedures(session, mock_path, counts)
                self._bulk_load_sql_history(session, mock_path, counts)
                session.commit()
        except MetadataError:
            raise
        except Exception as e:
            raise MetadataError(f"加载 JSON 数据失败: {e}") from e
        logger.info("批量加载完成: %s", counts)
        return counts

    def _bulk_load_tables(
        self, session: Session, mock_path: Path, counts: dict[str, int]
    ) -> None:
        """批量加载表元数据。"""
        tables = self._read_json(mock_path / "tables.json")
        for t in tables:
            session.add(TableORM(
                table_name=t["table_name"], schema_name=t.get("schema_name", "FAB"),
                description=t.get("description", ""), row_count=t.get("row_count", 0),
                tags=t.get("tags", []),
            ))
        counts["tables"] = len(tables)

    def _bulk_load_columns(
        self, session: Session, mock_path: Path, counts: dict[str, int]
    ) -> None:
        """批量加载字段元数据。"""
        columns = self._read_json(mock_path / "columns.json")
        for c in columns:
            session.add(ColumnORM(
                table_name=c["table_name"], column_name=c["column_name"],
                data_type=c.get("data_type", "VARCHAR2"),
                nullable=c.get("nullable", True), position=c.get("position", 0),
                semantic_type=c.get("semantic_type", "unknown"),
                semantic_label=c.get("semantic_label", ""),
                description=c.get("description", ""),
                confidence=c.get("confidence", 0.0), aliases=c.get("aliases", []),
            ))
        counts["columns"] = len(columns)

    def _bulk_load_procedures(
        self, session: Session, mock_path: Path, counts: dict[str, int]
    ) -> None:
        """批量加载存储过程元数据。"""
        procs = self._read_json(mock_path / "procedures.json")
        for p in procs:
            session.add(ProcedureORM(
                procedure_name=p["procedure_name"], schema_name=p.get("schema_name", "FAB"),
                definition=p.get("definition", ""), input_tables=p.get("input_tables", []),
                output_tables=p.get("output_tables", []), description=p.get("description", ""),
            ))
        counts["procedures"] = len(procs)

    def _bulk_load_sql_history(
        self, session: Session, mock_path: Path, counts: dict[str, int]
    ) -> None:
        """批量加载历史 SQL。"""
        sqls = self._read_json(mock_path / "sql_history.json")
        for s in sqls:
            session.add(SqlHistoryORM(
                sql_id=s["sql_id"], category=s.get("category", "simple"), sql=s.get("sql", ""),
            ))
        counts["sql_history"] = len(sqls)

    @staticmethod
    def _read_json(path: Path) -> Any:
        """读取 JSON 文件。

        Raises:
            MetadataError: 文件不存在或解析失败。
        """
        if not path.exists():
            raise MetadataError(f"JSON 文件不存在: {path}")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise MetadataError(f"JSON 解析失败: {path}: {e}") from e

    # ---------------- 读取 ----------------

    def get_tables(self) -> list[Table]:
        """返回全部表（含字段）。"""
        with self._session() as session:
            stmt = select(TableORM).order_by(TableORM.table_name)
            orms = session.scalars(stmt).all()
            return [self._to_table_model(orm) for orm in orms]

    def get_table_by_name(self, table_name: str) -> Table | None:
        """按表名查询表（含字段）。

        Args:
            table_name: 表名。

        Returns:
            Table 模型，不存在返回 None。
        """
        with self._session() as session:
            orm = session.get(TableORM, table_name)
            return self._to_table_model(orm) if orm else None

    def get_columns(self, table_name: str) -> list[Column]:
        """返回指定表的字段列表。"""
        with self._session() as session:
            stmt = (
                select(ColumnORM)
                .where(ColumnORM.table_name == table_name)
                .order_by(ColumnORM.position)
            )
            orms = session.scalars(stmt).all()
            return [self._to_column_model(orm) for orm in orms]

    def get_procedures(self) -> list[Procedure]:
        """返回全部存储过程。"""
        with self._session() as session:
            stmt = select(ProcedureORM).order_by(ProcedureORM.procedure_name)
            orms = session.scalars(stmt).all()
            return [self._to_procedure_model(orm) for orm in orms]

    def get_procedure_by_name(self, name: str) -> Procedure | None:
        """按过程名查询存储过程。"""
        with self._session() as session:
            orm = session.get(ProcedureORM, name)
            return self._to_procedure_model(orm) if orm else None

    def get_sql_history(self, category: str | None = None) -> list[dict[str, Any]]:
        """返回历史 SQL。

        Args:
            category: 可选类别过滤（simple/join/aggregate/...）。

        Returns:
            SQL 字典列表 [{sql_id, category, sql}]。
        """
        with self._session() as session:
            stmt = select(SqlHistoryORM).order_by(SqlHistoryORM.sql_id)
            if category:
                stmt = stmt.where(SqlHistoryORM.category == category)
            orms = session.scalars(stmt).all()
            return [
                {"sql_id": o.sql_id, "category": o.category, "sql": o.sql}
                for o in orms
            ]

    # ---------------- 模型转换 ----------------

    @staticmethod
    def _to_column_model(orm: ColumnORM) -> Column:
        """ColumnORM -> Column。"""
        try:
            sem = ColumnSemanticType(orm.semantic_type)
        except ValueError:
            sem = ColumnSemanticType.UNKNOWN
        return Column(
            table_name=orm.table_name, column_name=orm.column_name,
            data_type=orm.data_type, nullable=orm.nullable, position=orm.position,
            semantic_type=sem, semantic_label=orm.semantic_label,
            description=orm.description, confidence=orm.confidence,
            aliases=list(orm.aliases or []),
        )

    def _to_table_model(self, orm: TableORM) -> Table:
        """TableORM -> Table（含字段）。"""
        return Table(
            table_name=orm.table_name, schema_name=orm.schema_name,
            description=orm.description, row_count=orm.row_count,
            columns=[self._to_column_model(c) for c in orm.columns],
            tags=list(orm.tags or []),
        )

    @staticmethod
    def _to_procedure_model(orm: ProcedureORM) -> Procedure:
        """ProcedureORM -> Procedure。"""
        return Procedure(
            procedure_name=orm.procedure_name, schema_name=orm.schema_name,
            definition=orm.definition, input_tables=list(orm.input_tables or []),
            output_tables=list(orm.output_tables or []), description=orm.description,
        )
