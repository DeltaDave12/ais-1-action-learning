from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# SQLAlchemy database setup
SQLALCHEMY_DATABASE_URL = (
    "postgresql://postgres:admin@localhost/action_learning"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)
