from sqlalchemy.orm import scoped_session, sessionmaker
from sqlmodel import Session

TestSession = scoped_session(sessionmaker(class_=Session, expire_on_commit=False))
