# app
from flask import Flask
# login
from flask_login import LoginManager
# sent mail
from flask_mail import Mail
# db
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
# other
from werkzeug.routing import BaseConverter
from dotenv import load_dotenv
from datetime import timedelta
import os

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()

class SignedIntConverter(BaseConverter):
    regex = r'-?\d+'
    
    def to_python(self, value):
        return int(value)
    
    def to_url(self, value):
        return str(value)



def create_app() :
    app = Flask(__name__)

    # load env data
    load_dotenv()
    app.secret_key = os.environ.get("SECRET_KEY", "idk-bruh") # secret key
    app.permanent_session_lifetime = timedelta(days=3) # set session time
    
    # mail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get("SENDER_MAIL", "idk-bruh")
    app.config['MAIL_PASSWORD'] = os.environ.get("SENDER_PASSWORD", "idk-bruh")
    # init mail
    mail.init_app(app)

    # db
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///data.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    # init db
    db.init_app(app)
    migrate.init_app(app, db) 

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    # login
    login_manager.init_app(app)
    # set page login to redirect if user not login yet
    login_manager.login_view = "main.login"
    login_manager.login_message_category = "info"

    # converters
    app.url_map.converters['sint'] = SignedIntConverter
    

    # Register API blueprints from routes/api/
    from .routes.api import auth_api, user_api, plan_api, schedule_api, feedback_api
    app.register_blueprint(auth_api)
    app.register_blueprint(user_api)
    app.register_blueprint(plan_api)
    app.register_blueprint(schedule_api)
    app.register_blueprint(feedback_api)

    # Register web blueprints from routes/web/
    from .routes.web import web_login, web_password, web_dashboard, web_feedback, web_schedule
    app.register_blueprint(web_login)
    app.register_blueprint(web_password)
    app.register_blueprint(web_dashboard)
    app.register_blueprint(web_feedback)
    app.register_blueprint(web_schedule)

    return app

