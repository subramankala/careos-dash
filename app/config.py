from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GINGER_CAREOS_DASH_",
        env_file=".env",
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 8000
    base_url: str = "http://localhost:8000"
    signing_secret: str = "replace-me-with-a-long-random-secret"
    link_expiry_seconds: int = 1800
    openclaw_name: str = "OpenClaw"
    use_real_mcp: bool = False
    mcp_base_url: str = ""
    mcp_api_key: str = ""
    mcp_timeout_seconds: float = 5.0
    mcp_retry_attempts: int = 2


settings = Settings()
