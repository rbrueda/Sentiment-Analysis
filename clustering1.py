#this example goes through KMeans clustering

#attempt 1: to use centroid cluster

import pandas as pd

#use a sample dataset here with the data for one of the months

# here we will use the reddit data from April 2023 
fileSample = "/home/rocio/Documents/research/Data-To-Use/2024-04/combined_2024-04.csv"

df = pd.read_csv(fileSample)


#example - Tf-idf term weighting
#omit meaningless words -- "the", "a", "is"

print(df.info())

# data preprocessing -- sklearn to omit wordless that possess no value
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

#to perform regex operations, we will change comments type to unicode
comments = df["comments"].values.astype("U") #U = unicode

#change our string from english to unicode
#use vectorizer function to remove stop words
vectorizer = TfidfVectorizer(stop_words='english')
#* stop words: words that occur in high frequency but carry little to no meaning


#extract meaningful information for the comments
features = vectorizer.fit_transform(comments)

#check the number of samples
k = features.shape[0]

#todo: do something else here

#topic modeling and embedding
#convert it into a vector instead of shape

model = KMeans(n_clusters=k, init='k-means++', max_iter=100, n_init=1 )
model.fit(features) #infromation that we transformed from text to something more meaningful

print(model)

#create a new column called cluster
df["cluster"] = model.labels_

print(df.head())


#output the result here in an external text file

clusters = df.groupby('cluster')
for cluster in clusters.groups:
    f = open('samples/results2_cluster' + str(cluster) + '.csv', 'w')
    data = clusters.get_group(cluster)[['title','comments']]
    f.write(data.to_csv(index_label='id')) #set index to id
    f.close()


print("cluster centroids: \n")
order_centroids = model.cluster_centers_.argsort()[:, ::-1]

#gets the featured terms for each cluster
terms = vectorizer.get_feature_names_out()

for i in range(k): #iterate through through each division
    print(f"cluster {i}")
    for j in order_centroids[i, :3]: #print out 3 festure terms of each cluster
        print(f"{terms[j]}")
    
    print('---------------------------')