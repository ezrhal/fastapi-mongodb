from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    # tokens
    SECRET_KEY: SecretStr
    # access_token_expire_minutes: int = 30
    #
    # SQL SERVER
    SQL_PASS: SecretStr
    SQL_USER: SecretStr
    PMIS_DB_ADDRESS: SecretStr
    OTHERS_DB_ADDRESS: SecretStr
    S3_ENDPOINT: SecretStr
    S3_ACCESS_KEY: SecretStr
    S3_SECRET_KEY: SecretStr
    S3_REGION: SecretStr
    S3_DTS_BUCKET: SecretStr
    S3_SECURE: SecretStr
    THRESHOLD_BYTES: int
    # db1_password: SecretStr
    #
    # # DB 2 (optional)
    # db2_server: str | None = None
    # db2_database: str | None = None
    # db2_user: str | None = None
    # db2_password: SecretStr | None = None
    #
    # db_driver: str = "ODBC Driver 18 for SQL Server"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

settings = Settings()