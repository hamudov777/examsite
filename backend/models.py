from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    results = db.relationship('Result', backref='user', lazy=True)

class Exam(db.Model):
    __tablename__ = "exam"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=True)
    grade = db.Column(db.String(16), nullable=True)
    tests = db.relationship('Test', backref='exam', cascade="all, delete-orphan", lazy=True)

class Quiz(db.Model):
    __tablename__ = "quiz"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=True)
    tests = db.relationship('Test', backref='quiz', cascade="all, delete-orphan", lazy=True)

class Test(db.Model):
    __tablename__ = "test"
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=True)
    answers = db.relationship('Answer', backref='test', cascade="all, delete-orphan", lazy=True)

class Answer(db.Model):
    __tablename__ = "answer"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)

class Result(db.Model):
    __tablename__ = "result"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)  # ID экзамена или quiz
    item_type = db.Column(db.String(10), nullable=False)  # 'exam' или 'quiz'
    title = db.Column(db.String(255), nullable=False)  # Название экзамена/quiz для истории
    date = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Integer, nullable=False)