"""
Expected usage of module_dependencies' ``Module``::

    >>> from module_dependencies import Module
    >>> module = Module("nltk", count=1000)
    >>> module.usage()[:15]
    [2022-01-03 15:18:30,965] [module_dependencies.module.session] [INFO    ] - Fetching Python source code containing imports of `nltk`...
    [2022-01-03 15:18:33,796] [module_dependencies.module.session] [INFO    ] - Fetched Python source code containing imports of `nltk` (status code 200)
    [2022-01-03 15:18:33,797] [module_dependencies.module.session] [INFO    ] - Parsing 6,179,925 bytes of Python source code as JSON...
    [2022-01-03 15:18:33,847] [module_dependencies.module.session] [INFO    ] - Parsed 6,179,925 bytes of Python source code as JSON...
    [2022-01-03 15:18:33,850] [module_dependencies.module.session] [INFO    ] - Extracting dependencies of 731 files of Python source code...
    Parsing Files: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 731/731 [00:02<00:00, 254.17files/s]
    [2022-01-03 15:18:36,780] [module_dependencies.module.session] [INFO    ] - Extracted dependencies of 731 files of Python source code.
    [2022-01-03 15:18:36,780] [module_dependencies.module.session] [INFO    ] - Fetching Jupyter Notebook source code containing imports of `nltk`...
    [2022-01-03 15:18:39,878] [module_dependencies.module.session] [INFO    ] - Fetched Jupyter Notebook source code containing imports of `nltk` (status code 200)
    [2022-01-03 15:18:39,879] [module_dependencies.module.session] [INFO    ] - Parsing 25,071,542 bytes of Jupyter Notebook source code as JSON...
    [2022-01-03 15:18:40,053] [module_dependencies.module.session] [INFO    ] - Parsed 25,071,542 bytes of Jupyter Notebook source code as JSON...
    [2022-01-03 15:18:40,055] [module_dependencies.module.session] [INFO    ] - Extracting dependencies of 499 files of Jupyter Notebook source code...
    Parsing Files: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 499/499 [00:03<00:00, 143.93files/s]
    [2022-01-03 15:18:43,523] [module_dependencies.module.session] [INFO    ] - Extracted dependencies of 499 files of Jupyter Notebook source code.
    [('nltk.tokenize.word_tokenize', 343),
     ('nltk.download', 315),
     ('nltk.corpus.stopwords.words', 260),
     ('nltk.tokenize.sent_tokenize', 139),
     ('nltk.stem.porter.PorterStemmer', 106),
     ('nltk.stem.wordnet.WordNetLemmatizer', 105),
     ('nltk.tag.pos_tag', 67),
     ('nltk.stem.snowball.SnowballStemmer', 54),
     ('nltk.tokenize.RegexpTokenizer', 46),
     ('nltk.probability.FreqDist', 37),
     ('nltk.corpus.wordnet.synsets', 36),
     ('nltk.data.path.append', 36),
     ('nltk.data.load', 34),
     ('nltk.tokenize.TweetTokenizer', 33),
     ('nltk.translate.bleu_score.sentence_bleu', 32)]

Now we can see which objects from the NLTK module are most frequently used,
allowing us to prioritise our development efforts more effectively.
(Note: The output formatting was edited slightly)

We can also inspect a nested usage dictionary, rather than simply a list of tuples::

    >>> module.nested_usage()
    {
        "nltk": {
            "occurrences": 2465,
            "tokenize": {
                "occurrences": 671,
                "word_tokenize": {
                    "occurrences": 343
                },
                "sent_tokenize": {
                    "occurrences": 139
                },
                "RegexpTokenizer": {
                    "occurrences": 46
                },
                "TweetTokenizer": {
                    "occurrences": 33
                },
                "regexp": {
                    "occurrences": 23,
                    "WordPunctTokenizer": {
                        "occurrences": 23
                    }
                },
                "wordpunct_tokenize": {
                    "occurrences": 20
                },
                "treebank": {
                    "occurrences": 26,
                    "TreebankWordTokenizer": {
                        "occurrences": 16
                    },
                    "TreebankWordDetokenizer": {
                        "occurrences": 10
                    }
                },
                ...
            },
            ...
        }
    }

(Note: The output formatting was edited and truncated)

Alternatively, we can simply plot this data in a very useful interactive Sunburst chart, like so::

    >>> module.plot()

.. raw:: html
   :file: ../../docs/images/nltk_usage.html
"""

from .module import Module
