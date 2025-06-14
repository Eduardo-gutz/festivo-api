from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "festivodb")
SECRET_KEY = os.environ.get("SECRET_KEY", "secret")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
