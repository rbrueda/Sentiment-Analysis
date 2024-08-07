import pandas as pd
from nltk.corpus import stopwords
import re
import nltk
import numpy

# data preprocessing -- sklearn to omit wordless that possess no value
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

# import word-2-vec model
from gensim.models import Word2Vec

from sklearn.decomposition import PCA

#this example goes through KMeans clustering

def build_collection(data):
    collection = [] #collection of words
    counter = 0 
    
    for index, sentence in data.items():
        if pd.notna(sentence):
            print(sentence)
            counter += 1
            word_list = sentence.split(", ")  #split the list of words by separate names
            collection.append(word_list)

    print(collection)

    return collection

#attempt 1: to use centroid cluster


#use a sample dataset here with the data for one of the months

# here we will use the reddit data from April 2023 
fileSample = "/home/rocio/Documents/research/Data-To-Use/2024-04/combined_2024-04.csv"

df = pd.read_csv(fileSample)


#example - Tf-idf term weighting
#omit meaningless words -- "the", "a", "is"


#to perform regex operations, we will change comments type to unicode
comments = df["comments"].values.astype("U") #U = unicode

#* stop words: words that occur in high frequency but carry little to no meaning
stop = set(stopwords.words("english"))


#create a collection of words from album genres
collection_of_words = build_collection(df['comments'])

#train a word2vec model
#will start with a vector size of 100
model = Word2Vec(collection_of_words, vector_size=100, min_count=1)

#create a keyed vector instance
keyed_vectors = model.wv

#vectorize the list of words
vectors = keyed_vectors[model.wv.index_to_key]

#creates an instance of a 2-d PCA
pca = PCA(n_components=2)

#fit the vectors in the PCA object created -- used for dimensionality reduction
PCA_result = pca.fit_transform(vectors)

#* k = 5 or 6
kmeans = KMeans(n_clusters=5)

#fit K-means model with k=5
kmeans.fit(PCA_result)

#algorithm used for parititioning a dataset into a pre-defined number of clusters
clusters = kmeans.predict(PCA_result)

#dataframe for PCA results and clusters
PCA_df = pd.DataFrame(PCA_result, columns=['x_values', 'y_values'])
PCA_df['word'] = model.wv.index_to_key
PCA_df['cluster'] = clusters

#look at the result of PCA dataframe
print(PCA_df.head())

print(PCA_df['cluster'])

#open all the possible files

#iterate through each line of the cluster and print to a specific csv file
for index, entry in PCA_df.iterrows():

    #ex cluster 1 -> write to clusterRes1.csv
    if int(entry['cluster']) >= 1 and int(entry['cluster']) <= 5:
        f = open('samples/clusterRes' + str(entry['cluster']) + '.csv', 'w')
        f.write(entry['word'])
        f.close()

    #does not belong any of the clusters
    else:
        f = open('samples/clusterLeftovers.csv', 'w')
        f.write(entry['word'])
        f.close()