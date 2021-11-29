from nltk.corpus import brown
from nltk.tokenize import TextTilingTokenizer

output = TextTilingTokenizer().tokenize(brown.raw()[0:10000])
