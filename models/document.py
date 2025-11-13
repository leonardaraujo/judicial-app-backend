from sqlalchemy import Column, Integer, String, Text
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