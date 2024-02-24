import os
import secrets
import random
from PIL import Image
from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, request, jsonify
from app import app, db, bcrypt
from sqlalchemy import func
from app.forms import RegistrationForm, LoginForm, UpdateAccountForm, SearchForm
from app.models import Users, Movies, Likes, MyList, Views, WatchHistory
from flask_login import login_user, current_user, logout_user, login_required
from app.search import add_to_index, query_index, remove_from_index
from app.recommend import recommendations



def save_picture(form_picture):
	random_hex = secrets.token_hex(8)
	_, f_ext = os.path.splitext(form_picture.filename)
	picture_fname = random_hex + f_ext
	picture_path = os.path.join(app.root_path, 'static/profile_pics',picture_fname)

	output_size = (125,125)
	i = Image.open(form_picture)
	i.thumbnail(output_size)
	i.save(picture_path)
	
	if(current_user.image_file!='default.jpg'):
		del_file = current_user.image_file
		os.remove(os.path.join(app.root_path, 'static/profile_pics',del_file))

	return picture_fname


@app.route("/")
@app.route("/landing")
def landing():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	return render_template('landing.html')


@app.route("/index", methods=['GET','POST'])
@app.route("/home", methods=['GET','POST'])
@login_required
def home():
	#movies_all = Movies.query.limit(15).all()
	car = ['tt0910970','tt1950186','tt2015381','tt4154796','tt4729430','tt6751668','tt8579674']
	carousel = Movies.query.filter(Movies.movieid.in_(random.sample(car, 4))).all()

	views_all = Views.query.with_entities(Views.movieid).order_by(Views.views.desc()).limit(20).all()
	most_views = [i[0] for i in views_all]
	trending = Movies.query.filter(Movies.movieid.in_(most_views)).limit(20).all()

	likes_all = Likes.query.with_entities(Likes.movieid).filter_by(userid=current_user.userid).all()
	likes = [i[0] for i in likes_all]


	lv_id = []
	watchlist = WatchHistory.query.with_entities(WatchHistory.movieid).filter_by(userid=current_user.userid).all()
	watchlist = [i[0] for i in watchlist]
	lv_id = lv_id + watchlist + likes
	lv_id = set(lv_id)
	lv_id = list(lv_id)
	recommendx = []
	if(len(lv_id)==0):
		recommendx = Movies.query.order_by(func.random()).limit(20).all()
		print("No user activity yet!")
		#print(recommendx)
	else:
		o = Movies.query.with_entities(Movies.movie_title).filter(Movies.movieid.in_(lv_id)).all()
		o = [i[0] for i in o]
		temp = recommendations(o)
		print(temp)
		recommendx = Movies.query.filter(Movies.movie_title.in_(temp)).all()


	
	mylist_all = MyList.query.with_entities(MyList.movieid).filter_by(userid=current_user.userid).all()
	mylist = [i[0] for i in mylist_all]
	my_list = Movies.query.filter(Movies.movieid.in_(mylist)).limit(20).all() 

	comedies = Movies.query.filter(Movies.genre.contains('Comedy')).limit(20).all()

	indian_movies = Movies.query.filter(Movies.language.contains('Hindi')).limit(20).all()

	form = SearchForm()
	if form.validate_on_submit():
		return redirect(url_for('search', search_text=form.search_field.data))
	image_file = url_for('static', filename='profile_pics/'+current_user.image_file)
	return render_template('home.html', title='Home',image_file = image_file, form=form, recommendx=recommendx, my_list=my_list, comedies=comedies, indian=indian_movies, likes=likes, mylist=mylist, carousel1=carousel[0], carousel2=carousel[1],carousel3=carousel[2],carousel4=carousel[3])


@app.route("/search/<search_text>", methods=['GET','POST'])
@login_required
def search(search_text):
	likes_all = Likes.query.with_entities(Likes.movieid).filter_by(userid=current_user.userid).all()
	likes = [i[0] for i in likes_all]

	mylist_all = MyList.query.with_entities(MyList.movieid).filter_by(userid=current_user.userid).all()
	mylist = [i[0] for i in mylist_all]

	x = query_index('movies',search_text,1,100)
	s = [i['_id'] for i in x]
	search_results = Movies.query.filter(Movies.movieid.in_(s)).all()

	form = SearchForm()
	if form.validate_on_submit():
		return redirect(url_for('search', search_text=form.search_field.data))
	image_file = url_for('static', filename='profile_pics/'+current_user.image_file)
	return render_template('search.html',title='Search Results', search_text=search_results,image_file=image_file, form=form, likes=likes, my_list=mylist)


