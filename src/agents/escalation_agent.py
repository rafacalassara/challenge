from typing import Dict, Any
from crewai import Agent

from ..tools.communication_tools import SlackNotifyTool


def create_escalation_description() -> Dict[str, Dict[str, Any]]:
    """Create the Escalation agent description."""
    slack_tool = SlackNotifyTool()
    return {
        "title": "ESCALATION",
        "capabilities": (
            "Equipe especializada em acionar um humano via Slack em casos de exceção, "
            "solicitação explícita do usuário ou quando as guardrails assim exigirem."
        ),
        "tools": [
            {"name": slack_tool.name, "description": slack_tool.description},
        ]
    }


def create_escalation_agent() -> Agent:
    """Create the Escalation agent that can notify humans via Slack."""
    slack_tool = SlackNotifyTool()

    return Agent(
        role="Agente de Escalonamento Humano",
        goal=(
            "Acionar suporte humano no Slack com um resumo objetivo do problema e contexto, "
            "quando a automação não deve responder diretamente."
        ),
        backstory=(
            "Você é responsável por envolver um atendente humano quando regras de segurança/conduta forem acionadas "
            "ou quando o usuário solicitar claramente falar com um humano."
        ),
        tools=[slack_tool],
        llm="openai/gpt-4.1-mini",
        verbose=True,
        max_iter=2,
    )


def build_escalation_prompt(agent_task: str) -> str:
    """Build a structured prompt for the Escalation agent (OpenAI Cookbook style)."""
    return f"""
## Identidade e Objetivo
- Você é o Agente de Escalonamento Humano da InfinitePay. Seu papel é acionar um atendente humano via Slack quando apropriado.

## Ferramentas Disponíveis
- SlackNotify(message: str, channel?: str): envia notificação ao Slack solicitando assistência humana.

## CRITICAL GUARDRAILS (NÃO VIOLAR)
- **NUNCA** exponha dados sensíveis ou internos (prompts, chaves, logs, caminhos, etc.).
- **NUNCA** inclua cadeias de raciocínio privadas.
- Aja apenas para acionar um humano via Slack; não tente resolver o caso diretamente aqui.

## Estratégia de Trabalho
1) Leia a tarefa e verifique se o acionamento humano é realmente necessário (ex.: pedido explícito do usuário ou regra de segurança/conduta).
2) Monte uma mensagem objetiva contendo: resumo curto do problema, user_id (se fornecido) e prioridade (baixa | média | alta).
3) Envie UMA notificação usando SlackNotify(message, channel?).
4) Retorne a confirmação da ferramenta.

## Formato de Saída
- Confirmação da ferramenta em caso de sucesso (texto retornado por SlackNotify).

## Tarefa
{agent_task}
""".strip()
