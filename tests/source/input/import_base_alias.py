import nltk as nlp

output = nlp.TextTilingTokenizer().tokenize(nlp.brown.raw()[0:10000])
