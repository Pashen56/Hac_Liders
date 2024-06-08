import requests
import sqlite3
import os
import folium
from flask import Flask, render_template, url_for, request, flash, session, redirect, abort, g, make_response
from FDataBase import FDataBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from UserLogin import UserLogin
from forms import LoginForm, RegisterForm

# конфигурация
DATABASE = '/tmp/hac_znanie.db'
DEBUG = True
SECRET_KEY = '1d18ff72159315694f50aada02d0cea9d5c4957f'
MAX_CONTENT_LENGTH = 1024 * 1024
USERNAME = 'admin'
PASSWORD = '123'

app = Flask(__name__)
app.config.from_object(__name__)  # загрузка конфигураций

app.config.update(dict(DATABASE=os.path.join(app.root_path, 'hac_znanie.db')))

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "success"


@login_manager.user_loader
def load_user(user_id):
    print("load_user")
    return UserLogin().fromDB(user_id, dbase)


def connect_db():
    """Соединение с БД"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    """Вспомогательная функция для создания таблиц БД"""
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


def get_db():
    '''Соединение с БД, если оно еще не установлено'''
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


# Метод index обновлен для передачи списка проверок в шаблон
@app.route("/index")
@app.route("/")
@login_required
def index():
    requests_history = dbase.getRequestsHistory()
    print(requests_history)
    return render_template('index.html', menu=dbase.getMenu(), posts=dbase.getPostsAnonce(), requests=requests_history)


@app.route("/about")
def about():
    print(url_for('about'))
    return render_template('aboutsite.html', title="О сайте", menu=dbase.getMenu())


dbase = None


@app.before_request
def before_request():
    """Установление соединения с БД перед выполнением запроса"""
    global dbase
    db = get_db()
    dbase = FDataBase(db)


@app.teardown_appcontext
def close_db(error):
    '''Закрываем соединение с БД, если оно было установлено'''
    if hasattr(g, 'link_db'):
        g.link_db.close()


@app.route("/contact", methods=["POST", "GET"])
@login_required
def contact():
    if request.method == 'POST':
        if len(request.form['username']) > 2:
            flash('Сообщение отправлено', category='success')
        else:
            flash('Ошибка отправки', category='error')
        print(request.form['username'])
        print(request.form['email'])
        print(request.form['message'])
    return render_template('contact.html', title="Обратная связь", menu=dbase.getMenu())


@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    form = LoginForm()
    if form.validate_on_submit():
        user = dbase.getUserByEmail(form.email.data)
        if user and check_password_hash(user['psw'], form.psw.data):
            userlogin = UserLogin().create(user)
            rm = form.remember.data
            login_user(userlogin, remember=rm)
            return redirect(request.args.get("next") or url_for("profile"))

        flash("Неверная пара логин/пароль", "error")

    return render_template("login.html", menu=dbase.getMenu(), title="Авторизация", form=form)


@app.route("/register", methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hash = generate_password_hash(request.form['psw'])
        res = dbase.addUser(form.name.data, form.email.data, hash)
        if res:
            flash("Вы успешно зарегистрированы", "success")
            return redirect(url_for('login'))
        else:
            flash("Ошибка при добавлении в БД", "error")

    return render_template("register.html", menu=dbase.getMenu(), title="Регистрация", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    return render_template("profile.html", menu=dbase.getMenu(), title="Профиль")


@app.errorhandler(404)
def pageNotFount(error):
    return render_template('page404.html', title="Страница не найдена", menu=dbase.getMenu()), 404


@app.route("/post/<alias>")
@login_required
def showPost(alias):
    title, post = dbase.getPost(alias)
    if not title:
        abort(404)

    return render_template('post.html', menu=dbase.getMenu(), title=title, post=post)


@app.route('/userava')
@login_required
def userava():
    img = current_user.getAvatar(app)
    if not img:
        return ""

    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h


@app.route('/upload', methods=["POST", "GET"])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()
                res = dbase.updateUserAvatar(img, current_user.get_id())
                if not res:
                    flash("Ошибка обновления аватара", "error")
                    return redirect(url_for('profile'))
                flash("Аватар обновлен", "success")
            except FileNotFoundError as e:
                flash("Ошибка чтения файла", "error")
        else:
            flash("Ошибка обновления аватара", "error")

    return redirect(url_for('profile'))


@app.route('/aggregate')
@login_required
def aggregate():
    # Центрируем карту на Москве
    start_coords = (55.7558, 37.6173)  # Координаты Москвы
    folium_map = folium.Map(location=start_coords, zoom_start=12)
    resMap = dbase.getMap()
    folium.CircleMarker(
        location=[resMap.latitude, resMap.longitude],
        radius=30,
        popup=f'Риск: {resMap.Risk}',
        color='red',
        fill=True,
        fill_color=f'{resMap.RiskColor}'
    ).add_to(folium_map)

    # Возвращаем HTML с картой
    return folium_map._repr_html_()


if __name__ == "__main__":  # непосредственно на локальном устройстве
    app.run(debug=True)  # запуск фреймворка методом run
# Конечно, после его создания, здесь следует прописать debug=False,
# чтобы случайные ошибки реальный пользователь уже не видел
