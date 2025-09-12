import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from crewai.flow.flow import Flow, start, listen, router
from crewai import Agent

from src.flows.state import InfinitePayState, PlannedSteps, Step
from src.agents import (
    create_knowledge_agent,
    build_knowledge_prompt,
    create_support_agent,
    build_support_prompt,
    create_general_agent,
    build_general_prompt,
    create_manager_agent,
    build_manager_prompt,
    create_escalation_agent,
    build_escalation_prompt,
)
from src.guardrails.policy import (
    check_user_message_guardrails,
    sanitize_output,
)


class InfinitePayFlow(Flow[InfinitePayState]):

    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        # Provide a minimal valid initial state so Flow can initialize even without inputs
        if initial_state is None:
            initial_state = self._create_initial_state().model_dump()
        super().__init__(initial_state=initial_state)

    # Ensure CrewAI can always create a valid initial state for this Flow
    def _create_initial_state(self) -> InfinitePayState:  # type: ignore[override]
        return InfinitePayState(
            message="",
            user_id="",
            planned_steps=[],
            finished_steps=[],
            raw_response="",
            final_response="",
            processing_time=0.0,
            timestamp=datetime.now(),
            conversation_history=[],
            user_data=None,
        )

    @start()
    def initialize_request(self) -> str:
        """Inicializa o processamento da requisição"""
        print(f" Processando: {self.state.message}")
        self.state.timestamp = datetime.now()
        self.state.processing_time = 0.0
        # reset steps for a fresh run
        self.state.planned_steps = []
        self.state.finished_steps = []

    @router(initialize_request)
    async def agent_manager_plan(self) -> str:
        """Agent Manager: analisa a pergunta, define requisitos e monta os passos"""
        start_plan = time.time()

        # Guardrails pre-check: if the message violates content policy, refuse politely.
        allowed, reason = check_user_message_guardrails(self.state.message)
        if not allowed:
            refusal_task = (
                "A mensagem do usuário viola as políticas de conteúdo (informações internas/sensíveis). "
                "Responda educadamente que não é possível atender a solicitação por razões de segurança e confidencialidade. "
                "Não exponha detalhes internos. Ofereça-se para ajudar com dúvidas gerais sobre produtos e serviços."
                f"Motivo: {reason}"
            )
            self.state.planned_steps = [Step(agent="GENERAL", agent_task=refusal_task)]
            self.state.finished_steps = []
            self.state.processing_time += time.time() - start_plan
            return "execute_next_step"

        # Prompt dinâmico: injeta descrições das equipes e ferramentas disponíveis
        classification_prompt = build_manager_prompt(
            message=self.state.message,
            history=self.state.conversation_history,
        )

        manager_agent = create_manager_agent()
        agent_response = await manager_agent.kickoff_async(
            messages=classification_prompt,
            response_format=PlannedSteps,
        )
        self.state.planned_steps = agent_response.pydantic.steps

        self.state.finished_steps = []
        self.state.processing_time += time.time() - start_plan

        print(f" Plano criado com {len(self.state.planned_steps)} passos")
        return "execute_next_step"

    @router("execute_next_step")
    async def execute_next_step_func(self) -> str:
        """Executa o próximo passo do plano e atualiza finished_steps"""
        if not self.state.planned_steps:
            # Todas as etapas concluídas
            return "apply_personality"

        # Retira o próximo passo
        step = self.state.planned_steps.pop(0)
        step_agent = step.agent
        step_agent_task = step.agent_task
        print(f" Executando passo: {step_agent}:{step_agent_task}")

        exec_start = time.time()
        result_raw = ""

        agent, prompt = self._create_agent_and_task(agent=step_agent, task=step_agent_task)
        if agent:
            try:
                result = await agent.kickoff_async(messages=prompt)
            except Exception:
                result = agent.kickoff(messages=prompt)
            result_raw = getattr(result, "raw", str(result))

        # Atualiza estado com o resultado mais recente
        self.state.raw_response = sanitize_output(result_raw)
        self.state.processing_time += time.time() - exec_start

        self.state.finished_steps.append(
            {
                "agent": step_agent,
                "agent_task": step_agent_task,
                "status": "done",
                "result": self.state.raw_response,
            }
        )

        # Continua para o próximo passo (se houver)
        return "execute_next_step" if self.state.planned_steps else "apply_personality"

    @router("apply_personality")
    async def apply_personality_layer(self) -> str:
        """Aplica camada de personalidade (opcional)"""

        collected_info = ""
        for step in self.state.finished_steps:
            collected_info += f"\n\n{step['agent']}: {step['result']}"

        personality_prompt = f"""
        Você é o assistente oficial da InfinitePay.
        Sua missão é responder as dúvidas do usuário de forma amigável e profissional utilizando as informações coletadas e 
        levando em consideração o histórico de conversa.

        ## Inputs
        Mensagem: {self.state.message}
        Histórico: {self.state.conversation_history}
        
        Informações coletadas: {collected_info}
        
        ## Output
        Resposta final: 
        
        ### Tom
        Use tom amigável, seja claro e termine perguntando se há mais dúvidas.
        """
        agent, prompt = self._create_agent_and_task("GENERAL", personality_prompt)
        agent_response = await agent.kickoff_async(messages=prompt)
        self.state.final_response = sanitize_output(agent_response.raw)

        print(f" Processamento concluído em {self.state.processing_time:.2f}s")

        return "complete"

    @listen(apply_personality_layer)
    def finalize_response(self) -> Dict[str, Any]:
        """Finaliza e retorna a resposta estruturada"""
        return {
            "response": self.state.final_response,
            "processing_time": self.state.processing_time,
        }

    def _create_agent_and_task(self, agent: str, task: str) -> Agent|Tuple[Agent, str]:
        """Helper para criar agentes"""
        
        if agent == "KNOWLEDGE":
            return create_knowledge_agent(), build_knowledge_prompt(task)
        elif agent == "SUPPORT":
            return create_support_agent(), build_support_prompt(task)
        elif agent == "GENERAL":
            return create_general_agent(), build_general_prompt(task)
        elif agent == "ESCALATION":
            return create_escalation_agent(), build_escalation_prompt(task)
        else:
            return None
