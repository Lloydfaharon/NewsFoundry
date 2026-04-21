from dotenv import load_dotenv
load_dotenv()

from src.database import engine
from sqlalchemy import text

with engine.connect() as con:
    con.execute(text('DROP TABLE IF EXISTS chat CASCADE;'))
    con.commit()
print("Table chat supprimée avec succès !")
