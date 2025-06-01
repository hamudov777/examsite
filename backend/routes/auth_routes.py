from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from flask_login import login_required, current_user, login_user, logout_user
from models import db, Result, Exam, Test, User
from datetime import datetime
from forms import RegisterForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if user.username == "Admin" and not user.is_admin:
                user.is_admin = True
                db.session.commit()
            login_user(user)  # Исправлено здесь!
            flash("Вход выполнен!", "success")
            return redirect(url_for('index'))
        else:
            flash("Неверные имя пользователя или пароль.", "danger")
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash("Пользователь уже существует.", "danger")
        else:
            is_admin = form.username.data == "Admin"
            user = User(
                username=form.username.data,
                password_hash=generate_password_hash(form.password.data),
                is_admin=is_admin
            )
            db.session.add(user)
            db.session.commit()
            flash("Регистрация успешна! Теперь войдите.", "success")
            return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта.", "info")
    return redirect(url_for('index'))

# Очистка флага is_admin для всех, кроме "Admin"
@auth_bp.before_app_request
def reset_non_admin_flags():
    users = User.query.all()
    for user in users:
        if user.username != "Admin" and user.is_admin:
            user.is_admin = False
    db.session.commit()