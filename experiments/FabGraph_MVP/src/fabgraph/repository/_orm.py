"""SQLAlchemy 2.0 ORM 模型。

对应 SQLite 中的四张元数据表：
- ``tables`` / ``columns`` / ``procedures`` / ``sql_history``

list 字段（tags/aliases/input_tables/output_tables）以 JSON 字符串落库，
读取时由 :class:`MetadataRepository` 还原为 list。

对应ResNet输入嵌入层：将异构元数据投影到统一的关系张量空间。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """ORM 基类。"""


class TableORM(Base):
    """表元数据 ORM。"""

    __tablename__ = "tables"

    table_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    schema_name: Mapped[str] = mapped_column(String(64), default="FAB")
    description: Mapped[str] = mapped_column(Text, default="")
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[list] = mapped_column(JSON, default=list)

    columns: Mapped[list[ColumnORM]] = relationship(
        back_populates="table",
        cascade="all, delete-orphan",
        order_by="ColumnORM.position",
    )


class ColumnORM(Base):
    """字段元数据 ORM。"""

    __tablename__ = "columns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_name: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("tables.table_name", ondelete="CASCADE"),
        index=True,
    )
    column_name: Mapped[str] = mapped_column(String(128), index=True)
    data_type: Mapped[str] = mapped_column(String(64), default="VARCHAR2")
    nullable: Mapped[bool] = mapped_column(default=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    semantic_type: Mapped[str] = mapped_column(String(32), default="unknown")
    semantic_label: Mapped[str] = mapped_column(String(128), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    aliases: Mapped[list] = mapped_column(JSON, default=list)

    table: Mapped[TableORM] = relationship(back_populates="columns")


class ProcedureORM(Base):
    """存储过程元数据 ORM。"""

    __tablename__ = "procedures"

    procedure_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    schema_name: Mapped[str] = mapped_column(String(64), default="FAB")
    definition: Mapped[str] = mapped_column(Text, default="")
    input_tables: Mapped[list] = mapped_column(JSON, default=list)
    output_tables: Mapped[list] = mapped_column(JSON, default=list)
    description: Mapped[str] = mapped_column(Text, default="")


class SqlHistoryORM(Base):
    """历史 SQL ORM。"""

    __tablename__ = "sql_history"

    sql_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(32), default="simple", index=True)
    sql: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
