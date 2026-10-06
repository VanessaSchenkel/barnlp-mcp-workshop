from copy import deepcopy

from fastapi import HTTPException

from backend.models import MenuItem, OrderItem, OrderResponse, Table, TableStatus


SERVICE_RATE = 0.10

MENU = [
    MenuItem(
        id=1,
        name="NLP Burger",
        description="Hambúrguer artesanal com queijo e molho da casa.",
        price=32.00,
    ),
    MenuItem(
        id=2,
        name="Token Fries",
        description="Batatas fritas crocantes para compartilhar contexto.",
        price=18.00,
    ),
    MenuItem(
        id=3,
        name="Transformer Pizza",
        description="Pizza individual de queijo, tomate e manjericão.",
        price=48.00,
    ),
    MenuItem(
        id=4,
        name="Context Cooler",
        description="Drink cítrico sem álcool com limão e hortelã.",
        price=22.00,
    ),
    MenuItem(
        id=5,
        name="Embedding Soda",
        description="Refrigerante artesanal da casa.",
        price=10.00,
    ),
    MenuItem(
        id=6,
        name="Prompt Brownie",
        description="Brownie de chocolate com sorvete.",
        price=20.00,
    ),
]

_INITIAL_TABLES = {
    1: Table(id=1, status=TableStatus.OCCUPIED, items={1: 1, 2: 1}),
    2: Table(id=2, status=TableStatus.OCCUPIED, items={4: 2}),
    3: Table(id=3, status=TableStatus.FREE, items={}),
    4: Table(id=4, status=TableStatus.OCCUPIED, items={3: 1}),
}


class BarStore:
    def __init__(self) -> None:
        self.tables: dict[int, Table] = deepcopy(_INITIAL_TABLES)

    def reset(self) -> None:
        self.tables = deepcopy(_INITIAL_TABLES)

    def get_menu(self) -> list[MenuItem]:
        return MENU

    def get_menu_item(self, item_id: int) -> MenuItem:
        for item in MENU:
            if item.id == item_id:
                return item
        raise HTTPException(status_code=404, detail=f"Item {item_id} não existe no cardápio.")

    def get_table(self, table_id: int) -> Table:
        table = self.tables.get(table_id)
        if table is None:
            raise HTTPException(status_code=404, detail=f"Mesa {table_id} não existe.")
        return table

    def list_tables(self) -> list[Table]:
        return list(self.tables.values())

    def add_item(self, table_id: int, item_id: int, quantity: int) -> OrderResponse:
        table = self.get_table(table_id)
        self.get_menu_item(item_id)

        if table.status == TableStatus.CLOSED:
            raise HTTPException(
                status_code=409,
                detail=f"Mesa {table_id} já foi fechada. Use /reset para reiniciar a demo.",
            )

        if table.status == TableStatus.FREE:
            table.status = TableStatus.OCCUPIED

        table.items[item_id] = table.items.get(item_id, 0) + quantity
        return self.order_for(table_id)

    def remove_item(self, table_id: int, item_id: int, quantity: int) -> OrderResponse:
        table = self.get_table(table_id)

        if table.status != TableStatus.OCCUPIED:
            raise HTTPException(
                status_code=409,
                detail=f"Mesa {table_id} não está aberta.",
            )

        current = table.items.get(item_id, 0)
        if current == 0:
            raise HTTPException(
                status_code=404,
                detail=f"O item {item_id} não está no pedido da mesa {table_id}.",
            )

        if quantity >= current:
            del table.items[item_id]
        else:
            table.items[item_id] = current - quantity

        return self.order_for(table_id)

    def order_for(self, table_id: int) -> OrderResponse:
        table = self.get_table(table_id)

        items: list[OrderItem] = []
        subtotal = 0.0

        for item_id, quantity in table.items.items():
            menu_item = self.get_menu_item(item_id)
            item_total = round(menu_item.price * quantity, 2)
            subtotal += item_total
            items.append(
                OrderItem(
                    item_id=item_id,
                    name=menu_item.name,
                    unit_price=menu_item.price,
                    quantity=quantity,
                    item_total=item_total,
                )
            )

        subtotal = round(subtotal, 2)
        service_charge = round(subtotal * SERVICE_RATE, 2)
        total = round(subtotal + service_charge, 2)

        return OrderResponse(
            table_id=table.id,
            status=table.status,
            items=items,
            subtotal=subtotal,
            service_charge=service_charge,
            total=total,
        )

    def close_table(self, table_id: int) -> OrderResponse:
        table = self.get_table(table_id)

        if table.status != TableStatus.OCCUPIED:
            raise HTTPException(
                status_code=409,
                detail=f"Mesa {table_id} não está aberta.",
            )

        if not table.items:
            raise HTTPException(
                status_code=409,
                detail=f"Mesa {table_id} não possui itens para fechar.",
            )

        table.status = TableStatus.CLOSED
        return self.order_for(table_id)


store = BarStore()
