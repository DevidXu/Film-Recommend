#coding=utf-8
from gensim.models.keyedvectors import KeyedVectors
from gensim.models import word2vec
from nltk.corpus import wordnet, stopwords
from sklearn.neural_network import MLPClassifier
import numpy as np
import random, csv, re, nltk, time, requests
from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import json
from googletrans import Translator

movie_url = {}

movie_base_url = "http://www.metacritic.com"
movie_user_suffix = "/user-reviews"
movie_preference_url = "http://www.metacritic.com/browse/movies/score/metascore/all/filtered"

movie_url["WILD HOGS"] = "http://www.metacritic.com/movie/wild-hogs/user-reviews"

headers = {
    'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
}

pages = 10
review_num_min = 20
review_num_max = 100

def getMovieLinks(baseurl):
    links = []
    req = requests.get(baseurl, headers=headers)
    req.encoding = 'utf-8'
    soup = BeautifulSoup(req.text, 'html.parser')
    req.close()
    results = soup.find_all(href=re.compile("movie"))
    for result in results:
        if len(result['href']) > 7 and result['href'][:7] == '/movie/' and result['href'][-7:] != 'reviews':
            if result['href'] not in links: links.append(result['href'])
    print("%d movies are scratched now." % len(links))
    return links


def getMovieReview(url):
    reviews = []
    print("Film review of %s has been downloaded!" % url[7:])
    url = movie_base_url + url + movie_user_suffix
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
    }
    req = requests.get(url, headers=headers)
    req.encoding = 'utf-8'
    soup = BeautifulSoup(req.text, 'html.parser')
    req.close()
    results = soup.find_all('div', class_='review_body')
    for result in results:
        reviews.append(result.text[1:-1])
    return reviews


trans = Translator(service_urls=['translate.google.cn'])
def translate(wd):
    for c in wd:
        if c < u'\u4e00' or c > u'\u9fa5':
            source = 'en'
            destination = 'zh-cn'
        elif c == wd[-1]:
            source = 'zh-cn'
            destination = 'en'

    result = trans.translate(wd, src=source, dest=destination)
    return result.text
    '''
    userAgent = "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"

    header = {
        "Host": "fanyi.baidu.com",
        "Origin": "http://fanyi.baidu.com",
        "User-Agent": userAgent
    }
    postUrl = "http://fanyi.baidu.com/basetrans"
    for c in wd:
        if c < u'\u4e00' or c > u'\u9fa5':
            mdata = {"from": "en","to": "zh","query": wd}
            wd = wd.upper()
            break
        elif c == wd[-1]:
            mdata = {"from": "zh","to": "en","query": wd}
    response = requests.post(postUrl, data=mdata, headers=header)
    result = response.text
    result = json.loads(result)
    try:
        return result["dict"]["netdata"]["types"][0]["trans"]
    except:
        return result["trans"][0]['dst']
    return ""
    '''


class FilmReviewRecommend():
    dimension = 0
    wv_model = None
    m = {}
    sr = stopwords.words('english')
    X_train, X_test, label_train, label_test = [], [], [], []
    exceptions = 0

    def __init__(self):
        print("Model is being loaded...")
        self.wv_model = KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)
        print("Model has been loaded completely!")

        self.input_dim = self.wv_model.vector_size
        print("Vector dimension: %d" % self.input_dim)


    def getReviewVector(self, reviews, name):
        film_name, film_vector = name, []
        for review in reviews[:min([review_num_max, len(reviews)])]:
            tokens = review.split()
            temp_vector = []
            for token in tokens:
                if token not in self.sr and (not not wordnet.synsets(token)) and not token.isdigit() and token != 'I':
                    try:
                        temp_vector.append(self.wv_model[token])
                    except:
                        continue
            l = len(temp_vector)
            if l == 0: continue
            temp_vector = np.sum(temp_vector, axis=0)
            temp_vector *= 1.0 / l
            film_vector.append(temp_vector)
        l = len(film_vector)
        if l == 0: return []
        film_vector = np.sum(np.array(film_vector), axis=0) * 1.0 / (l + 1e-5)
        film_vector = film_vector.tolist()
        film_vector.insert(0, film_name)
        return film_vector


    def prepare_data(self):
        movie_links = getMovieLinks(movie_preference_url)
        for i in range(pages-1):
            movie_links += getMovieLinks(movie_preference_url+'?page='+str(i+1))
        out = open('film_vector.csv', 'w', newline='', encoding='utf-8')
        csv_write = csv.writer(out, dialect='excel')
        for url in movie_links:
            time.sleep(2)
            reviews = getMovieReview(url)
            if (len(reviews) < review_num_min): continue
            film_vector = self.getReviewVector(reviews, url[7:])
            if len(film_vector)==0: continue
            csv_write.writerow(film_vector)
        out.close()


    def readFilmVectors(self):
        temp_file = open('film_vector.csv','r')
        file = csv.reader(temp_file)
        for line in file:
            vector = line[1:]
            vector = [float(ele) for ele in vector]
            self.m[line[0]]=np.array(vector)


    def find_similar(self, film_name):
        for c in film_name:
            if c < u'\u4e00' or c > u'\u9fa5':
                film_name = film_name.lower(); break
            elif c == film_name[-1]:
                try: film_name = translate(film_name).lower()
                except: print("Cannot translate the name"); return;
        film_name = film_name.replace(' ','-')
        reviews = getMovieReview('/movie/'+film_name)
        if len(reviews)==0:
            print("No review on this film"); return;
        film_vector = self.getReviewVector(reviews, film_name)[1:]
        film_vector = np.array(film_vector)
        dis_map = {}
        for key in self.m:
            dis_map[key]=np.dot(self.m[key], film_vector)/(1e-7+(sum(self.m[key]**2)**0.5)*(sum(film_vector**2)**0.5))
        l = sorted(dis_map.items(), key=lambda x: x[1], reverse=True)
        for ele in l[:5]:
            #print(ele[0])
            print(ele[0]+ ' --- ' + translate(ele[0].replace('-',' ')))
        return



if __name__=="__main__":
    fr = FilmReviewRecommend()
    # fr.prepare_data()
    fr.readFilmVectors()
    while True:
        a = input("Input a film name:")
        fr.find_similar(a)






