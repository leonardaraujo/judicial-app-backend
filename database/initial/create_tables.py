from database.database import Base, engine
from models.user import User
from models.document import Document

print("FKs registradas:", Base.metadata.tables["documents"].foreign_keys)

# Crear primero users, luego documents
User.__table__.create(bind=engine, checkfirst=True)
Document.__table__.create(bind=engine, checkfirst=True)

print("Tablas creadas con foreign keys")