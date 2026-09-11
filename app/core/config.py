from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Audio processing
    confidence_threshold: float = 0.6
    min_audio_duration: float = 3.0
    max_audio_duration: float = 5.0
    sample_rate: int = 16000
    max_clips: int = 10

    # LLM explanation provider (OpenRouter-compatible)
    # USE_LLM=false keeps the app in no-credential MockLLM mode.
    use_llm: bool = False
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"


settings = Settings()
