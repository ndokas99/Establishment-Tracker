from flask_sqlalchemy import SQLAlchemy
from os import path


db = SQLAlchemy()


class Session(db.Model):
    sessionId = db.Column(db.Text, primary_key=True)
    sessionMap = db.Column(db.Text, nullable=True)
    sessionTime = db.Column(db.DateTime(timezone=True), nullable=True)


def create_database():
    if not path.exists("session.db"):
        db.create_all()