import nltk.corpus
import nltk.tokenize

ttt = nltk.tokenize.TextTilingTokenizer()
data = nltk.corpus.brown.raw()[0:10000]
output = ttt.tokenize(data)
