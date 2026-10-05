import json
import os
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI
from pydantic import BaseModel, Field


load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

BASE_INSTRUCTIONS = """
Você é o atendente virtual do BARNLP Bar.

Você tem acesso às ferramentas expostas pelo servidor MCP local.
Use as ferramentas sempre que precisar consultar ou alterar o estado real de uma mesa.

Regras:
- Nunca diga que consultou, adicionou, removeu ou fechou algo sem executar a ferramenta correspondente quando ela for necessária.
- Se uma ferramenta retornar erro, explique o erro ao usuário em vez de inventar um resultado.
- Só feche uma mesa quando o cliente pedir explicitamente.
- Responda em português, de forma curta e natural.
""".strip()

app = FastAPI(
    title="BARNLP Chat API",
    description="Camada HTTP entre o frontend React, a LLM e o servidor MCP local.",
    version="0.1.0",
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4_000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=30)


def mcp_tools_to_openai(tools_result):
    return [
        {
            "type": "function",
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        }
        for tool in tools_result.tools
    ]


def tool_result_to_text(result) -> str:
    structured = getattr(result, "structured_content", None)
    if structured is not None:
        return json.dumps(structured, ensure_ascii=False)

    texts = []
    for block in getattr(result, "content", []):
        text = getattr(block, "text", None)
        if text:
            texts.append(text)

    if texts:
        return "\n".join(texts)

    if hasattr(result, "model_dump_json"):
        return result.model_dump_json(by_alias=True)

    return str(result)


def server_params():
    return StdioServerParameters(
        command="uv",
        args=["run", "python", "student/server.py"],
    )


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL}


@app.get("/tools")
async def list_tools():
    async with stdio_client(server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()

            return {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description or "",
                    }
                    for tool in result.tools
                ]
            }


@app.post("/chat")
async def chat(request: ChatRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY não encontrada no .env.",
        )

    openai_client = AsyncOpenAI()

    async with stdio_client(server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tools = mcp_tools_to_openai(tools_result)

            input_messages = [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ]

            try:
                response = await openai_client.responses.create(
                    model=MODEL,
                    instructions=BASE_INSTRUCTIONS,
                    input=input_messages,
                    tools=tools,
                )
            except Exception as exc:
                raise HTTPException(
                    status_code=502,
                    detail=f"Erro ao chamar a LLM: {exc}",
                ) from exc

            traces = []

            while True:
                calls = [
                    item
                    for item in response.output
                    if item.type == "function_call"
                ]

                if not calls:
                    break

                outputs = []

                for call in calls:
                    arguments = json.loads(call.arguments or "{}")
                    trace = {
                        "name": call.name,
                        "arguments": arguments,
                        "result": "",
                        "error": False,
                    }

                    try:
                        result = await session.call_tool(
                            call.name,
                            arguments=arguments,
                        )
                        output = tool_result_to_text(result)
                        trace["result"] = output
                    except Exception as exc:
                        output = json.dumps(
                            {"error": str(exc)},
                            ensure_ascii=False,
                        )
                        trace["result"] = output
                        trace["error"] = True

                    traces.append(trace)

                    outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": output,
                        }
                    )

                try:
                    response = await openai_client.responses.create(
                        model=MODEL,
                        instructions=BASE_INSTRUCTIONS,
                        input=outputs,
                        tools=tools,
                        previous_response_id=response.id,
                    )
                except Exception as exc:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Erro ao continuar resposta da LLM: {exc}",
                    ) from exc

            return {
                "message": response.output_text,
                "tool_calls": traces,
            }
