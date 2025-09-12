from typing import Optional, Type
import json

from pydantic import BaseModel, Field
from crewai.tools import BaseTool

from src.config.settings import settings

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None


class SlackNotifyInput(BaseModel):
    channel: Optional[str] = Field(default=None, description="Slack channel (e.g., #support). If omitted, uses settings.slack_channel")
    message: str = Field(description="Message to send to Slack")


class SlackNotifyTool(BaseTool):
    name: str = "SlackNotify"
    description: str = (
        "Send a notification to Slack to request human assistance. "
        "Uses SLACK_WEBHOOK_URL when configured; otherwise, returns a stubbed confirmation."
    )
    args_schema: Type[BaseModel] = SlackNotifyInput

    def _run(self, message: str, channel: Optional[str] = None) -> str:
        target_channel = channel or getattr(settings, "slack_channel", "#support-escalations")
        webhook_url = getattr(settings, "slack_webhook_url", None)

        payload = {
            "text": f"[Escalation] {message}",
        }

        # If a default channel is desired in the payload (depending on the Slack app), include it
        if target_channel:
            payload["channel"] = target_channel

        if webhook_url and httpx is not None:
            try:
                resp = httpx.post(webhook_url, headers={"Content-Type": "application/json"}, content=json.dumps(payload), timeout=5.0)
                if resp.status_code >= 200 and resp.status_code < 300:
                    return f"Slack notified successfully in {target_channel}."
                return f"Slack notification failed with status {resp.status_code}: {resp.text[:200]}"
            except Exception as e:  # pragma: no cover - network environment dependent
                return f"Error sending Slack notification (stub fallback): {str(e)}"

        # Stubbed path when webhook isn't configured
        return f"[stub] Slack notification to {target_channel}: {message}"
