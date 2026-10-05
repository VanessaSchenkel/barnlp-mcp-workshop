"""
Esqueleto para os participantes.

Objetivo:
1. Entender como uma API existente pode ser exposta via MCP.
2. Implementar algumas tools.
3. Adicionar um resource.
4. Experimentar um prompt.

O backend e BarAPIClient já estão prontos.
"""

import json

from mcp.server import MCPServer

from mcp_server.api_client import BarAPIClient


mcp = MCPServer("BARNLP Bar - Workshop")
api = BarAPIClient()


@mcp.tool()
async def get_table_order(table_id: int) -> dict:
    """Consulta o pedido atual de uma mesa."""
    return await api.get_order(table_id)


# TODO 1
# Crie add_item_to_order(table_id, item_name, quantity=1)


# TODO 2
# Crie get_table_total(table_id)


# DESAFIO
# Crie remove_item_from_order(...)
# Crie close_table(...)


# TODO 3
# Exponha o cardápio como resource em bar://menu.
# Dica:
#
# @mcp.resource("bar://menu", mime_type="application/json")
# async def menu_resource() -> str:
#     ...


# TODO 4
# Crie um prompt "attend_table" que receba table_id.


if __name__ == "__main__":
    mcp.run()
