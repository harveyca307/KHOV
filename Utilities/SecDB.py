import os
import sys

from sqlalchemy import create_engine, Column, String, Integer, update, delete, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(__file__)


class PyDB(Base):
    __tablename__ = 'secrets'

    id = Column('id', Integer, primary_key=True)
    secret = Column('secret', String, unique=True, nullable=False)
    username = Column('username', String, nullable=False)
    password = Column('password', String, nullable=False)


class DB(PyDB):
    def __init__(self):
        super().__init__()
        db = os.path.join(application_path, 'secrets.db')
        self.engine = create_engine('sqlite:///' + db)
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def create_secrets(self, secret: str, username: str, password: str):
        db = PyDB()
        db.secret = secret
        db.username = username
        db.password = password
        self.session.add(db)
        self.session.commit()

    def retrieve_secrets(self, secret: str):
        stmt = select(PyDB.username, PyDB.password).where(PyDB.secret == secret)
        _results = self.session.execute(stmt)
        return _results

    def update_secret(self, secret: str, username: str or None, password: str):
        if username:
            stmt = update(PyDB).where(PyDB.secret == secret).values(username=username, password=password)
        else:
            stmt = update(PyDB).where(PyDB.secret == secret).values(password=password)
        self.session.execute(stmt)
        self.session.commit()

    def delete_secret(self, secret: str):
        stmt = delete(PyDB).where(PyDB.secret == secret)
        self.session.execute(stmt)
        self.session.commit()

    def secret_exists(self, secret: str) -> bool:
        stmt = select(PyDB.secret).where(PyDB.secret == secret)
        _results = self.session.execute(stmt).first()
        if not _results:
            return False
        else:
            return True
