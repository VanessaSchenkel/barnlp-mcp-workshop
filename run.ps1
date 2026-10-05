$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$backend = $null
$chat = $null
$frontend = $null

function Stop-Barnlp {
    Write-Host ""
    Write-Host "🛑 Encerrando BARNLP Bar..."

    foreach ($process in @($backend, $chat, $frontend)) {
        if ($null -ne $process -and -not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

trap {
    Stop-Barnlp
    break
}

function Require-Command {
    param(
        [string]$Name,
        [string]$Help
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Write-Host "❌ Comando '$Name' não encontrado."
        Write-Host $Help
        exit 1
    }
}

Write-Host "🍺 BARNLP Bar — iniciando ambiente"
Write-Host ""

Require-Command "python" "Instale Python 3.11+."
Require-Command "node" "Instale Node.js 22+."
Require-Command "npm" "Instale npm."
Require-Command "uv" "Instale uv: https://docs.astral.sh/uv/"

$nodeMajor = [int]((node -p "process.versions.node.split('.')[0]"))
if ($nodeMajor -lt 22) {
    Write-Host "⚠️  Node $(node -v) detectado. Recomendado: Node 22+."
}

# -------------------------------------------------------------------
# Python
# -------------------------------------------------------------------

if (-not (Test-Path ".venv")) {
    Write-Host "🐍 Criando ambiente virtual..."
    python -m venv .venv

    Write-Host "📦 Instalando dependências Python..."
    & ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
    & ".\.venv\Scripts\python.exe" -m pip install -e .
}
else {
    Write-Host "✅ Ambiente Python encontrado."
}

# -------------------------------------------------------------------
# .env
# -------------------------------------------------------------------

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host ""
        Write-Host "⚠️  Criei o arquivo .env a partir de .env.example."
        Write-Host "   Preencha OPENAI_API_KEY e rode .\run.ps1 novamente."
        exit 1
    }

    Write-Host "❌ Arquivo .env não encontrado."
    exit 1
}

if ((Get-Content ".env" -Raw) -match "COLE_A_CHAVE_AQUI") {
    Write-Host "❌ Preencha OPENAI_API_KEY no arquivo .env antes de continuar."
    exit 1
}

# -------------------------------------------------------------------
# Frontend
# -------------------------------------------------------------------

if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "📦 Instalando dependências do frontend..."
    Push-Location frontend
    npm install
    Pop-Location
}
else {
    Write-Host "✅ Dependências do frontend encontradas."
}

Write-Host ""
Write-Host "🚀 Subindo serviços..."
Write-Host ""

$pythonExe = Resolve-Path ".\.venv\Scripts\python.exe"

$backend = Start-Process `
    -FilePath $pythonExe `
    -ArgumentList "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000" `
    -PassThru `
    -NoNewWindow

$chat = Start-Process `
    -FilePath $pythonExe `
    -ArgumentList "-m", "uvicorn", "client.chat_server:app", "--reload", "--port", "8001" `
    -PassThru `
    -NoNewWindow

$frontend = Start-Process `
    -FilePath "npm" `
    -ArgumentList "run", "dev" `
    -WorkingDirectory (Join-Path $PSScriptRoot "frontend") `
    -PassThru `
    -NoNewWindow

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "🍺 BARNLP Bar está rodando"
Write-Host ""
Write-Host "Swagger:   http://127.0.0.1:8000/docs"
Write-Host "Dashboard: http://localhost:5173/"
Write-Host "Chat:      http://localhost:5173/chat"
Write-Host ""
Write-Host "MCP Inspector (opcional, em outro terminal):"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  mcp dev student/server.py"
Write-Host ""
Write-Host "Pressione Ctrl+C para encerrar tudo."
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Stop-Barnlp
}
