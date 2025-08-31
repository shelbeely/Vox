import os
import asyncio
import asyncpg

def get_db_url():
    # Try .env first, then environment
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv('.env')
    return os.environ.get("SUPABASE_DB_URL")

async def run_schema():
    db_url = get_db_url()
    if not db_url:
        print("SUPABASE_DB_URL not set in environment or .env")
        return
    schema_path = "docs/supabase_schema.sql"
    if not os.path.exists(schema_path):
        print(f"Schema file not found: {schema_path}")
        return
    with open(schema_path, "r") as f:
        sql = f.read()
    # Split on semicolons, ignore empty statements
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    conn = await asyncpg.connect(db_url)
    try:
        for stmt in statements:
            await conn.execute(stmt)
        print("Schema applied successfully.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_schema())
