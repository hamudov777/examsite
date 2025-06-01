from flask import Flask, render_template
from models import db, User
from routes.auth_routes import auth_bp
from routes.student_routes import student_bp
from routes.admin_routes import admin_bp
from flask_login import LoginManager

app = Flask(__name__, instance_relative_config=True)
# Загружает конфиг из ../instance/config.py (если вы запускаете из backend)
app.config.from_pyfile('../instance/config.py', silent=True)

# Инициализация базы данных
db.init_app(app)

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Blueprint'ы
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(admin_bp, url_prefix='/admin')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)