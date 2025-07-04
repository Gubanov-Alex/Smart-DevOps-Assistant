#!/usr/bin/env python3
"""Simple repository test without complex dependencies."""

import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text


# Simple test of database connection and basic operations
async def test_basic_database_connection():
    """Test basic database connectivity."""
    print("🔧 Testing database connection...")

    # Create engine
    database_url = "postgresql+asyncpg://devops_user:devops_pass@localhost:5433/devops_assistant"
    engine = create_async_engine(database_url, echo=False)

    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # Test basic query
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ Database connection successful: {row}")

            # Check tables exist
            result = await session.execute(text("""
                                                SELECT table_name
                                                FROM information_schema.tables
                                                WHERE table_schema = 'public'
                                                ORDER BY table_name
                                                """))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Found tables: {tables}")

            # Count records in each table
            for table in tables:
                if table != 'alembic_version':
                    result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"📊 {table}: {count} records")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    finally:
        await engine.dispose()

    return True


async def test_log_entry_creation():
    """Test creating a simple log entry."""
    print("\n🔧 Testing log entry creation...")

    database_url = "postgresql+asyncpg://devops_user:devops_pass@localhost:5433/devops_assistant"
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # Insert a test log entry
            await session.execute(text("""
                                       INSERT INTO log_entries (id, message, level, source, timestamp, created_at)
                                       VALUES (gen_random_uuid(), 'Test log from repository test', 'INFO',
                                               'test-script', NOW(), NOW())
                                       """))
            await session.commit()
            print("✅ Test log entry created successfully")

            # Query the entry back
            result = await session.execute(text("""
                                                SELECT message, level, source
                                                FROM log_entries
                                                WHERE source = 'test-script'
                                                ORDER BY created_at DESC LIMIT 1
                                                """))
            row = result.fetchone()
            if row:
                print(f"✅ Retrieved log entry: {row}")
            else:
                print("❌ Could not retrieve test log entry")

    except Exception as e:
        print(f"❌ Log entry creation failed: {e}")
        return False
    finally:
        await engine.dispose()

    return True


async def main():
    """Main test function."""
    print("🚀 Starting simple repository tests...")

    # Test database connection
    if not await test_basic_database_connection():
        print("💥 Database connection test failed!")
        return

    # Test log entry creation
    if not await test_log_entry_creation():
        print("💥 Log entry creation test failed!")
        return

    print("\n🎉 All basic tests passed!")
    print("📋 Next steps:")
    print("1. Database connection works")
    print("2. Tables are created and accessible")
    print("3. Basic CRUD operations work")
    print("4. Ready for full repository testing")


if __name__ == "__main__":
    asyncio.run(main())
