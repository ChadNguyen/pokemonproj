from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config) # Config Class
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Disable deprecated feature
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)

from app import routes, models

# create the tables in the database
db.create_all()




