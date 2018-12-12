import requests
from bs4 import BeautifulSoup
import nltk
import re
import csv
import random
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from constants import *
import time

movie_url = {}

movie_base_url = "http://www.metacritic.com"
movie_user_suffix = "/user-reviews"
movie_preference_url = "http://www.metacritic.com/browse/movies/score/metascore/all/filtered"

movie_url["WILD HOGS"] = "http://www.metacritic.com/movie/wild-hogs/user-reviews"

headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
    }

num_films = 10




def getMovieLinks(baseurl):
    links = []
    req = requests.get(baseurl, headers = headers)
    req.encoding = 'utf-8'
    soup = BeautifulSoup(req.text, 'html.parser')
    req.close()
    results = soup.find_all(href=re.compile("movie"))
    for result in results:
        if len(result['href'])>7 and result['href'][:7]=='/movie/' and result['href'][-7:]!='reviews':
            if result['href'] not in links: links.append(result['href'])
    print("%d movies are scratched now." % len(links))
    return links[:200]


def getMovieReview(url):
    reviews = []
    print("Film review of %s is being downloaded!" % url[7:])
    url = movie_base_url+url+movie_user_suffix
    req = requests.get(url, headers = headers)
    req.encoding = 'utf-8'
    soup = BeautifulSoup(req.text, 'html.parser')
    req.close()
    results = soup.find_all('div', class_='review_body')
    for result in results:
        reviews.append(result.text[1:-1])
    return reviews



if __name__ == "__main__":
    requests.adapters.DEFAULT_RETRIES = 5
    s = requests.session()
    s.keep_alive = False
    movie_links = getMovieLinks(movie_preference_url)

    out = open('reviews.csv','w', newline='', encoding='utf-8')
    out_words = open('reviews_word.csv','w', newline='', encoding='utf-8')
    csv_write = csv.writer(out,dialect='excel')
    csv_word_write = csv.writer(out_words, dialect='excel')

    sr = stopwords.words('english')

    #chosen_movie_links = ['jaws','la-la-land','wall-e','gravity','die-hard','toy-story-3','moonlight','inception']
    #chosen_movie_links = ['/movie/'+ele for ele in chosen_movie_links]

    count = 0
    for url in movie_links:
        time.sleep(2)
        reviews = getMovieReview(url)
        if count==dimension: break
        if (len(reviews)<review_num_min): continue
        count += 1
        for review in reviews[:min([review_num_max, len(reviews)])]:
            csv_write.writerow([url[7:], review])
            tokens = review.split()
            words = [url[7:]]
            for token in tokens:
                if token not in sr and (not not wordnet.synsets(token)) and not token.isdigit() and token!='I':
                    words.append(token)
            csv_word_write.writerow(words)
        print("%d useful film review sets has been collected" % count)
    out.close()
    out_words.close()
