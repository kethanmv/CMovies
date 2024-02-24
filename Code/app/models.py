import app
from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from app.search import add_to_index, remove_from_index, query_index


@login_manager.user_loader
def load_user(user_id):
	return Users.query.get(int(user_id))


class Users(db.Model, UserMixin):
	userid = db.Column(db.Integer,primary_key=True)
	username = db.Column(db.String(20),unique=True,nullable=False)
	email = db.Column(db.String(120),unique=True,nullable=False)
	image_file = db.Column(db.String(20),nullable=False,default='default.jpg')
	password = db.Column(db.String(60),nullable=False)

	def get_id(self):
		return (self.userid)

	def __repr__(self):
		return f"Users('{self.userid}','{self.username}','{self.email}','{self.image_file}','{self.password}')"

class Movies(db.Model):
	movieid = db.Column(db.String(30),primary_key=True)
	movie_title = db.Column(db.String(100),unique=True,nullable=False)
	desc = db.Column(db.String(1024),unique=True,nullable=False)
	release_year = db.Column(db.String(5),nullable=False, default=str(datetime.now().year))
	genre = db.Column(db.String(50),nullable=False)
	movie_length = db.Column(db.String(10),nullable=False)
	language = db.Column(db.String(20),nullable=False)
	director = db.Column(db.String(50),nullable=False)
	act_cast = db.Column(db.String(50),nullable=False)
	movie_link = db.Column(db.String(100),nullable=False,unique=True)
	movie_pic = db.Column(db.String(20),nullable=False,default='default_movie.jpg')
	youtube_id = db.Column(db.String(100),nullable=False,unique=True)

	__searchable__ = ['movie_title','desc','genre','director','act_cast','language']

	def __repr__(self):
		return f"Movies('{self.movieid}','{self.movie_title}','{self.desc}','{self.release_year}','{self.genre}','{self.movie_length}','{self.language}','{self.director}','{self.act_cast}','{self.movie_link}','{self.movie_pic}','{self.youtube_id}')"


class Likes(db.Model):
	userid = db.Column(db.Integer,nullable=False,primary_key=True)
	movieid = db.Column(db.String(30),nullable=False,primary_key=True)
	timestamp = db.Column(db.DateTime,nullable=False,primary_key=True)


class MyList(db.Model):
	userid = db.Column(db.Integer,nullable=False,primary_key=True)
	movieid = db.Column(db.String(30),nullable=False,primary_key=True)
	timestamp = db.Column(db.DateTime,nullable=False,primary_key=True)


class WatchHistory(db.Model):
	userid = db.Column(db.Integer,nullable=False,primary_key=True)
	movieid = db.Column(db.String(30),nullable=False,primary_key=True)
	timestamp = db.Column(db.DateTime,nullable=False,primary_key=True)


class Views(db.Model):
	movieid = db.Column(db.String(30),primary_key=True)
	views = db.Column(db.Integer,default=0,nullable=False) 