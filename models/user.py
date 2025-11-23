from sqlalchemy import Column, String, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from database.database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
