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