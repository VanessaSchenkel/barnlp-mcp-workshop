import asyncio
import json
import os
import sys
from typing import Any

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


BASE_INSTRUCTIONS = """
Você é o atendente virtual do BARNLP Bar.

Você tem acesso às ferramentas expostas pelo servidor MCP.
Use as ferramentas sempre que precisar consultar ou alterar o estado real de uma mesa.

Regras:
- Nunca diga que adicionou, removeu ou fechou algo sem executar a ferramenta correspondente.
- Se uma ferramenta retornar erro, explique o erro ao usuário em vez de inventar um resultado.
- Antes de fechar uma mesa, só chame close_table se o cliente tiver pedido explicitamente para fechar.
- Responda em português, de forma curta e natural.
""".strip()


def mcp_tools_to_openai(tools_result) -> list[dict[str, Any]]:
    """Converte os schemas das tools MCP para function tools da Responses API."""
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
    """Transforma o resultado MCP em texto/JSON para devolver à LLM."""
    structured = getattr(result, "structured_content", None)
    if structured is not None:
        return json.dumps(structured, ensure_ascii=False)

    texts: list[str] = []
    for block in getattr(result, "content", []):
        text = getattr(block, "text", None)
        if text:
            texts.append(text)

    if texts:
        return "\n".join(texts)

    if hasattr(result, "model_dump_json"):
        return result.model_dump_json(by_alias=True)

    return str(result)


def prompt_to_text(prompt_result) -> str:
    parts: list[str] = []
    for message in prompt_result.messages:
        content = message.content
        text = getattr(content, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts)


def resource_to_text(resource_result) -> str:
    parts: list[str] = []
    for content in resource_result.contents:
        text = getattr(content, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts)


async def chat_with_tools(
    openai_client: AsyncOpenAI,
    mcp_session: ClientSession,
    tools: list[dict[str, Any]],
    user_text: str,
    previous_response_id: str | None,
    extra_context: str,
):
    instructions = BASE_INSTRUCTIONS
    if extra_context:
        instructions += f"\n\nContexto fornecido pelo cliente MCP:\n{extra_context}"

    response = await openai_client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=user_text,
        tools=tools,
        previous_response_id=previous_response_id,
    )

    while True:
        tool_calls = [item for item in response.output if item.type == "function_call"]

        if not tool_calls:
            return response

        tool_outputs = []

        for call in tool_calls:
            arguments = json.loads(call.arguments or "{}")

            print(f"\n🔧 MCP tool: {call.name}")
            print(f"   argumentos: {json.dumps(arguments, ensure_ascii=False)}")

            try:
                result = await mcp_session.call_tool(call.name, arguments=arguments)
                output = tool_result_to_text(result)
            except Exception as exc:
                output = json.dumps({"error": str(exc)}, ensure_ascii=False)

            print(f"   resultado: {output}")

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": output,
                }
            )

        response = await openai_client.responses.create(
            model=MODEL,
            instructions=instructions,
            input=tool_outputs,
            tools=tools,
            previous_response_id=response.id,
        )


async def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY não encontrada.")
        print('Defina antes de rodar: export OPENAI_API_KEY="sua-chave"')
        sys.exit(1)

    openai_client = AsyncOpenAI()

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "student/server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()

            print("\n🍺 BARNLP Bar Agent")
            print(f"🤖 Modelo: {MODEL}")
            print(
                "🔧 Tools disponíveis: "
                + (", ".join(t.name for t in tools_result.tools) or "nenhuma")
            )
            print("\nComandos:")
            print("  /menu       carrega bar://menu como contexto")
            print("  /prompt N   carrega o prompt attend_table para a mesa N")
            print("  /tools      mostra as tools MCP disponíveis")
            print("  /exit       encerra")
            print()

            previous_response_id: str | None = None
            extra_context_parts: list[str] = []

            while True:
                user_text = input("Você: ").strip()

                if not user_text:
                    continue

                if user_text.lower() in {"/exit", "exit", "quit"}:
                    break

                if user_text.lower() == "/tools":
                    current = await session.list_tools()
                    print(
                        "Tools: "
                        + (", ".join(tool.name for tool in current.tools) or "nenhuma")
                    )
                    continue

                if user_text.lower() == "/menu":
                    try:
                        resource = await session.read_resource("bar://menu")
                        menu_text = resource_to_text(resource)
                        extra_context_parts.append(
                            "Cardápio atual do BARNLP Bar:\n" + menu_text
                        )
                        print("📚 Resource bar://menu carregado no contexto da LLM.")
                        print(menu_text)
                    except Exception as exc:
                        print(
                            "⚠️ Não consegui ler bar://menu. "
                            "Ele já foi implementado no servidor MCP?"
                        )
                        print(f"   {exc}")
                    continue

                if user_text.lower().startswith("/prompt "):
                    table_id = user_text.split(maxsplit=1)[1].strip()
                    try:
                        prompt = await session.get_prompt(
                            "attend_table",
                            arguments={"table_id": table_id},
                        )
                        prompt_text = prompt_to_text(prompt)
                        extra_context_parts.append(
                            f"Prompt MCP attend_table({table_id}):\n{prompt_text}"
                        )
                        print(
                            f"📝 Prompt attend_table({table_id}) "
                            "carregado no contexto da LLM."
                        )
                        print(prompt_text)
                    except Exception as exc:
                        print(
                            "⚠️ Não consegui carregar attend_table. "
                            "Ele já foi implementado no servidor MCP?"
                        )
                        print(f"   {exc}")
                    continue

                tools_result = await session.list_tools()
                openai_tools = mcp_tools_to_openai(tools_result)

                response = await chat_with_tools(
                    openai_client=openai_client,
                    mcp_session=session,
                    tools=openai_tools,
                    user_text=user_text,
                    previous_response_id=previous_response_id,
                    extra_context="\n\n".join(extra_context_parts),
                )

                previous_response_id = response.id
                print(f"\nAgente: {response.output_text}\n")


if __name__ == "__main__":
    asyncio.run(main())
