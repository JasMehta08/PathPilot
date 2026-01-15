from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    CAMPUS_LOCATION: str = "Gandhinagar, India"
    UPLOAD_DIR: Path = Path("data/uploads")
    MODELS_DIR: Path = Path("data/models")
    TEMP_PROCESS_DIR: Path = Path("temp_process")
    
    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.MODELS_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
