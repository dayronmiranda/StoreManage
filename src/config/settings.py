import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    def __init__(self):
        # Database
        self.MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.DATABASE_NAME = os.getenv("DATABASE_NAME", "sistema_gestion")

        # Security (simplified for MVP)
        self.SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")

        # File Upload
        self.UPLOAD_PATH = os.getenv("UPLOAD_PATH", "./uploads")
        self.MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "5242880"))  # 5MB
        self.ALLOWED_IMAGE_TYPES = os.getenv("ALLOWED_IMAGE_TYPES", "image/jpeg,image/png,image/jpg")

        # Environment
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

        # CORS
        self.ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

    @property
    def allowed_image_types_list(self) -> List[str]:
        return self.ALLOWED_IMAGE_TYPES.split(",")


settings = Settings()