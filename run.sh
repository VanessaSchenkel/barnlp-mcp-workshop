#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

BACKEND_PID=""
CHAT_PID=""
FRONTEND_PID=""

cleanup() {
  echo
  echo "🛑 Encerrando BARNLP Bar..."

  for pid in "$BACKEND_PID" "$CHAT_PID" "$FRONTEND_PID"; do
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done

  wait 2>/dev/null || true
}

trap cleanup EXIT INT TERM

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "❌ Comando '$1' não encontrado."
    echo "$2"
    exit 1
  fi
}

echo "🍺 BARNLP Bar — iniciando ambiente"
echo

require_command "python3" "Instale Python 3.11+."
require_command "node" "Instale Node.js 22+."
require_command "npm" "Instale npm."
require_command "uv" "Instale uv: curl -LsSf https://astral.sh/uv/install.sh | sh"

NODE_MAJOR="$(node -p "process.versions.node.split('.')[0]")"
if [ "$NODE_MAJOR" -lt 22 ]; then
  echo "⚠️  Node $(node -v) detectado. Recomendado: Node 22+."
fi

# -------------------------------------------------------------------
# Python
# -------------------------------------------------------------------

if [ ! -d ".venv" ]; then
  echo "🐍 Criando ambiente virtual..."
  python3 -m venv .venv

  echo "📦 Instalando dependências Python..."
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -e .
else
  echo "✅ Ambiente Python encontrado."
fi

# -------------------------------------------------------------------
# .env
# -------------------------------------------------------------------

if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo
    echo "⚠️  Criei o arquivo .env a partir de .env.example."
    echo "   Preencha OPENAI_API_KEY e rode ./run.sh novamente."
    exit 1
  fi

  echo "❌ Arquivo .env não encontrado."
  exit 1
fi

if grep -q "COLE_A_CHAVE_AQUI" .env 2>/dev/null; then
  echo "❌ Preencha OPENAI_API_KEY no arquivo .env antes de continuar."
  exit 1
fi

# -------------------------------------------------------------------
# Frontend
# -------------------------------------------------------------------

if [ ! -d "frontend/node_modules" ]; then
  echo "📦 Instalando dependências do frontend..."
  (cd frontend && npm install)
else
  echo "✅ Dependências do frontend encontradas."
fi

echo
echo "🚀 Subindo serviços..."
echo

# Backend do bar
.venv/bin/python -m uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

# Chat / LLM / MCP
.venv/bin/python -m uvicorn client.chat_server:app --reload --port 8001 &
CHAT_PID=$!

# React
(
  cd frontend
  npm run dev
) &
FRONTEND_PID=$!

sleep 2

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🍺 BARNLP Bar está rodando"
echo
echo "Swagger:   http://127.0.0.1:8000/docs"
echo "Dashboard: http://localhost:5173/"
echo "Chat:      http://localhost:5173/chat"
echo
echo "MCP Inspector (opcional, em outro terminal):"
echo "  source .venv/bin/activate"
echo "  mcp dev student/server.py"
echo
echo "Pressione Ctrl+C para encerrar tudo."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

wait
