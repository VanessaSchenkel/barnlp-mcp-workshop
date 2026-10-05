from fastapi.testclient import TestClient

from backend.main import app
from backend.store import store


client = TestClient(app)


def setup_function():
    store.reset()


def test_menu_is_available():
    response = client.get("/menu")
    assert response.status_code == 200
    assert len(response.json()) >= 5


def test_add_item_occupieds_free_table():
    response = client.post(
        "/tables/3/order/items",
        json={"item_id": 1, "quantity": 2},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "occupied"
    assert body["items"][0]["quantity"] == 2


def test_total_includes_service_charge():
    response = client.get("/tables/1/total")
    assert response.status_code == 200
    body = response.json()
    assert body["subtotal"] == 50.0
    assert body["service_charge"] == 5.0
    assert body["total"] == 55.0


def test_closed_table_rejects_new_items():
    close = client.post("/tables/1/close")
    assert close.status_code == 200

    add = client.post(
        "/tables/1/order/items",
        json={"item_id": 1, "quantity": 1},
    )
    assert add.status_code == 409
