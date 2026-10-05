import json

from mcp.server import MCPServer

from mcp_server.api_client import BarAPIClient


mcp = MCPServer("BARNLP Bar")
api = BarAPIClient()


@mcp.tool()
async def get_table_order(table_id: int) -> dict:
    """Consulta o pedido atual de uma mesa do BARNLP Bar."""
    return await api.get_order(table_id)


@mcp.tool()
async def add_item_to_order(
    table_id: int,
    item_name: str,
    quantity: int = 1,
) -> dict:
    """Adiciona uma quantidade de um item do cardápio ao pedido de uma mesa."""
    return await api.add_item(table_id, item_name, quantity)


@mcp.tool()
async def remove_item_from_order(
    table_id: int,
    item_name: str,
    quantity: int = 1,
) -> dict:
    """Remove uma quantidade de um item do pedido de uma mesa."""
    return await api.remove_item(table_id, item_name, quantity)


@mcp.tool()
async def get_table_total(table_id: int) -> dict:
    """Calcula subtotal, taxa de serviço e total atual de uma mesa."""
    return await api.get_total(table_id)


@mcp.tool()
async def close_table(table_id: int) -> dict:
    """Fecha uma mesa aberta e retorna o resumo final da conta."""
    return await api.close_table(table_id)


@mcp.resource(
    "bar://menu",
    name="menu",
    description="Cardápio atual do BARNLP Bar.",
    mime_type="application/json",
)
async def menu_resource() -> str:
    return json.dumps(await api.get_menu(), ensure_ascii=False, indent=2)


@mcp.resource(
    "bar://info",
    name="bar_info",
    description="Informações e regras gerais do BARNLP Bar.",
    mime_type="application/json",
)
async def bar_info_resource() -> str:
    return json.dumps(await api.get_info(), ensure_ascii=False, indent=2)


@mcp.prompt(
    name="attend_table",
    title="Atender uma mesa",
    description="Inicia um fluxo de atendimento para uma mesa do BARNLP Bar.",
)
def attend_table(table_id: str) -> str:
    return f"""
Você está atendendo a mesa {table_id} do BARNLP Bar.

Use o cardápio disponível em bar://menu como referência.
Consulte o pedido atual antes de assumir o que já foi solicitado.

Regras:
- Nunca adicione ou remova itens sem um pedido claro do cliente.
- Se o nome de um item estiver ambíguo, peça esclarecimento.
- Antes de fechar a mesa, informe o total atual.
- Só feche a mesa depois de uma confirmação explícita do cliente.
""".strip()


if __name__ == "__main__":
    mcp.run()
