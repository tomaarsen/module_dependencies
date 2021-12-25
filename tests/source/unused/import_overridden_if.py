if input() == "2":
    from nltk.corpus import words

    print(len(words.words()))
else:
    words = ["a", "b", "c"]
    words.count()
