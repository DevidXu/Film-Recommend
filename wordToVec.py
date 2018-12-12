from gensim.models.keyedvectors import KeyedVectors
from gensim.models import word2vec
from nltk.corpus import wordnet
from constants import *
from sklearn.neural_network import MLPClassifier
import numpy as np
import random
import csv

class FilmReviewRecommend():
    dimension = 0
    wv_model = None
    mlp = None
    m = {}
    keys = []
    X_train, X_test, label_train, label_test = [], [], [], []
    exceptions = 0

    def __init__(self, useWiki):
        if useWiki:
            print("Model is being loaded...")
            self.wv_model = KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)
            print("Model has been loaded completely!")

        self.output_dim = dimension
        self.input_dim = self.wv_model.vector_size
        print("Vector dimension: %d" % self.input_dim)


    def dataToVector(self, save):
        temp = open('review_imdb.csv','r')
        file = csv.reader(temp)
        for line in file:
            if random.random()<0.7:
                if not self.m.__contains__(line[0]): self.m[line[0]] = []
                for word in line[1:]:
                    try:
                        self.m[line[0]].append(self.wv_model[word])
                    except:
                        self.exceptions += 1
            else:
                test_data = []
                for word in line[1:]:
                    try:
                        test_data.append(self.wv_model[word])
                    except:
                        self.exceptions += 1
                if len(test_data)>0:
                    self.X_test.append(test_data)
                    self.label_test.append(line[0])
        self.X_test, self.label_test = np.array(self.X_test), np.array(self.label_test)

        print('%d exceptions happened in the word-to-vector transformation!' % self.exceptions)
        temp.close()

        if save:
            data = open('word_vectors.txt','w')
            for keys in self.m:
                for ele in self.m[keys]:
                    for num in ele:
                        data.write(str(num)+' ')
                data.write('\n')
            data.close()
        return self.m


    def trainClassifer(self):
        temp_keys = self.m.keys()
        for ele in temp_keys: self.keys.append(ele)
        for key in self.m:
            for ele in self.m[key]:
                self.X_train.append(ele)
                self.label_train.append(self.keys.index(key))

        self.X_train, self.label_train = np.array(self.X_train), np.array(self.label_train)
        self.mlp = MLPClassifier(solver='sgd', alpha=1e-5, max_iter=100000, hidden_layer_sizes=(100), random_state=0)  # adam 50000 100, 50, 10
        self.mlp.fit(self.X_train, self.label_train)


    def testTrainData(self):
        print('\nThe test result for original reviews:')
        print(self.keys)
        random_key, predicts = [], []
        accuracy = 0.0
        for i in range(len(self.keys)):
            random_key.append(random.choice(self.keys))
            vectors = self.m[random_key[i]]
            predicts = self.mlp.predict(vectors)
            proba = np.zeros(dimension)
            for k in predicts:
                proba[k]+=1
            temp = np.argmax(proba)
            print("Test: %s;   Result: %s" %(random_key[i], self.keys[temp]))
            if random_key[i]==self.keys[temp]: accuracy+=1.0
        print("Accuracy: %f" % (accuracy/(0.01+len(self.keys))))


    def testNewReview(self):
        print('\nThe test result for new reviews:')
        print(self.keys)
        random_key, predicts = [], []
        accuracy, whole = 0.0, 0.0
        for i in range(len(self.label_test)):
            predicts = self.mlp.predict(self.X_test[i])
            proba = np.zeros(dimension)
            for k in predicts:
                proba[k]+=1
            temp = np.argmax(proba)
            # print("Origin: %s;   Result: %s" %(self.label_test[i], self.keys[temp]))
            if self.label_test[i]==self.keys[temp]: accuracy+=1.0
        print("Accuracy: %f" % (accuracy/(0.01+len(self.label_test))))


    def testNewFilm(self, films):
        print('\nThe test result for films not in the training set:')
        for key in films:
            film_name, film_review = key, films[key]
            review_vector = []
            for token in film_review.split():
                if (not not wordnet.synsets(token)) and not token.isdigit():
                    try:
                        review_vector.append(self.wv_model[token])
                    except:
                        continue
            predicts = self.mlp.predict(review_vector)
            proba = np.zeros(dimension)
            for k in predicts:
                proba[k] += 1
            temp = np.argmax(proba)
            print("The film predicted for %s is %s" %  (film_name, self.keys[temp]))
            print(proba)



