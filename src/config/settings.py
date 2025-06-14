from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    openweather_api_key: str = Field(..., description="OpenWeather API key for the application")
    tavily_api_key: str = Field(..., description="Tavily API key for the application")
    # debug: bool = Field(False, description="Debug mode for the application")
    anthropic_api_key: str = Field(..., description="Anthropic API key for the application")
    cohere_api_key: str = Field(..., description="Cohere API key for the application")
    langsmith_api_key: str = Field(..., description="LangSmith API key for the application")
    langsmith_tracing: str = Field(..., description="LangSmith tracing for the application")
    qdrant_api_key: str = Field(..., description="Qdrant API key for the application")
    qdrant_url: str = Field(..., description="Qdrant URL for the application")
    gemini_api_key: str = Field(..., description="Gemini API key for the application")
    mem0_api_key: str = Field(..., description="Mem0 API key for the application")
    voyage_api_key: str = Field(..., description="Voyage API key for the application")
    groq_api_key: str = Field(..., description="Groq API key for the application")


    model_config = SettingsConfigDict(env_file=".env")

# Instantiate settings object
settings = Settings()
