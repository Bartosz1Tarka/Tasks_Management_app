from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

#Tabela asocjacyjna (pomocnicza) dla relacji wiele-do-wielu między Notatkami (Note) a Tagami (Tag)
note_tag = db.Table('note_tag',
    db.Column('note_id', db.Integer, db.ForeignKey('note.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
    )

class Status(db.Model):
    __tablename__ = 'status'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, default="Not assigned")
    color = db.Column(db.String(7), nullable=False, server_default='#808080')
    notes = db.relationship('Note', back_populates='status')

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(7))
    notes = db.relationship('Note', secondary=note_tag, back_populates='tags')

class Note(db.Model):
    __tablename__ = 'note'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), unique=True, nullable=False)
    data = db.Column(db.String(10000), nullable=False)
    deadline = db.Column(db.DateTime(timezone=True), default=func.now())
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    tags = db.relationship('Tag', secondary=note_tag, back_populates='notes')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)
    user = db.relationship('User', back_populates='notes')
    status = db.relationship('Status', back_populates='notes')

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    notes = db.relationship('Note', back_populates='user', cascade='all, delete-orphan')