if __name__=='__main__':
    fr = FilmReviewRecommend(True)
    fr.dataToVector(True)
    films = {}
    fr.trainClassifer()
    films["Jaws"] = "I think it is the best movie introducing attacks from animals. Sometimes they are so fierce that they attack people. The special effects built for shakr is also amazing. The bloody scene is so realistic that I get scared by the shark actually. And I have to say that it is not a good idea to swim in somewhere you know nothing about --- There might be a shark there!"
    films["Zero Dark Thirty"] = "Zero Dark Thirty is a perfect film a movie that reflects America's patriotism and faith in a woman wanting to capture the most wanted man in the world dotod is a movie full of action drama and a magnificent Final voltage Jessica Chastain this spectacular"
    films["Wall-E"] = "This movie brings a whole new dimension to Pixar movies; it gives an innovative and creative insight into what the future would be like. It gives a whole new total perspective of what is the meaning of life. Cute characters, wonderful songs and lots of funny moments for the kids to enjoy. I love how this movie is also raising awareness of global warming at the same time. Simply stunning and recommended at all ages. Always will be a family classic."
    films["Taxi Driver"] = "Mind blowing and brutally brilliant work.This is essentially the film that singlehandedly got me into films.After I saw this hard hitting, chillingly atmospheric and gripping masterpiece I was forced to re asses what a motion picture really is. I had never seen anything that demanded and rewarded my attention in such a powerful and serious manner.Scorsese's direction is pure genius as is De Niro's psychotic and disturbing aura.The creepy score is immense in its feel and the evolotion of thought throughout is unrivalled. Darkly compelling and definitive stuff. This is without doubt a landmark in film making, underlined by one of THE partnerships in cinema history 'De Niro and Scorsese'. As effectively strong as a picture can be."
    films["12-years-a-slave"] = " I'm glad Steve McQueen has the mentality that he has, as seen in Hunger and Shame. He, like Lars Von Trier, aren't afraid and won't hold back. This pattern is seen here again, which leaves an everlasting memory of the harsh reality faced by Solomon Northup. Great performances all around. Just amazing filmmaking, the whole team, all around. Sean Bobbitt with the great eye as well. The long takes, especially with Ejiofor hanging by the noose, wow. Nice editing."
    films["The Servant"] = "A dissolute young gentleman begins to fall under the spell of his butler in this fascinating look at class and relationships in early 1960s London. It was based on a play by the great Harold Pinter, and he specialized in these murky tales of power relationships between men. Fox is perfect as the unfocused upper class fellow, and Bogarde is fine but seems a little miscast. Craig and Miles are solid as a young lady and a cheerful tramp respectively. Director Losey and cinematographer Slocombe do a great job of making a pretty basic set (a London townhouse) visually stimulating"
    films["Moonlight"] = "I feel that this movie took so great reviews just because of the homosexeual mixed with the race theme. It was a good standing movie, the performances were strong , i loved the photography and the sound i must say but i just didnt feel it. Any of it, any of the struggle of the heroes.I just watched the trailer again i liked it more that the movie itself, i excected so much more. The scene at the beach ,camera half in the water ok just marvelous! And also i am sorry but i cant see why Mahershala Ali is nominated for an oscar, Naomie Harris did sooo much better bravo!"
    fr.testTrainData()
    fr.testNewReview()
    fr.testNewFilm(films)