# 🍺 BARNLP Bar — MCP Workshop

Projeto da oficina **“Do Chat à Ação: conectando agentes a APIs com MCP”**.

A proposta é partir de uma API REST já existente e criar uma camada MCP para que uma LLM consiga consultar dados e executar ações no sistema usando linguagem natural.

O projeto inclui:

- Backend local com **FastAPI**
- Servidor **MCP**
- **MCP Inspector** para testar tools, resources e prompts
- Integração com uma **LLM**
- Frontend em **React**
- Dashboard para visualizar o estado das mesas
- Chat web em `/chat` para interagir com o agente

---

## 🧠 Arquitetura

```text
Usuário
  ↓
React / Chat
  ↓
LLM
  ↓
MCP Client
  ↓
MCP Server
  ↓
FastAPI
  ↓
Estado do BARNLP Bar
```

O frontend também permite visualizar as alterações feitas pelo agente em tempo real.

---

# 1. Requisitos

Antes de começar, confira se a máquina possui:

### Python

Recomendado:

```bash
python3 --version
```

Use **Python 3.11 ou superior**.

---

### Node.js

Confira:

```bash
node -v
```

Para o MCP Inspector, use **Node 22 ou superior**.

Caso use `nvm`:

```bash
nvm install 22
nvm use 22
```

Depois:

```bash
node -v
npm -v
```

---

### uv

Confira:

```bash
uv --version
```

Se não estiver instalado:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Depois, abra um novo terminal ou rode:

```bash
source ~/.zshrc
```

---

# 2. Clonar o projeto

```bash
git clone URL_DO_REPOSITORIO
cd barnlp-mcp-workshop
```

---

# 3. Criar o ambiente Python

Crie o virtual environment:

```bash
python3 -m venv .venv
```

Ative:

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```powershell
.venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -e .
```

---

# 4. Rodar o backend do bar

Abra um terminal na raiz do projeto e execute:

```bash
uvicorn backend.main:app --reload --port 8000
```

A API ficará disponível em:

```text
http://127.0.0.1:8000
```

---

# 5. Explorar a API pelo Swagger

Abra no navegador:

```text
http://127.0.0.1:8000/docs
```

Antes de mexer com MCP, vale entender o sistema que já existe.

Teste alguns endpoints.

## Ver o cardápio

```text
GET /menu
```

---

## Ver as mesas

```text
GET /tables
```

---

## Consultar o pedido da mesa 1

```text
GET /tables/1/order
```

---

## Consultar a mesa 3

```text
GET /tables/3/order
```

Inicialmente ela deve estar livre:

```json
{
  "table_id": 3,
  "status": "free",
  "items": [],
  "subtotal": 0,
  "service_charge": 0,
  "total": 0
}
```

---

## Adicionar itens à mesa 3

Use:

```text
POST /tables/3/order/items
```

Body:

```json
{
  "item_id": 1,
  "quantity": 2
}
```

A mesa passa de:

```text
free
```

para:

```text
occupied
```

---

## Ver o total

```text
GET /tables/3/total
```

---

## Fechar a mesa

```text
POST /tables/3/close
```

---

## Reiniciar a demo

Caso queira voltar ao estado inicial:

```text
POST /reset
```

Isso é útil durante os testes da oficina.

---

# 6. Primeiro contato com MCP

Mantenha o backend rodando.

Abra um **segundo terminal**, ative o ambiente virtual e execute:

```bash
mcp dev student/server.py
```

O comando abrirá o **MCP Inspector**.

Caso ele não abra automaticamente, use a URL exibida no terminal.

---

# 7. MCP Inspector

Clique em **Connect**.

Depois abra a seção:

```text
Tools
```

No início do exercício, o projeto já possui uma tool pronta:

```text
get_table_order
```

Teste com:

```json
{
  "table_id": 1
}
```

O MCP Server irá:

```text
Inspector
   ↓
get_table_order
   ↓
MCP Server
   ↓
BarAPIClient
   ↓
FastAPI
```

O resultado deve mostrar o pedido atual da mesa.

Também teste:

```json
{
  "table_id": 3
}
```

---

# 8. Estrutura do exercício MCP

