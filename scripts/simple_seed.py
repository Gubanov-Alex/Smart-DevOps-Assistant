"""Simple database seeding script."""

import asyncio
import random
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text


async def create_sample_data():
    """Create sample data in the database."""
    print("🌱 Creating sample data...")
    
    database_url = "postgresql+asyncpg://devops_user:devops_pass@localhost:5433/devops_assistant"
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Create sample log entries
            log_entries = []
            for i in range(10):
                log_id = str(uuid.uuid4())
                message = f"Sample log message {i+1}"
                level = random.choice(['INFO', 'WARNING', 'ERROR', 'DEBUG'])
                source = random.choice(['web-server', 'api-service', 'database', 'cache'])
                timestamp = datetime.now() - timedelta(hours=random.randint(0, 24))
                
                await session.execute(text("""
                    INSERT INTO log_entries (id, message, level, source, timestamp, created_at)
                    VALUES (:id, :message, :level, :source, :timestamp, :created_at)
                """), {
                    'id': log_id,
                    'message': message,
                    'level': level,
                    'source': source,
                    'timestamp': timestamp,
                    'created_at': datetime.now()
                })
                log_entries.append(log_id)
            
            print(f"✅ Created {len(log_entries)} log entries")
            
            # Create sample incidents
            incidents = []
            for i in range(5):
                incident_id = str(uuid.uuid4())
                title = f"Sample Incident {i+1}"
                description = f"This is a sample incident for testing purposes #{i+1}"
                severity = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
                status = random.choice(['OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED'])
                source = random.choice(['monitoring', 'user-report', 'automated'])
                created_at = datetime.now() - timedelta(hours=random.randint(0, 48))
                
                await session.execute(text("""
                    INSERT INTO incidents (id, title, description, severity, status, source, created_at, updated_at)
                    VALUES (:id, :title, :description, :severity, :status, :source, :created_at, :updated_at)
                """), {
                    'id': incident_id,
                    'title': title,
                    'description': description,
                    'severity': severity,
                    'status': status,
                    'source': source,
                    'created_at': created_at,
                    'updated_at': created_at
                })
                incidents.append(incident_id)
            
            print(f"✅ Created {len(incidents)} incidents")
            
            # Create sample ML models
            models = []
            for i in range(3):
                model_id = str(uuid.uuid4())
                name = f"sample-model-{i+1}"
                version = f"1.{i}.0"
                model_type = random.choice(['classifier', 'anomaly_detector', 'predictor'])
                status = random.choice(['TRAINING', 'TRAINED', 'DEPLOYED', 'READY'])
                created_at = datetime.now() - timedelta(days=random.randint(1, 30))
                accuracy = random.uniform(0.8, 0.95)
                
                await session.execute(text("""
                    INSERT INTO ml_models (id, name, version, model_type, status, created_at, updated_at, accuracy, is_active)
                    VALUES (:id, :name, :version, :model_type, :status, :created_at, :updated_at, :accuracy, :is_active)
                """), {
                    'id': model_id,
                    'name': name,
                    'version': version,
                    'model_type': model_type,
                    'status': status,
                    'created_at': created_at,
                    'updated_at': created_at,
                    'accuracy': accuracy,
                    'is_active': status == 'DEPLOYED'
                })
                models.append(model_id)
            
            print(f"✅ Created {len(models)} ML models")
            
            # Commit all changes
            await session.commit()
            print("✅ All sample data committed to database")
            
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        await session.rollback()
        return False
    finally:
        await engine.dispose()
    
    return True


async def main():
    """Main seeding function."""
    print("🚀 Starting database seeding...")
    
    if await create_sample_data():
        print("🎉 Database seeding completed successfully!")
    else:
        print("💥 Database seeding failed!")


if __name__ == "__main__":
    asyncio.run(main())
