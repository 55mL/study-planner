from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.routing import BaseConverter

from apscheduler.schedulers.background import BackgroundScheduler
from app.notification.scheduler import batch_job
from app.notification.scheduler import start_scheduler

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

def create_app():
    app = Flask(__name__)

    load_dotenv()
    app.secret_key = os.environ.get("SECRET_KEY", "idk-bruh")
    app.permanent_session_lifetime = timedelta(days=3)
    
    # mail config
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get("SENDER_MAIL", "idk-bruh")
    app.config['MAIL_PASSWORD'] = os.environ.get("SENDER_PASSWORD", "idk-bruh")
    mail.init_app(app)

    # db config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///data.db")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    db.init_app(app)
    migrate.init_app(app, db)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    # ✅ login_manager config
    login_manager.init_app(app)
    login_manager.login_view = "web_login.login"  # เปลี่ยนตาม blueprint ของคุณ
    login_manager.login_message_category = "info"

    # ✅ ต้องมี user_loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # converters
    app.url_map.converters['sint'] = SignedIntConverter
    
    # Register blueprints
    from .routes.api import auth_api, user_api, plan_api, schedule_api, feedback_api, study_api
    app.register_blueprint(auth_api)
    app.register_blueprint(user_api)
    app.register_blueprint(plan_api)
    app.register_blueprint(schedule_api)
    app.register_blueprint(feedback_api)
    app.register_blueprint(study_api)

    from .routes.web import web_login, web_password, web_dashboard, web_feedback, web_schedule
    app.register_blueprint(web_login)
    app.register_blueprint(web_password)
    app.register_blueprint(web_dashboard)
    app.register_blueprint(web_feedback)
    app.register_blueprint(web_schedule)

    from .routes.web import web_main
    app.register_blueprint(web_main)

    # ✅ เริ่ม scheduler ตอน app start
    start_scheduler()

    with app.app_context():
        batch_job()

    return app