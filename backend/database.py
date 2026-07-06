from pickle import TRUE
from sqlmodel import create_engine, SQLModel, Session
from config import DATABASE_URL


engine  = create_engine(DATABASE_URL, echo=True, connect_args={
    'check_same_thread': False
})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
