from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # App                                                                  #
    # ------------------------------------------------------------------ #
    app_name: str = Field(default="FAQ Generator API", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    allowed_origins_str: str = Field(
        default="*",
        alias="ALLOWED_ORIGINS",
        description="CORS 허용 오리진 (콤마 구분)",
    )
    webhook_secret: str = Field(
        default="your-webhook-secret-key-here",
        alias="WEBHOOK_SECRET",
        description="Webhook 인증 키",
    )

    # ------------------------------------------------------------------ #
    # Lark Base                                                            #
    # ------------------------------------------------------------------ #
    lark_app_id: str = Field(
        default="",
        alias="LARK_APP_ID",
        description="Lark App ID",
    )
    lark_app_secret: str = Field(
        default="",
        alias="LARK_APP_SECRET",
        description="Lark App Secret",
    )
    lark_base_app_token: str = Field(
        default="",
        alias="LARK_BASE_APP_TOKEN",
        description="Lark Base app_token",
    )
    lark_faq_table_id: str = Field(
        default="",
        alias="LARK_FAQ_TABLE_ID",
        description="FAQ 테이블 ID",
    )
    lark_feedback_table_id: str = Field(
        default="",
        alias="LARK_FEEDBACK_TABLE_ID",
        description="피드백 테이블 ID (선택)",
    )
    lark_source_doc_table_id: str = Field(
        default="",
        alias="LARK_SOURCE_DOC_TABLE_ID",
        description="소스 문서 테이블 ID (선택)",
    )

    # ------------------------------------------------------------------ #
    # OpenAI                                                               #
    # ------------------------------------------------------------------ #
    openai_api_key: str = Field(
        ...,
        alias="OPENAI_API_KEY",
        description="OpenAI API 키",
    )

    # ------------------------------------------------------------------ #
    # ChromaDB                                                             #
    # ------------------------------------------------------------------ #
    chroma_persist_dir: str = Field(
        default="./chroma_db",
        alias="CHROMA_PERSIST_DIR",
        description="ChromaDB 벡터 저장 디렉터리",
    )

    # ------------------------------------------------------------------ #
    # Embedding                                                            #
    # ------------------------------------------------------------------ #
    embedding_model_name: str = Field(
        default="BAAI/bge-m3",
        alias="EMBEDDING_MODEL_NAME",
        description="HuggingFace 임베딩 모델명",
    )

    # ------------------------------------------------------------------ #
    # Cache                                                                #
    # ------------------------------------------------------------------ #
    cache_ttl_seconds: int = Field(
        default=300,
        alias="CACHE_TTL_SECONDS",
        description="인메모리 캐시 TTL (초). 기본 5분",
        ge=0,
    )

    # ------------------------------------------------------------------ #
    # Validators                                                           #
    # ------------------------------------------------------------------ #
    @property
    def allowed_origins(self) -> list[str]:
        """ALLOWED_ORIGINS를 콤마로 구분된 문자열에서 리스트로 변환"""
        if not self.allowed_origins_str:
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins_str.split(",") if origin.strip()]

    @field_validator("lark_app_id", "lark_app_secret", "lark_base_app_token", "lark_faq_table_id")
    @classmethod
    def strip_lark_values(cls, v: str) -> str:
        return (v or "").strip()

    @property
    def chroma_dir(self) -> Path:
        return Path(self.chroma_persist_dir)


settings = Settings()
