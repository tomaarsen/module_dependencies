import nltk.corpus
import nltk.tokenize

output = nltk.tokenize.TextTilingTokenizer().tokenize(nltk.corpus.brown.raw()[0:10000])
