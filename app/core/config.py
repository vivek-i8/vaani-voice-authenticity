from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Model configuration
    model_name: str = "Gustking/wav2vec2-large-xlsr-deepfake-audio-classification"

    # Audio processing
    confidence_threshold: float = 0.6
    min_audio_duration: float = 3.0
    max_audio_duration: float = 5.0
    sample_rate: int = 16000
    max_clips: int = 10

    # LLM configuration
    use_bedrock: bool = False
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"


settings = Settings()
