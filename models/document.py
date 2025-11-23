from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(100))
    case_year = Column(String(10))
    crime = Column(Text)
    verdict = Column(Text)
    cited_jurisprudence = Column(Text)
    file_path = Column(String(255))
    detected_names = Column(Text)
    resume = Column(Text)

    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    is_approved = Column(Boolean, default=False)

    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    uploader = relationship("User", backref="documents")
