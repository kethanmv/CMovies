import pandas as pd
from rake_nltk import Rake
import operator
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer

pd.set_option('display.max_columns', 100)
df = pd.read_csv('E:/PESU/Sem 6/WT2/Project/app/output.csv', encoding='latin-1')

df = df[['Title','Genre','Director','Actors','Plot']]
df['Actors'] = df['Actors'].map(lambda x: x.split(',')[:3])
df['Genre'] = df['Genre'].map(lambda x: x.lower().split('|'))
df['Director'] = df['Director'].map(lambda x: x.split(' '))

for index, row in df.iterrows():
    row['Actors'] = [x.lower().replace(' ','') for x in row['Actors']]
    row['Director'] = ''.join(row['Director']).lower()

df['Key_words'] = ""

for index, row in df.iterrows():
    plot = row['Plot']
    
    # instantiating Rake, by default is uses english stopwords from NLTK
    # and discard all puntuation characters
    r = Rake()

    # extracting the words by passing the text
    r.extract_keywords_from_text(plot)

    # getting the dictionary with key words and their scores
    key_words_dict_scores = r.get_word_degrees()
    
    # assigning the key words to the new column
    row['Key_words'] = list(key_words_dict_scores.keys())

# dropping the Plot column
df.drop(columns = ['Plot'], inplace = True)

df.set_index('Title', inplace = True)

df['bag_of_words'] = ''
columns = df.columns
for index, row in df.iterrows():
    words = ''
    for col in columns:
        if col != 'Director':
            words = words + ' '.join(row[col])+ ' '
        else:
            words = words + row[col]+ ' '
    row['bag_of_words'] = words
    
df.drop(columns = [col for col in df.columns if col!= 'bag_of_words'], inplace = True)

# instantiating and generating the count matrix
count = CountVectorizer()
count_matrix = count.fit_transform(df['bag_of_words'])

# creating a Series for the movie titles so they are associated to an ordered numerical
# list I will use later to match the indexes
indices = pd.Series(df.index)
indices[:5]

# generating the cosine similarity matrix
cosine_sim = cosine_similarity(count_matrix, count_matrix)

def recommendations(titles, cosine_sim = cosine_sim):
    #print("Entered")
    print(titles)
    recommended_movies = {}
    
    for k in titles:
    # gettin the index of the movie that matches the title
        #print(k)
        idx = indices[indices == k].index[0]

        # creating a Series with the similarity scores in descending order
        score_series = pd.Series(cosine_sim[idx]).sort_values(ascending = False)
        # getting the indexes of the 10 most similar movies
        top_10_indexes = list(score_series.iloc[1:21].index)
        
        # populating the list with the titles of the best 20 matching movies
        x=1
        for i in top_10_indexes:
            recommended_movies[list(df.index)[i]] = score_series.iloc[x:x+1].values[0]
            x=x+1
    sorted_d = dict( sorted(recommended_movies.items(), key=operator.itemgetter(1),reverse=True))
    movies=[]
    for key in sorted_d.keys():
        if key not in titles:
            movies.append(key)
    return movies[:20]


#print(recommendations(['WALL-E']))