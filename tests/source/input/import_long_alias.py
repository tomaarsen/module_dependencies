import nltk.corpus as crps
import nltk.tokenize as tknz

output = tknz.TextTilingTokenizer().tokenize(crps.brown.raw()[0:10000])