@app.route("/mylist", methods=['GET','POST'])
@login_required
def mylist():
	likes_all = Likes.query.with_entities(Likes.movieid).filter_by(userid=current_user.userid).all()
	likes = [i[0] for i in likes_all]

	mylist_all = MyList.query.with_entities(MyList.movieid).filter_by(userid=current_user.userid).all()
	mylist = [i[0] for i in mylist_all]
	my_movies = Movies.query.filter(Movies.movieid.in_(mylist)).all()

	form = SearchForm()
	if form.validate_on_submit():
		return redirect(url_for('search', search_text=form.search_field.data))
	image_file = url_for('static', filename='profile_pics/'+current_user.image_file)
	return render_template('mylist.html',title='My List', mylist = my_movies,form=form,image_file=image_file,likes=likes, my_list=mylist)


@app.route("/getcounts/<movie_id>")
@login_required
def views(movie_id):
	viewsx = Views.query.filter_by(movieid=movie_id).first()
	l=[]
	likesx = Likes.query.filter_by(movieid=movie_id).all()
	#print(len(likesx))
	#print(viewsx.views)
	obj = [{ "likes":len(likesx),"views": viewsx.views}]
	return jsonify(obj),200


@app.route("/clear")
@login_required
def clear():
	delete_q = WatchHistory.__table__.delete().where(WatchHistory.userid == str(current_user.userid))
	db.session.execute(delete_q)
	db.session.commit()
	return redirect(url_for('history'))


@app.route("/latest", methods=['GET','POST'])
@login_required
def latest():
	views_all = Views.query.with_entities(Views.movieid).order_by(Views.views.desc()).limit(20).all()
	most_views = [i[0] for i in views_all]
	trending = Movies.query.filter(Movies.movieid.in_(most_views)).limit(20).all()
	new_movies = Movies.query.filter(Movies.release_year.in_(["2019","2018","2017"])).order_by(Movies.release_year.desc()).limit(20).all()
	
	likes_all = Likes.query.with_entities(Likes.movieid).filter_by(userid=current_user.userid).all()
	likes = [i[0] for i in likes_all]

	mylist_all = MyList.query.with_entities(MyList.movieid).filter_by(userid=current_user.userid).all()
	mylist = [i[0] for i in mylist_all]

	form = SearchForm()
	if form.validate_on_submit():
		return redirect(url_for('search', search_text=form.search_field.data))
	image_file = url_for('static', filename='profile_pics/'+current_user.image_file)
	return render_template('latest.html', title='Latest',image_file = image_file, form=form, trending=trending, likes=likes, mylist=mylist, new_movies=new_movies)


@app.route("/like/<movie_id>", methods=['GET','POST'])
@login_required
def like(movie_id):
	like = Likes(userid=current_user.userid,movieid=movie_id,timestamp=datetime.now())
	x = Likes.query.filter_by(movieid=movie_id,userid=current_user.userid).first()
	if not x:
		db.session.add(like)
		db.session.commit()
	else:
		db.session.delete(x)
		db.session.commit()
	url = str(request.referrer)
	if('search' in url):
		x = url.split("/")
		#print(x)
		return redirect(url_for('search',search_text=str(x[-1])))
	elif('info' in url):
		x = url.split("/")
		#print(x)
		return redirect(url_for('info',video_id=str(x[-1])))
	elif('watch' in url):
		x = url.split("/")
		return redirect(url_for('watch',youtube_id=str(x[-1])))
	else:
		url = url.split("/")[-1]
	return redirect(url_for(url))


@app.route("/add_to_list/<movie_id>", methods=["GET","POST"])
@login_required
def add_to_list(movie_id):
	listx = MyList(userid=current_user.userid,movieid=movie_id,timestamp=datetime.now())
	x = MyList.query.filter_by(movieid=movie_id,userid=current_user.userid).first()
	if not x:
		db.session.add(listx)
		db.session.commit()
	else:
		db.session.delete(x)
		db.session.commit()
	url = str(request.referrer)
	if('search' in url):
		x = url.split("/")
		#print(x)
		return redirect(url_for('search',search_text=str(x[-1])))
	elif('info' in url):
		x = url.split("/")
		#print(x)
		return redirect(url_for('info',video_id=str(x[-1])))
	elif('watch' in url):
		x = url.split("/")
		return redirect(url_for('watch',youtube_id=str(x[-1])))
	else:
		url = url.split("/")[-1]
	return redirect(url_for(url))


@app.route("/info/<video_id>", methods=['GET','POST'])
@login_required
def info(video_id):
	likes_all = Likes.query.with_entities(Likes.movieid).filter_by(userid=current_user.userid).all()
	likes = [i[0] for i in likes_all]

	mylist_all = MyList.query.with_entities(MyList.movieid).filter_by(userid=current_user.userid).all()
	mylist = [i[0] for i in mylist_all]

	form = SearchForm()
	if form.validate_on_submit():
		return redirect(url_for('search', search_text=form.search_field.data))
	movie = Movies.query.filter_by(movieid=video_id).first()
	image_file = url_for('static', filename='profile_pics/'+current_user.image_file)
	return render_template('info.html',title='Info - '+movie.movie_title, movie=movie,form=form,image_file=image_file,likes=likes, my_list=mylist)


