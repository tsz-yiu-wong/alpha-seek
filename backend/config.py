'''
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379"
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "your-token"
    INFLUXDB_ORG: str = "your-org"
    INFLUXDB_BUCKET: str = "meme_coin_data"

    class Config:
        env_file = ".env"

settings = Settings() 
'''