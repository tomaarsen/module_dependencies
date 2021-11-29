from nltk import corpus, tokenize

output = tokenize.TextTilingTokenizer().tokenize(corpus.brown.raw()[0:10000])