O arquivo usado durante a oficina é:

```text
student/server.py
```

Ele começa com uma tool pronta:

```python
@mcp.tool()
async def get_table_order(table_id: int) -> dict:
    """Consulta o pedido atual de uma mesa."""
    return await api.get_order(table_id)
```

Durante a oficina serão adicionadas novas capacidades, como:

```text
add_item_to_order
remove_item_from_order
get_table_total
close_table
```

Além de:

```text
Resource → bar://menu
Prompt   → attend_table
```

A ideia é observar as capacidades do agente aumentando conforme o MCP Server evolui.

---

# 9. Configurar a LLM

Crie um arquivo chamado:

```text
.env
```

na raiz do projeto.

Exemplo:

```env
OPENAI_API_KEY=COLE_A_CHAVE_AQUI
OPENAI_MODEL=gpt-5.6-luna
```

Durante a oficina, a chave temporária será disponibilizada pela instrutora.

> ⚠️ Nunca faça commit do `.env`.

O `.gitignore` já deve conter:

```gitignore
.env
```

---

# 10. Testar a LLM pelo terminal

O backend deve continuar rodando em:

```text
:8000
```

Em outro terminal, execute:

```bash
python client/agent.py
```

Você deverá ver algo semelhante a:

```text
🍺 BARNLP Bar Agent

🤖 Modelo: gpt-5.6-luna
🔧 Tools disponíveis: get_table_order
```

Experimente:

```text
O que a mesa 1 pediu?
```

A LLM deve decidir usar:

```text
get_table_order
```

O terminal também mostra a chamada MCP:

```text
🔧 MCP tool: get_table_order

argumentos:
{"table_id": 1}
```

Depois aparece a resposta final da LLM.

Esse fluxo é:

```text
Usuário
   ↓
LLM
   ↓
escolhe uma tool
   ↓
MCP
   ↓
FastAPI
   ↓
resultado
   ↓
LLM
   ↓
Usuário
```

---

# 11. Rodar o servidor do chat web

Para utilizar a rota `/chat` do frontend, precisamos de uma pequena API que conecta:

```text
React → LLM → MCP
```

Abra outro terminal na raiz do projeto:

```bash
uvicorn client.chat_server:app --reload --port 8001
```

Agora temos:

```text
FastAPI do bar   → http://127.0.0.1:8000
Chat / LLM / MCP → http://127.0.0.1:8001
```

---

# 12. Rodar o frontend React

Abra outro terminal:

```bash
cd frontend
```

Instale as dependências:

```bash
npm install
```

Depois rode:

```bash
npm run dev
```

O frontend ficará disponível em:

```text
http://localhost:5173
```

---

# 13. Dashboard das mesas

Abra:

```text
http://localhost:5173/
```

O dashboard mostra:

- mesas;
- status;
- pedido atual;
- itens;
- subtotal;
- taxa de serviço;
- total.

Os status possíveis são:

```text
free
occupied
closed
```

A tela consulta a API periodicamente.

Isso significa que, quando uma tool MCP altera o estado de uma mesa, o dashboard reflete a mudança automaticamente.

---

# 14. Chat com o agente

Abra:

```text
http://localhost:5173/chat
```

Nesta tela é possível conversar diretamente com a LLM.

Exemplo:

```text
O que a mesa 1 pediu?
```

A interface também mostra qual tool MCP foi executada.

Por exemplo:

```text
🔧 get_table_order

Argumentos:
{
  "table_id": 1
}
```

e o resultado devolvido pela tool.

---

# 15. Alterando estado através da linguagem natural

Depois de implementar:

```text
add_item_to_order
```

experimente no chat:

```text
Adiciona dois NLP Burgers na mesa 3.
```

O fluxo será:

```text
Mensagem do usuário
        ↓
       LLM
        ↓
add_item_to_order
        ↓
       MCP
        ↓
     FastAPI
        ↓
estado da mesa alterado
        ↓
dashboard atualizado
```

Depois volte para:

```text
http://localhost:5173/
```

A mesa 3 deve aparecer como:

```text
occupied
```

e mostrar os itens adicionados.

---

