import os
import asyncio
import aiosqlite

def get_db_path():
    # Try .env first, then environment
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv('.env')
    return os.environ.get("DATABASE_PATH", "vox_data.db")

async def run_schema():
    db_path = get_db_path()
    schema_path = "docs/sqlite_schema.sql"
    
    if not os.path.exists(schema_path):
        print(f"Schema file not found: {schema_path}")
        return
    
    with open(schema_path, "r") as f:
        schema = f.read()
    
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(schema)
        await db.commit()
        print(f"Schema applied successfully to {db_path}")

if __name__ == "__main__":
    asyncio.run(run_schema())
