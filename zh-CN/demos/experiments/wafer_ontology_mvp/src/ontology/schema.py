from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Lot(SQLModel, table=True):
    lot_id: str = Field(primary_key=True, index=True)
    product_name: str
    current_yield: float
    status: str = "RUNNING"
    create_time: datetime = Field(default_factory=datetime.now)


class Wafer(SQLModel, table=True):
    wafer_id: str = Field(primary_key=True, index=True)
    slot: int
    parent_lot_id: str = Field(foreign_key="lot.lot_id")
    status: str = "RUNNING"
    defect_count: int = 0


class Equipment(SQLModel, table=True):
    eq_id: str = Field(primary_key=True, index=True)
    type: str
    status: str = "RUNNING"
    alarm_count: int = 0


class ProcessStep(SQLModel, table=True):
    step_id: str = Field(primary_key=True, index=True)
    lot_id: str = Field(foreign_key="lot.lot_id")
    eq_id: str = Field(foreign_key="equipment.eq_id")
    recipe_name: str
    timestamp: datetime = Field(default_factory=datetime.now)


class Defect(SQLModel, table=True):
    defect_id: str = Field(primary_key=True, index=True)
    wafer_id: str = Field(foreign_key="wafer.wafer_id")
    type: str
    severity: str
    location_x: float
    location_y: float
    detected_at: datetime = Field(default_factory=datetime.now)


GRAPH_RELATIONS = {
    "CONTAINS": {"source": "Lot", "target": "Wafer"},
    "PROCESSED_ON": {"source": "Wafer", "target": "Equipment"},
    "HAS_STEP": {"source": "Lot", "target": "ProcessStep"},
    "ASSIGNED_TO": {"source": "ProcessStep", "target": "Equipment"},
    "HAS_DEFECT": {"source": "Wafer", "target": "Defect"},
}
