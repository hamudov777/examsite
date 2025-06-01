from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=25)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6, max=64)])
    submit = SubmitField('Войти')

class RegisterForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=25)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6, max=64)])
    confirm = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')