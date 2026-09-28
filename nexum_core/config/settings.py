from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ai_provider: str = "mock"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:4b"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1"
    max_iterations: int = 8
    network_mode: str = "off"
    network_max_bytes: int = 2_000_000
    network_timeout: float = 15.0
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
