from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from elasticsearch import Elasticsearch
import os
from flask_ngrok import run_with_ngrok

ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')

app = Flask(__name__)
app.config['SECRET_KEY'] = '08f9d43762bca081dc5a2267f07a5267'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cmovies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ELASTICSEARCH_URL'] = 'http://localhost:9200'
app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) if app.config['ELASTICSEARCH_URL'] else None
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from app import routes