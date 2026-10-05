from fastapi import FastAPI, Query

from backend.models import AddItemRequest, MenuItem, OrderResponse, Table
from backend.store import SERVICE_RATE, store


app = FastAPI(
    title="BARNLP Bar API",
    description="API local usada na oficina Do Chat à Ação: conectando agentes a APIs com MCP.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/info")
def get_bar_info() -> dict:
    return {
        "name": "BARNLP Bar",
        "service_charge_percent": int(SERVICE_RATE * 100),
        "notes": [
            "A primeira adição de item abre automaticamente uma mesa livre.",
            "Mesas fechadas não aceitam novos pedidos.",
        ],
    }


@app.get("/menu", response_model=list[MenuItem])
def get_menu() -> list[MenuItem]:
    return store.get_menu()


@app.get("/tables", response_model=list[Table])
def list_tables() -> list[Table]:
    return store.list_tables()


@app.get("/tables/{table_id}", response_model=Table)
def get_table(table_id: int) -> Table:
    return store.get_table(table_id)


@app.get("/tables/{table_id}/order", response_model=OrderResponse)
def get_order(table_id: int) -> OrderResponse:
    return store.order_for(table_id)


@app.post("/tables/{table_id}/order/items", response_model=OrderResponse)
def add_item(table_id: int, request: AddItemRequest) -> OrderResponse:
    return store.add_item(table_id, request.item_id, request.quantity)


@app.delete("/tables/{table_id}/order/items/{item_id}", response_model=OrderResponse)
def remove_item(
    table_id: int,
    item_id: int,
    quantity: int = Query(default=1, ge=1, le=20),
) -> OrderResponse:
    return store.remove_item(table_id, item_id, quantity)


@app.get("/tables/{table_id}/total", response_model=OrderResponse)
def get_total(table_id: int) -> OrderResponse:
    return store.order_for(table_id)


@app.post("/tables/{table_id}/close", response_model=OrderResponse)
def close_table(table_id: int) -> OrderResponse:
    return store.close_table(table_id)


@app.post("/reset")
def reset_demo() -> dict[str, str]:
    store.reset()
    return {"status": "reset", "message": "BARNLP Bar voltou ao estado inicial."}
