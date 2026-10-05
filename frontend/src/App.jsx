import { useEffect, useMemo, useRef, useState } from "react";

const money = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

const statusLabels = {
  free: "Livre",
  occupied: "Ocupada",
  closed: "Fechada",
};

async function api(path) {
  const response = await fetch(`/api${path}`);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Erro ${response.status}`);
  }
  return response.json();
}

function Nav() {
  const path = window.location.pathname;

  return (
    <nav className="nav">
      <a className={path === "/" ? "nav__item active" : "nav__item"} href="/">
        Mesas
      </a>
      <a
        className={path === "/chat" ? "nav__item active" : "nav__item"}
        href="/chat"
      >
        Chat com agente
      </a>
    </nav>
  );
}

function Shell({ children }) {
  return (
    <main className="page">
      <header className="topbar">
        <div className="brand">
          <span className="brand__icon">🍺</span>
          <div>
            <h1>BARNLP Bar</h1>
            <p>Do Chat à Ação com MCP</p>
          </div>
        </div>
        <Nav />
      </header>
      {children}
    </main>
  );
}

function StatusBadge({ status }) {
  return (
    <span className={`status status--${status}`}>
      <span className="status__dot" />
      {statusLabels[status] ?? status}
    </span>
  );
}

function TableCard({ table, selected, onClick }) {
  return (
    <button
      className={`table-card ${selected ? "table-card--selected" : ""}`}
      onClick={onClick}
    >
      <div>
        <span className="eyebrow">Mesa</span>
        <strong className="table-number">{table.id}</strong>
      </div>
      <StatusBadge status={table.status} />
      <div className="table-card__footer">
        {table.status === "free"
          ? "Aguardando clientes"
          : table.status === "closed"
            ? "Conta encerrada"
            : "Atendimento em andamento"}
      </div>
    </button>
  );
}

function OrderPanel({ tableId, order, error }) {
  if (error) {
    return (
      <section className="order-panel">
        <p className="error">{error}</p>
      </section>
    );
  }

  if (!order) {
    return (
      <section className="order-panel">
        <p className="muted">Carregando pedido...</p>
      </section>
    );
  }

  return (
    <section className="order-panel">
      <div className="order-panel__header">
        <div>
          <span className="eyebrow">Pedido atual</span>
          <h2>Mesa {tableId}</h2>
        </div>
        <StatusBadge status={order.status} />
      </div>

      {order.items.length === 0 ? (
        <div className="empty-state">
          <span className="empty-state__icon">🍽️</span>
          <strong>Nenhum item ainda</strong>
          <span>O agente pode começar o pedido pelo MCP.</span>
        </div>
      ) : (
        <div className="order-items">
          {order.items.map((item) => (
            <div className="order-item" key={item.item_id}>
              <div>
                <strong>{item.name}</strong>
                <span>
                  {item.quantity} × {money.format(item.unit_price)}
                </span>
              </div>
              <strong>{money.format(item.item_total)}</strong>
            </div>
          ))}
        </div>
      )}

      <div className="totals">
        <div>
          <span>Subtotal</span>
          <strong>{money.format(order.subtotal)}</strong>
        </div>
        <div>
          <span>Serviço</span>
          <strong>{money.format(order.service_charge)}</strong>
        </div>
        <div className="totals__grand">
          <span>Total</span>
          <strong>{money.format(order.total)}</strong>
        </div>
      </div>
    </section>
  );
}

function Dashboard() {
  const [tables, setTables] = useState([]);
  const [menu, setMenu] = useState([]);
  const [selectedTableId, setSelectedTableId] = useState(1);
  const [order, setOrder] = useState(null);
  const [orderError, setOrderError] = useState("");
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  const selectedTable = useMemo(
    () => tables.find((table) => table.id === selectedTableId),
    [tables, selectedTableId],
  );

  async function refresh() {
    try {
      const [nextTables, nextMenu] = await Promise.all([
        api("/tables"),
        menu.length ? Promise.resolve(menu) : api("/menu"),
      ]);

      setTables(nextTables);
      if (!menu.length) setMenu(nextMenu);
      setConnected(true);

      try {
        const nextOrder = await api(`/tables/${selectedTableId}/order`);
        setOrder(nextOrder);
        setOrderError("");
      } catch (error) {
        setOrder(null);
        setOrderError(error.message);
      }

      setLastUpdate(new Date());
    } catch {
      setConnected(false);
    }
  }

  useEffect(() => {
    refresh();
    const interval = window.setInterval(refresh, 1200);
    return () => window.clearInterval(interval);
  }, [selectedTableId]);

  return (
    <Shell>
      <div className="connection-row">
        <div className="connection">
          <span className={`connection__dot ${connected ? "online" : ""}`} />
          {connected ? "API conectada" : "API desconectada"}
          {lastUpdate && (
            <small>
              {lastUpdate.toLocaleTimeString("pt-BR", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}
            </small>
          )}
        </div>
      </div>

      <div className="content">
        <section>
          <div className="section-heading">
            <div>
              <span className="eyebrow">Salão</span>
              <h2>Mesas</h2>
            </div>
            <span className="muted">{tables.length} mesas</span>
          </div>

          <div className="tables-grid">
            {tables.map((table) => (
              <TableCard
                key={table.id}
                table={table}
                selected={selectedTableId === table.id}
                onClick={() => setSelectedTableId(table.id)}
              />
            ))}
          </div>

          <section className="menu-card">
            <div className="section-heading">
              <div>
                <span className="eyebrow">Resource</span>
                <h2>Cardápio</h2>
              </div>
              <span className="muted">{menu.length} itens</span>
            </div>

            <div className="menu-list">
              {menu.map((item) => (
                <div className="menu-item" key={item.id}>
                  <div>
                    <strong>{item.name}</strong>
                    <span>{item.description}</span>
                  </div>
                  <strong>{money.format(item.price)}</strong>
                </div>
              ))}
            </div>
          </section>
        </section>

        <aside>
          <OrderPanel
            tableId={selectedTableId}
            order={order}
            error={orderError}
          />

          <section className="hint-card">
            <span className="eyebrow">Experimente no chat</span>
            <p>
              “Adiciona dois NLP Burgers na mesa{" "}
              <strong>{selectedTable?.id ?? selectedTableId}</strong>.”
            </p>
            <a className="text-link" href="/chat">
              Abrir agente →
            </a>
          </section>
        </aside>
      </div>
    </Shell>
  );
}

function ToolTrace({ trace }) {
  if (!trace?.length) return null;

  return (
    <div className="tool-traces">
      {trace.map((item, index) => (
        <details className="tool-trace" key={`${item.name}-${index}`}>
          <summary>
            <span>🔧</span>
            <strong>{item.name}</strong>
            <span className={item.error ? "trace-error" : "trace-ok"}>
              {item.error ? "erro" : "executada"}
            </span>
          </summary>
          <div className="tool-trace__body">
            <span>Argumentos</span>
            <pre>{JSON.stringify(item.arguments, null, 2)}</pre>
            <span>Resultado</span>
            <pre>{item.result}</pre>
          </div>
        </details>
      ))}
    </div>
  );
}

function Chat() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Oi! Eu sou o atendente virtual do BARNLP Bar. Pergunte sobre uma mesa ou faça um pedido.",
      trace: [],
    },
  ]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [tools, setTools] = useState([]);
  const [agentOnline, setAgentOnline] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    fetch("/agent/tools")
      .then((response) => {
        if (!response.ok) throw new Error();
        return response.json();
      })
      .then((data) => {
        setTools(data.tools ?? []);
        setAgentOnline(true);
      })
      .catch(() => setAgentOnline(false));
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function sendMessage(event) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || sending) return;

    const userMessage = { role: "user", content: text, trace: [] };
    const nextMessages = [...messages, userMessage];

    setMessages(nextMessages);
    setDraft("");
    setSending(true);

    try {
      const history = nextMessages
        .filter((message) => ["user", "assistant"].includes(message.role))
        .map(({ role, content }) => ({ role, content }));

      const response = await fetch("/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history }),
      });

      const body = await response.json();

      if (!response.ok) {
        throw new Error(body.detail || "Falha ao falar com o agente.");
      }

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: body.message,
          trace: body.tool_calls ?? [],
        },
      ]);
      setAgentOnline(true);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: `Não consegui responder: ${error.message}`,
          trace: [],
          error: true,
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  const examples = [
    "O que a mesa 1 pediu?",
    "Quanto está a conta da mesa 1?",
    "Adiciona dois NLP Burgers na mesa 3.",
  ];

  return (
    <Shell>
      <div className="chat-layout">
        <section className="chat-card">
          <div className="chat-card__header">
            <div>
              <span className="eyebrow">LLM + MCP</span>
              <h2>Converse com o agente</h2>
            </div>
            <div className="connection">
              <span
                className={`connection__dot ${agentOnline ? "online" : ""}`}
              />
              {agentOnline ? "Agente disponível" : "Agente offline"}
            </div>
          </div>

          <div className="messages">
            {messages.map((message, index) => (
              <div
                className={`message message--${message.role} ${
                  message.error ? "message--error" : ""
                }`}
                key={index}
              >
                <span className="message__role">
                  {message.role === "user" ? "Você" : "Agente"}
                </span>
                <div className="message__bubble">{message.content}</div>
                <ToolTrace trace={message.trace} />
              </div>
            ))}

            {sending && (
              <div className="message message--assistant">
                <span className="message__role">Agente</span>
                <div className="message__bubble typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          <form className="composer" onSubmit={sendMessage}>
            <input
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ex.: O que a mesa 1 pediu?"
              disabled={sending}
            />
            <button disabled={!draft.trim() || sending} type="submit">
              Enviar
            </button>
          </form>
        </section>

        <aside className="chat-sidebar">
          <section className="side-card">
            <span className="eyebrow">MCP Server</span>
            <h3>Tools disponíveis</h3>
            {tools.length === 0 ? (
              <p className="muted">
                Nenhuma tool encontrada ou servidor ainda não conectado.
              </p>
            ) : (
              <div className="tools-list">
                {tools.map((tool) => (
                  <div className="tool-pill" key={tool.name}>
                    <strong>{tool.name}</strong>
                    {tool.description && <span>{tool.description}</span>}
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="side-card">
            <span className="eyebrow">Teste rápido</span>
            <div className="examples">
              {examples.map((example) => (
                <button
                  key={example}
                  onClick={() => setDraft(example)}
                  type="button"
                >
                  {example}
                </button>
              ))}
            </div>
          </section>

          <section className="flow-card">
            <span>Mensagem</span>
            <b>↓</b>
            <span>LLM</span>
            <b>↓</b>
            <span>MCP Tool</span>
            <b>↓</b>
            <span>API do Bar</span>
          </section>
        </aside>
      </div>
    </Shell>
  );
}

export default function App() {
  return window.location.pathname === "/chat" ? <Chat /> : <Dashboard />;
}
