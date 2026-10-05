from difflib import get_close_matches

import httpx


class BarAPIError(RuntimeError):
    pass


class BarAPIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")

    async def _request(self, method: str, path: str, **kwargs):
        async with httpx.AsyncClient(base_url=self.base_url, timeout=5.0) as client:
            response = await client.request(method, path, **kwargs)

        if response.is_error:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except Exception:
                pass
            raise BarAPIError(f"API do bar respondeu {response.status_code}: {detail}")

        return response.json()

    async def get_info(self):
        return await self._request("GET", "/info")

    async def get_menu(self):
        return await self._request("GET", "/menu")

    async def get_order(self, table_id: int):
        return await self._request("GET", f"/tables/{table_id}/order")

    async def get_total(self, table_id: int):
        return await self._request("GET", f"/tables/{table_id}/total")

    async def close_table(self, table_id: int):
        return await self._request("POST", f"/tables/{table_id}/close")

    async def _resolve_item_id(self, item_name: str) -> int:
        menu = await self.get_menu()

        exact = next(
            (item for item in menu if item["name"].casefold() == item_name.casefold()),
            None,
        )
        if exact:
            return exact["id"]

        names = [item["name"] for item in menu]
        matches = get_close_matches(item_name, names, n=1, cutoff=0.55)
        if not matches:
            raise BarAPIError(
                f"Não encontrei '{item_name}' no cardápio. "
                f"Itens disponíveis: {', '.join(names)}"
            )

        matched_name = matches[0]
        return next(item["id"] for item in menu if item["name"] == matched_name)

    async def add_item(self, table_id: int, item_name: str, quantity: int = 1):
        item_id = await self._resolve_item_id(item_name)
        return await self._request(
            "POST",
            f"/tables/{table_id}/order/items",
            json={"item_id": item_id, "quantity": quantity},
        )

    async def remove_item(self, table_id: int, item_name: str, quantity: int = 1):
        item_id = await self._resolve_item_id(item_name)
        return await self._request(
            "DELETE",
            f"/tables/{table_id}/order/items/{item_id}",
            params={"quantity": quantity},
        )
