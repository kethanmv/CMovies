from bs4 import BeautifulSoup
import requests
import re
import os
import csv
import urllib
import shutil
import sqlite3

def download_poster(link):
	url = 'http://www.imdb.com' + link
	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'lxml')
	img_url = soup.find('div',attrs={'class':'poster'}).find('img')
	img_url = img_url.attrs.get('src')
	base_dir = os.getcwd()
	dir_name = "static/movie_posters"
	dir_path = os.path.join(base_dir, dir_name)
	if not os.path.exists(dir_path):
		os.mkdir(dir_path)
	name = str(link.split('/')[2])
	with urllib.request.urlopen(img_url) as response, open('static/movie_posters/'+name+'.jpg', 'wb') as out_file:
		shutil.copyfileobj(response, out_file)

def get_trailer_link(name):
	search_query = name.replace(' ','+')
	search_query = search_query + "+official+trailer"
	url = 'https://www.youtube.com/results?search_query='+search_query
	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'lxml')
	first_vid = soup.select('div.yt-lockup-content')
	if first_vid:
		link = first_vid[0].find('a').attrs.get('href')
	else:
		return "Not Available"
	return link[link.find('=')+1:]

def get_language(link):
	url = 'https://www.imdb.com' + link
	#print(url)
	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'lxml')
	txt_block= soup.find('div',attrs={'class':'article','id':'titleDetails'}).find_all('div',attrs={'class':'txt-block'})
	for i in txt_block:
		l = i.find('h4').get_text().strip()
		if("Language" in l):
			k = i.find_all('a')
			language = [j.get_text() for j in k]
			languages = ', '.join(language)
			break
	return languages

def add_to_db():
	firstline = True
	with open('output.csv', 'r') as file:
		reader = csv.reader(file)
		for i in reader:
			if firstline:
				firstline = False
				continue
			print(i[1])
			with sqlite3.connect("cmovies.db") as con:
				cur = con.cursor()
				sql = "insert into movies(movieid,movie_title,desc,release_year,genre,movie_length,language,director,act_cast,movie_link,movie_pic,youtube_id) VALUES ('"+i[0]+"','"+i[1]+"','"+i[2]+"','"+i[3]+"','"+i[4]+"','"+i[5]+"','"+i[6]+"','"+i[7]+"','"+i[8]+"','"+i[9]+"','"+i[10]+"','"+i[11]+"')"
				cur.execute(sql)
				sql = "insert into views(movieid,views) VALUES ('"+i[0]+"',0)"
				cur.execute(sql)
				con.commit()
		
def scrap_imdb():
	url = 'http://www.imdb.com/chart/top'
	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'lxml')

	movies = soup.select('td.titleColumn')
	links = [a.attrs.get('href') for a in soup.select('td.titleColumn a')]
	crew = [a.attrs.get('title') for a in soup.select('td.titleColumn a')]

	imdb = []
	with open('output.csv','a', newline='') as fd:
		writer = csv.DictWriter(fd, fieldnames = ["movieid", "Title", "Plot","Year","Genre","Runtime","Language","Director","Actors","IMDB","Pic","Youtube"])
		writer.writeheader()

	for index in range(0, len(links)):
		movie_string = movies[index].get_text()
		movie = (' '.join(movie_string.split()).replace('.', ''))
		movie_title = movie[len(str(index))+1:-7]
		year = re.search('\((.*?)\)', movie_string).group(1)
		year = int(year)
		if (year<2020):
			url = 'https://www.imdb.com' + links[index]
			response = requests.get(url)
			soup = BeautifulSoup(response.text, 'lxml')
			desc = soup.select('div.summary_text')[0].get_text().strip()
			languages = get_language(links[index])
			movieid = str(links[index].split('/')[2])
			director = crew[index][:crew[index].find('(')-1]
			act_crew = crew[index][crew[index].find(')')+3:]
			length = soup.find('div',attrs={'class':'subtext'}).find('time').get_text().strip()
			x = soup.find('div',attrs={'class':'subtext'}).find_all('a')
			x = list(x)
			x = x[:len(x)-1]
			genres = [i.get_text() for i in x]
			trailer_link = get_trailer_link(movie_title)
			download_poster(links[index])
			poster = movieid + ".jpg"
			if trailer_link == "Not Available":
				continue
			data = [str(movieid.strip()),movie_title.strip().replace("'","''"),desc.replace("'", "''").replace("\\",""),str(year),' | '.join(genres),str(length),languages.strip(),director.strip().replace("'", "''"),act_crew.strip().replace("'", "''"),links[index],poster.strip(),trailer_link.strip()]
			with open('output.csv','a', newline='') as fd:
				writer = csv.writer(fd)
				writer.writerow(data)
			'''data = {"movieid": movieid.strip(),
					"movie_title": movie_title.strip(),
					"desc": desc,
					"year": year,
					"genres": genres,
					"movie_length": length,
					"language": languages.strip(),
					"director": director.strip(),
					"star_cast": act_crew.strip(),
					"movie_link": links[index],
					"poster": poster.strip(),
					"youtube_id": trailer_link.strip()
					}
			imdb.append(data)'''


#scrap_imdb()

add_to_db()
