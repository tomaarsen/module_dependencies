from nltk.corpus import brown
from nltk.tokenize import TextTilingTokenizer

ttt = TextTilingTokenizer()
data = brown.raw()[0:10000]
output = ttt.tokenize(data)