# 16. Fluxo sugerido para testar

Um exemplo completo de conversa:

```text
O que a mesa 3 pediu?
```

Depois:

```text
Adiciona dois NLP Burgers e uma Token Fries na mesa 3.
```

Depois:

```text
Quanto ficou a conta?
```

Depois:

```text
Tira uma Token Fries e coloca um Context Cooler.
```

Depois:

```text
Quanto ficou agora?
```

E finalmente:

```text
Pode fechar a mesa.
```

Enquanto conversa, mantenha o dashboard aberto para acompanhar as alterações.

---

# 17. Tools, Resources e Prompts

O projeto explora três primitivas importantes do MCP.

## Tools

Ações que a LLM pode decidir executar.

Exemplos:

```text
get_table_order
add_item_to_order
remove_item_from_order
get_table_total
close_table
```

---

## Resources

Dados que o cliente pode disponibilizar como contexto.

Exemplo:

```text
bar://menu
```

---

## Prompts

Templates reutilizáveis de interação.

Exemplo:

```text
attend_table
```

---

# 18. Processos que devem estar rodando

Para utilizar **todo o projeto**, mantenha três processos ativos.

### Terminal 1 — API do bar

```bash
uvicorn backend.main:app --reload --port 8000
```

### Terminal 2 — Chat / LLM / MCP

```bash
uvicorn client.chat_server:app --reload --port 8001
```

### Terminal 3 — React

```bash
cd frontend
npm run dev
```

Então acesse:

```text
Swagger
http://127.0.0.1:8000/docs

Dashboard
http://localhost:5173/

Chat
http://localhost:5173/chat
```

O MCP Inspector é executado separadamente quando necessário:

```bash
mcp dev student/server.py
```

---

# 19. Comandos principais

## Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

## MCP Inspector

```bash
mcp dev student/server.py
```

## Chat pelo terminal

```bash
python client/agent.py
```

## Chat API

```bash
uvicorn client.chat_server:app --reload --port 8001
```

## React

```bash
cd frontend
npm run dev
```

## Resetar o bar

Pelo Swagger:

```text
POST /reset
```

---

# 20. Troubleshooting

## `spawn uv ENOENT`

O Inspector não encontrou o `uv`.

Confira:

```bash
uv --version
```

Caso não exista:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Inspector reclama da versão do Node

Confira:

```bash
node -v
```

Use Node 22+.

Com `nvm`:

```bash
nvm install 22
nvm use 22
```

---

## `Cannot find native binding`

Limpe o cache temporário do `npx`:

```bash
rm -rf ~/.npm/_npx
npm cache verify
```

Depois:

```bash
npm install -g npm@latest
```

Teste:

```bash
npx --yes @modelcontextprotocol/inspector
```

Depois tente novamente:

```bash
mcp dev student/server.py
```

---

## `OPENAI_API_KEY não encontrada`

Confira se existe um arquivo:

```text
.env
```

na raiz do projeto.

Ele deve conter:

```env
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.6-luna
```

Não coloque o `.env` dentro de `client/` ou `frontend/`.

---

## Frontend diz que a API está desconectada

Confira se o backend está rodando:

```bash
uvicorn backend.main:app --reload --port 8000
```

Depois teste:

```text
http://127.0.0.1:8000/docs
```

---

## Chat aparece offline

Confira se o servidor do chat está rodando:

```bash
uvicorn client.chat_server:app --reload --port 8001
```

---

## Quero voltar o bar ao estado inicial

Use:

```text
POST /reset
```

no Swagger:

```text
http://127.0.0.1:8000/docs
```

---

# 🍺 BARNLP Bar

A ideia deste projeto não é ensinar FastAPI, React ou OpenAI.

Essas partes existem para tornar visível o que realmente queremos explorar:

```text
Como uma LLM descobre capacidades externas
e executa ações reais através do MCP?
```

Começamos com uma API comum.

Depois adicionamos:

```text
Tools
Resources
Prompts
```

E transformamos uma conversa como:

```text
“Adiciona dois NLP Burgers na mesa 3.”
```

em uma ação real no sistema.

**Chat → LLM → MCP → API → Ação.**