from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Session(db.Model):
    sessionId = db.Column(db.Text, primary_key=True)
    sessionMap = db.Column(db.Text, nullable=True)
    sessionTime = db.Column(db.DateTime(timezone=True), nullable=True)