@app.route("/remove/<movie_id>", methods=['GET','POST'])
@login_required
def remove_from_list(movie_id):
	x = MyList.query.filter_by(movieid=movie_id,userid=current_user.userid).first()
	if x:
		db.session.delete(x)
		db.session.commit()
	return redirect(url_for('mylist'))


@app.route("/watch/<youtube_id>", methods=['GET','POST'])
@login_required
def watch(youtube_id):
	movie = Movies.query.filter_by(youtube_id=youtube_id).first()
	x = Views.query.filter_by(movieid=movie.movieid).first()
	x.views = x.views + 1;
	db.session.commit()
	y = WatchHistory.query.filter_by(movieid=movie.movieid,userid=current_user.userid).first()
	z = WatchHistory(userid=current_user.userid,movieid=movie.movieid,timestamp=datetime.now())
	if not y:
		db.session.add(z)
		db.session.commit()

	temp = recommendations([movie.movie_title])
	recommendx = Movies.query.filter(Movies.movie_title.in_(temp)).limit(10).all()

	likes_all = Likes.query.with_entities(Likes.movieid).filter_by(userid=current_user.userid).all()
	likes = [i[0] for i in likes_all]

	mylist_all = MyList.query.with_entities(MyList.movieid).filter_by(userid=current_user.userid).all()
	mylist = [i[0] for i in mylist_all]

	form = SearchForm()
	if form.validate_on_submit():
		return redirect(url_for('search', search_text=form.search_field.data))
	image_file = url_for('static', filename='profile_pics/'+current_user.image_file)
	return render_template('watch.html',title='Watch - '+movie.movie_title, youtube_id=youtube_id,form=form,image_file=image_file, curmovie=movie, recommendx=recommendx, likes=likes, mylist=mylist)


@app.route("/history", methods=['GET','POST'])
@login_required
def history():
	mylist_all = WatchHistory.query.with_entities(WatchHistory.movieid).filter_by(userid=current_user.userid).all()
	mylist = [i[0] for i in mylist_all]
	my_movies_history = Movies.query.filter(Movies.movieid.in_(mylist)).all()

	likes_all = Likes.query.with_entities(Likes.movieid).filter_by(userid=current_user.userid).all()
	likes = [i[0] for i in likes_all]
	mylist_all = MyList.query.with_entities(MyList.movieid).filter_by(userid=current_user.userid).all()
	mylist = [i[0] for i in mylist_all]

	form = SearchForm()
	if form.validate_on_submit():
		return redirect(url_for('search', search_text=form.search_field.data))
	image_file = url_for('static', filename='profile_pics/'+current_user.image_file)
	return render_template('myhistory.html',title='Watch History',form=form,image_file=image_file,history=my_movies_history,likes=likes, mylist=mylist)


@app.route("/register", methods=['GET','POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegistrationForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = Users(username=form.username.data,email=form.email.data,password=hashed_password)
		db.session.add(user)
		db.session.commit()
		flash(f'Account created for {form.username.data}!', 'success')
		return redirect(url_for('register'))
	return render_template('register.html',title='Register',form=form)


@app.route("/login", methods=['GET','POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = LoginForm()
	if form.validate_on_submit():
		user = Users.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password,form.password.data):
			login_user(user,remember=form.remember.data)
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('home'))
		else:
			flash(f'Login Unsuccessful. Please check username and password.', 'danger')
	return render_template('login.html',title='Login', form=form)



@app.route("/account", methods=['GET','POST'])
@login_required
def account():
	form1 = SearchForm()
	if form1.validate_on_submit():
		return redirect(url_for('search', search_text=form1.search_field.data))
	form = UpdateAccountForm()
	if form.validate_on_submit():
		if form.picture.data:
			picture_file = save_picture(form.picture.data)
			current_user.image_file = picture_file
		current_user.username = form.username.data
		current_user.email = form.email.data
		db.session.commit()
		flash('Your Account details has been updated!','success')
		return redirect(url_for('account'))
	elif request.method == 'GET':
		form.username.data = current_user.username
		form.email.data = current_user.email
	image_file = url_for('static', filename='profile_pics/'+current_user.image_file)
	return render_template('account.html', title='Account', image_file = image_file, form=form, form1=form1)


@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for('landing'))



@app.route("/getsearchresults/<stri>")
@login_required
def search_x(stri):
	f = open('app/search.txt', 'r+')
	x = f.readlines()
	f.close()
	x = [k.strip() for k in x]
	res = [i for i in x if i.lower().startswith(stri.lower())]
	if(len(res)>7):
		res=res[:6]
	return jsonify(res),200
