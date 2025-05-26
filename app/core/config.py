from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(dotenv_path=".env", override=True)


class Settings(BaseSettings):
    POSTGRES_DB_HOST: str
    POSTGRES_DB_PORT: int
    POSTGRES_DB_USER: str
    POSTGRES_DB_PASS: str
    POSTGRES_DB_NAME: str

    TEST_POSTGRES_DB_HOST: str
    TEST_POSTGRES_DB_PORT: int
    TEST_POSTGRES_DB_USER: str
    TEST_POSTGRES_DB_PASS: str
    TEST_POSTGRES_DB_NAME: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    @property
    def TEST_POSTGRES_URL_ASYNC(self):
        return f"postgresql+asyncpg://{self.TEST_POSTGRES_DB_USER}:{self.TEST_POSTGRES_DB_PASS}@{self.TEST_POSTGRES_DB_HOST}:{self.TEST_POSTGRES_DB_PORT}/{self.TEST_POSTGRES_DB_NAME}"

    @property
    def POSTGRES_URL_ASYNC(self):
        return f"postgresql+asyncpg://{self.POSTGRES_DB_USER}:{self.POSTGRES_DB_PASS}@{self.POSTGRES_DB_HOST}:{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings: Settings = Settings()
