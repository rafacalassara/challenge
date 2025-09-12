from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Challenge API"
    debug: bool = False

    # Optional Slack integration
    slack_webhook_url: str | None = None
    slack_channel: str | None = None

    # Optional OpenAI key (some environments set this)
    openai_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
