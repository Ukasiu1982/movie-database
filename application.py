import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, redirect, request, url_for
from flask import render_template
from tmd_connecotr import TMDConnector
from flask_login import LoginManager, login_user, login_required, logout_user

app = Flask(__name__)
app.secret_key = 'super secret key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

tmd_connector = TMDConnector()
LOGGED = False

#  wysylanie zapytania do api co 12 godzin, seconds określa co ile sa wysylane zapytania do api
scheduler = BackgroundScheduler(timezone="Europe/Berlin")
scheduler.add_job(func=tmd_connector.check_available_provider_for_movie, trigger="interval", seconds=43200)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


@login_manager.user_loader
def load_user(session_id):
    if tmd_connector.session_id == '':
        return None
    return tmd_connector


@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login?next=' + request.path)


@app.route("/", methods=["POST", "GET"])
@login_required
def index():
    #  przekazujemy dane to wygenerowania w html, mozemy przekazac caly obiekt tmd_connector i np dostac z niego
    #  nazwe uzytkownika
    if request.method == 'GET':
        tmd_connector.get_no_provider_list_id()
        user_lists = tmd_connector.get_user_lists()
        context = {
            'tmd': tmd_connector,
            'user_lists': user_lists
        }
        return render_template("index.html", context=context)


@app.route("/delete_list/<list_id>", methods=['GET'])
@login_required
def delete_list(list_id):
    tmd_connector.delete_list(list_id)
    return redirect(url_for("index"))


@app.route("/create_list", methods=['GET', 'POST'])
@login_required
def create_list():
    """create list"""
    if request.method == 'POST':
        name = request.form['name']
        language = request.form['language']
        description = request.form['description']
        object = tmd_connector.create_list(name=name, description=description, language=language)
        return redirect(url_for("index"))
    return render_template("create_list.html")


@app.route("/list/<list_id>")
@login_required
def list_detail(list_id):
    """get list details"""
    movie_list = tmd_connector.get_list_detail(list_id)
    context = {
        'movie_list': movie_list,
        'tmd': tmd_connector
    }
    return render_template("list.html", context=context)


@app.route("/add_movie/<movie_id>")
@login_required
def add_movie(movie_id):
    """
    add movie to list
    """
    tmd_connector.add_movie_to_list(movie_id)
    return redirect(url_for("list_detail", list_id=tmd_connector.actual_list_id))


@app.route("/movie", methods=['GET', 'POST'])
@login_required
def search_movie():
    """add movie to list"""
    if request.method == 'POST':
        language = request.form['language']
        query = request.form['query']
        search_movie = tmd_connector.search_movie(language=language, query=query)
        context = {
            'query': query,
            'search_movie': search_movie,
            'tmd': tmd_connector
        }
        return render_template('search_movie_result.html', context=context)
    else:
        return render_template('search_movie.html')


@app.route("/remove_movie/<movie_id>")
@login_required
def remove_movie(movie_id):
    """remove movie from list"""
    tmd_connector.remove_movie_from_list(movie_id)
    return redirect(url_for("list_detail", list_id=tmd_connector.actual_list_id))


@app.route("/select_provider_region", methods=['POST'])
@login_required
def select_provider_region():
    """set provider region"""
    if request.method == 'POST':
        region = request.form['region']
        tmd_connector.set_selected_region(region)
        return redirect(url_for('index'))
    return redirect(url_for('index'))


@app.route("/login", methods=["POST", "GET"])
def login():
    """
    login user by login_manager
    tmd_connector is use as user object
    """
    #  jezeli metoda = POST, to logujemy sie do TMD api, jezeli sie udalo to logujemy sie do aplikacji
    #  jezeli get to wyswietlamy formularz logowania
    if request.method == "POST":
        login = request.form['login']
        password = request.form['password']

        #  if login to api is successful, we login to application
        if tmd_connector.login_to_api(login, password):
            login_user(tmd_connector)
            return redirect(url_for("index"))
        else:
            return print("not logged")
    else:
        return render_template("login.html")


@login_required
@app.route('/logout')
def logout():
    """logout user"""
    if tmd_connector.delete_session():
        logout_user()
        return redirect('/login?next=' + request.path)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5008)
