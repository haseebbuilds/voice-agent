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
    """Initialize database connection"""
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        # Test connection
        await Tortoise.get_connection("default").execute_query("SELECT 1")
        await Tortoise.generate_schemas()
        print(f"Connected to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'database'}")
    except Exception as e:
        print(f"Database connection error: {e}")
        print(f"Attempted connection string: postgres://postgres:***@{DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")
        raise


async def close_db():
    """Close database connection"""
    await Tortoise.close_connections()

