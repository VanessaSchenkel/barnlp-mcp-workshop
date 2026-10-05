from enum import Enum

from pydantic import BaseModel, Field


class TableStatus(str, Enum):
    FREE = "free"
    OCCUPIED = "occupied"
    CLOSED = "closed"


class MenuItem(BaseModel):
    id: int
    name: str
    description: str
    price: float


class OrderItem(BaseModel):
    item_id: int
    name: str
    unit_price: float
    quantity: int
    item_total: float


class Table(BaseModel):
    id: int
    status: TableStatus
    items: dict[int, int] = Field(default_factory=dict)


class AddItemRequest(BaseModel):
    item_id: int
    quantity: int = Field(default=1, ge=1, le=20)


class OrderResponse(BaseModel):
    table_id: int
    status: TableStatus
    items: list[OrderItem]
    subtotal: float
    service_charge: float
    total: float
