import nltk

ttt = nltk.TextTilingTokenizer()
data = nltk.brown.raw()[0:10000]
output = ttt.tokenize(data)
