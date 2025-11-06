from database.database import Base, engine
import models.document

Base.metadata.create_all(bind=engine)
print("Tables created!")