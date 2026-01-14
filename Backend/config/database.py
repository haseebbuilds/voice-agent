"""
Database configuration for Tortoise ORM
"""
from tortoise import Tortoise
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get DATABASE_URL and strip quotes if present
database_url = os.getenv("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/voice_intake")
DATABASE_URL = database_url.strip('"').strip("'")  # Remove quotes if present

TORTOISE_ORM = {
    "connections": {
        "default": DATABASE_URL
    },
    "apps": {
        "models": {
            "models": ["models.caller", "models.intake_call", "models.case_question", 
                      "models.appointment", "models.calendar_event", "aerich.models"],
            "default_connection": "default",
        },
    },
}


async def init_db():
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        await Tortoise.get_connection("default").execute_query("SELECT 1")
        await Tortoise.generate_schemas()
    except Exception:
        raise


async def close_db():
    await Tortoise.close_connections()

