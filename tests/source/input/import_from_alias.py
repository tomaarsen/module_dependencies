from nltk.corpus import brown as br
from nltk.tokenize import TextTilingTokenizer as ttt

output = ttt().tokenize(br.raw()[0:10000])
