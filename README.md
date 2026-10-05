# BARNLP Bar

Projeto didático para a oficina **“Do Chat à Ação: conectando agentes a APIs com MCP”**.

## Arquitetura

```text
Usuário
  ↓ linguagem natural
LLM / Host
  ↓
MCP Client
  ↓
MCP Server
  ↓ HTTP
FastAPI
  ↓
Estado local do BARNLP Bar
```

O backend já existe. O exercício da oficina é criar a camada MCP que permite ao agente
consultar informações e executar ações sobre a API.

## Requisitos

- Python 3.11+
- `uv` recomendado

## Instalação

```bash
uv sync
```

Ou com pip:

```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

pip install -e .
```

## 1. Rodar o backend

Na raiz do projeto:

```bash
uv run uvicorn backend.main:app --reload
```

Abra:

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs

### Reset da demo

```bash
curl -X POST http://127.0.0.1:8000/reset
```

## 2. Testar a API

Exemplo:

```bash
curl http://127.0.0.1:8000/menu
```

Adicionar dois NLP Burgers à mesa 3:

```bash
curl -X POST http://127.0.0.1:8000/tables/3/order/items \
  -H "Content-Type: application/json" \
  -d '{"item_id": 1, "quantity": 2}'
```

## 3. Rodar o MCP Inspector

Com o backend rodando em outro terminal:

```bash
uv run mcp dev student/server.py
```

Para testar a implementação completa:

```bash
uv run mcp dev mcp_server/server.py
```

O SDK MCP v2 usa `MCPServer`. O comando `mcp dev` abre a experiência de desenvolvimento
com o Inspector.

## MCP completo

### Tools

- `get_table_order`
- `add_item_to_order`
- `remove_item_from_order`
- `get_table_total`
- `close_table`

### Resources

- `bar://menu`
- `bar://info`

### Prompt

- `attend_table(table_id)`

## Fluxo final da demo

1. “Estou na mesa 3. Quero dois NLP Burgers e uma Token Fries.”
2. “Quanto ficou a conta?”
3. “Na verdade tira uma batata e coloca um Context Cooler.”
4. “Quanto ficou agora?”
5. “Pode fechar a mesa.”

## Testes

```bash
uv run pytest
```
