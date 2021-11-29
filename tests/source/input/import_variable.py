from nltk import corpus, stopwords, tokenize

output = tokenize.TextTilingTokenizer().tokenize(corpus.brown.raw()[0:10000])

output = [token for token in output if token not in stopwords]
