from flask import Flask, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'secret-key-change-in-production')

database_url = os.environ.get('DB_URL') or os.environ.get('DATABASE_URL')
if not database_url:
    db_user = os.environ.get('POSTGRES_USER', 'postgres')
    db_pass = os.environ.get('POSTGRES_PASSWORD', '123')
    db_name = os.environ.get('POSTGRES_DB', 'sweater')
    db_host = os.environ.get('DB_HOST', 'postgres')
    db_port = os.environ.get('DB_PORT', '5432')
    database_url = f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# ==================== HTML Pages ====================

@app.route('/')
def index():
    html = '''
    <html>
    <head><title>Sweater</title></head>
    <body style="font-family:Arial;text-align:center;padding:50px;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;margin:0;">
        <div style="background:white;padding:40px;border-radius:12px;box-shadow:0 10px 40px rgba(0,0,0,0.2);width:360px;margin:0 auto;">
            <h1 style="color:#333;">Добро пожаловать!</h1>
            <div style="margin:30px 0;">
                <a href="/login" style="display:inline-block;padding:15px 30px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;text-decoration:none;border-radius:8px;margin:10px;">Вход</a>
                <a href="/register" style="display:inline-block;padding:15px 30px;background:linear-gradient(135deg,#764ba2,#667eea);color:white;text-decoration:none;border-radius:8px;margin:10px;">Регистрация</a>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/login')
def login():
    return '''
    <html>
    <head><title>Вход</title></head>
    <body style="font-family:Arial;text-align:center;padding:50px;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;margin:0;">
        <div style="background:white;padding:40px;border-radius:12px;box-shadow:0 10px 40px rgba(0,0,0,0.2);width:360px;margin:0 auto;">
            <h2 style="color:#333;">Вход</h2>
            <div id="msg"></div>
            <form id="loginForm">
                <input type="email" id="email" placeholder="Email" required style="width:100%;padding:14px;margin:10px 0;border:2px solid #e0e0e0;border-radius:6px;font-size:16px;box-sizing:border-box;">
                <input type="password" id="password" placeholder="Пароль" required style="width:100%;padding:14px;margin:10px 0;border:2px solid #e0e0e0;border-radius:6px;font-size:16px;box-sizing:border-box;">
                <button type="submit" style="width:100%;padding:14px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:6px;font-size:16px;cursor:pointer;margin-top:10px;">Войти</button>
            </form>
            <div style="margin-top:16px;color:#666;">Нет аккаунта? <a href="/register" style="color:#667eea;">Зарегистрироваться</a></div>
        </div>
    </body>
    </html>
    <script>
        document.getElementById('loginForm').onsubmit = async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            try {
                const res = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password }),
                    credentials: 'include'
                });
                const data = await res.json();
                if (res.ok) {
                    document.getElementById('msg').innerHTML = '<div style="background:#e8f5e9;color:#2e7d32;padding:12px;border-radius:6px;margin-bottom:12px;">Успех! Добро пожаловать, ' + data.name + '!</div>';
                    setTimeout(() => window.location.href = '/profile', 1500);
                } else {
                    document.getElementById('msg').innerHTML = '<div style="background:#ffebee;color:#c62828;padding:12px;border-radius:6px;margin-bottom:12px;">' + (data.error || 'Ошибка входа') + '</div>';
                }
            } catch (err) {
                document.getElementById('msg').innerHTML = '<div style="background:#ffebee;color:#c62828;padding:12px;border-radius:6px;margin-bottom:12px;">Ошибка соединения</div>';
            }
        };
    </script>
    '''

@app.route('/register')
def register():
    return '''
    <html>
    <head><title>Регистрация</title></head>
    <body style="font-family:Arial;text-align:center;padding:50px;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;margin:0;">
        <div style="background:white;padding:40px;border-radius:12px;box-shadow:0 10px 40px rgba(0,0,0,0.2);width:360px;margin:0 auto;">
            <h2 style="color:#333;">Регистрация</h2>
            <div id="msg"></div>
            <form id="registerForm">
                <input type="text" id="name" placeholder="Имя" required style="width:100%;padding:14px;margin:10px 0;border:2px solid #e0e0e0;border-radius:6px;font-size:16px;box-sizing:border-box;">
                <input type="email" id="email" placeholder="Email" required style="width:100%;padding:14px;margin:10px 0;border:2px solid #e0e0e0;border-radius:6px;font-size:16px;box-sizing:border-box;">
                <input type="password" id="password" placeholder="Пароль" required style="width:100%;padding:14px;margin:10px 0;border:2px solid #e0e0e0;border-radius:6px;font-size:16px;box-sizing:border-box;">
                <button type="submit" style="width:100%;padding:14px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:6px;font-size:16px;cursor:pointer;margin-top:10px;">Зарегистрироваться</button>
            </form>
            <div style="margin-top:16px;color:#666;">Уже есть аккаунт? <a href="/login" style="color:#667eea;">Войти</a></div>
        </div>
    </body>
    </html>
    <script>
        document.getElementById('registerForm').onsubmit = async (e) => {
            e.preventDefault();
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            try {
                const res = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, password })
                });
                const data = await res.json();
                if (res.ok) {
                    document.getElementById('msg').innerHTML = '<div style="background:#e8f5e9;color:#2e7d32;padding:12px;border-radius:6px;margin-bottom:12px;">Регистрация успешна!</div>';
                    setTimeout(() => window.location.href = '/login', 1500);
                } else {
                    document.getElementById('msg').innerHTML = '<div style="background:#ffebee;color:#c62828;padding:12px;border-radius:6px;margin-bottom:12px;">' + (data.error || 'Ошибка') + '</div>';
                }
            } catch (err) {
                document.getElementById('msg').innerHTML = '<div style="background:#ffebee;color:#c62828;padding:12px;border-radius:6px;margin-bottom:12px;">Ошибка соединения</div>';
            }
        };
    </script>
    '''

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    return '''
    <html>
    <head><title>Профиль</title></head>
    <body style="font-family:Arial;text-align:center;padding:50px;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;margin:0;">
        <div style="background:white;padding:40px;border-radius:12px;box-shadow:0 10px 40px rgba(0,0,0,0.2);width:360px;margin:0 auto;">
            <div style="background:linear-gradient(135deg,#11998e,#38ef7d);color:white;padding:16px;border-radius:8px;margin-bottom:20px;font-size:18px;">Вы успешно вошли!</div>
            <h2 style="color:#333;">Добро пожаловать!</h2>
            <div style="font-size:24px;margin-bottom:24px;color:#667eea;font-weight:bold;">''' + session.get('user_name', '') + '''</div>
            <a href="/logout" style="display:inline-block;padding:12px 24px;background:linear-gradient(135deg,#f093fb,#f5576c);color:white;text-decoration:none;border-radius:6px;">Выйти</a>
        </div>
    </body>
    </html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ==================== REST API ====================

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not all([name, email, password]):
        return jsonify({'error': 'Заполните все поля'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email уже зарегистрирован'}), 400

    user = User(name=name, email=email, password=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'Регистрация успешна', 'id': user.id})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        session['user_name'] = user.name
        return jsonify({'message': 'Успешный вход', 'name': user.name})
    return jsonify({'error': 'Неверный email или пароль'}), 401

@app.route('/api/profile', methods=['GET'])
def api_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    return jsonify({'name': session.get('user_name')})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'message': 'Выход выполнен'})

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)