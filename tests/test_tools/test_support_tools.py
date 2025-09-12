import pytest

from src.tools.support_tools import (
    UserInfoTool,
    AccountStatusTool,
    TransactionHistoryTool,
    TicketTool,
)


def test_user_info_tool_output_format():
    tool = UserInfoTool()
    out = tool._run("user-1")
    assert "Informações do usuário user-1" in out
    assert "Nome:" in out and "Status:" in out and "Produtos:" in out


def test_account_status_tool_output():
    tool = AccountStatusTool()
    out = tool._run("user-2")
    assert out.endswith("active")


def test_transaction_history_limit():
    tool = TransactionHistoryTool()
    out = tool._run("user-3", limit=3)
    assert "TX-001" in out and "TX-003" in out
    assert "TX-004" not in out


def test_ticket_tool_creates_ticket_id():
    tool = TicketTool()
    out = tool._run("user-4", issue="Falha de login")
    assert "TICKET-123" in out and "Falha de login" in out
