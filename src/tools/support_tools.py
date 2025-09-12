from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field


class UserInfoInput(BaseModel):
    user_id: str = Field(description="ID do usuário")


class UserInfoTool(BaseTool):
    name: str = "UserInfo"
    description: str = "Recupera informações básicas do usuário (stub)"
    args_schema: Type[BaseModel] = UserInfoInput

    def _run(self, user_id: str) -> str:
        user_data = {
            "user_id": user_id,
            "name": "João Silva",
            "account_status": "active",
            "registration_date": "2023-05-15",
            "products": ["maquininha_smart", "conta_digital"],
        }
        return (
            f"Informações do usuário {user_id}:\n"
            f"- Nome: {user_data['name']}\n"
            f"- Status: {user_data['account_status']}\n"
            f"- Cliente desde: {user_data['registration_date']}\n"
            f"- Produtos: {', '.join(user_data['products'])}"
        )


class AccountStatusInput(BaseModel):
    user_id: str = Field(description="ID do usuário")


class AccountStatusTool(BaseTool):
    name: str = "AccountStatus"
    description: str = "Verifica status da conta do usuário (stub)"
    args_schema: Type[BaseModel] = AccountStatusInput

    def _run(self, user_id: str) -> str:
        return f"Status da conta do usuário {user_id}: active"


class TicketInput(BaseModel):
    user_id: str = Field(description="ID do usuário")
    issue: str = Field(description="Descrição do problema")


class TicketTool(BaseTool):
    name: str = "Ticket"
    description: str = "Cria um ticket de suporte (stub)"
    args_schema: Type[BaseModel] = TicketInput

    def _run(self, user_id: str, issue: str) -> str:
        return f"Ticket criado para usuário {user_id}: TICKET-123 | Assunto: {issue}"


class TransactionHistoryInput(BaseModel):
    user_id: str = Field(description="ID do usuário")
    limit: int = Field(default=5, description="Quantidade de transações a retornar")


class TransactionHistoryTool(BaseTool):
    name: str = "TransactionHistory"
    description: str = "Retorna histórico recente de transações (stub)"
    args_schema: Type[BaseModel] = TransactionHistoryInput

    def _run(self, user_id: str, limit: int = 5) -> str:
        items = [f"TX-{i:03d}" for i in range(1, limit + 1)]
        return f"Transações recentes para {user_id}: {', '.join(items)}"
