import nltk

sentence_tokenizer = 12


class MyObject:
    pass


obj = MyObject()

if sentence_tokenizer:
    sentence_tokenizer = sentence_tokenizer
else:
    obj.sentence_tokenizer = nltk.tokenize.sent_tokenize

obj.sentence_tokenizer()
