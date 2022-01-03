# Module Dependencies
## Brief overview
The ``module_dependencies`` Python module allows you to gather the dependencies of specific modules in source code. It has been split into two main sections: ``Module`` and ``Source``.

The former, ``Module``, supports functionality for mapping a module name to the usage of that module within open source repositories.
This is very useful when we are interested in determining which sections of a Python module is most frequently used. For example:

```python
from module_dependencies import Module
from pprint import pprint

# Attempt to find 1000 imports of the "nltk" module
# in both Python files and Jupyter Notebooks each
module = Module("nltk", count="1000")
print(module.usage())
module.plot()
```

This program outputs:
```python
[2022-01-03 14:14:39,127] [module_dependencies.module.session] [INFO    ] - Fetching Python source code containing imports of `nltk`...
[2022-01-03 14:14:42,824] [module_dependencies.module.session] [INFO    ] - Fetched Python source code containing imports of `nltk` (status code 200)
[2022-01-03 14:14:42,825] [module_dependencies.module.session] [INFO    ] - Parsing 6,830,859 bytes of Python source code as JSON...
[2022-01-03 14:14:42,865] [module_dependencies.module.session] [INFO    ] - Parsed 6,830,859 bytes of Python source code as JSON...
[2022-01-03 14:14:42,866] [module_dependencies.module.session] [INFO    ] - Extracting dependencies of 725 files of Python source code...
Parsing Files: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 725/725 [00:02<00:00, 258.48files/s]
[2022-01-03 14:14:45,702] [module_dependencies.module.session] [INFO    ] - Extracted dependencies of 725 files of Python source code.
[2022-01-03 14:14:45,703] [module_dependencies.module.session] [INFO    ] - Fetching Jupyter Notebook source code containing imports of `nltk`...
[2022-01-03 14:14:48,726] [module_dependencies.module.session] [INFO    ] - Fetched Jupyter Notebook source code containing imports of `nltk` (status code 200)
[2022-01-03 14:14:48,726] [module_dependencies.module.session] [INFO    ] - Parsing 25,713,281 bytes of Jupyter Notebook source code as JSON...
[2022-01-03 14:14:48,886] [module_dependencies.module.session] [INFO    ] - Parsed 25,713,281 bytes of Jupyter Notebook source code as JSON...
[2022-01-03 14:14:48,888] [module_dependencies.module.session] [INFO    ] - Extracting dependencies of 495 files of Jupyter Notebook source code...
Parsing Files: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 495/495 [00:02<00:00, 167.09files/s]
[2022-01-03 14:14:51,851] [module_dependencies.module.session] [INFO    ] - Extracted dependencies of 495 files of Jupyter Notebook source code.
[('nltk.tokenize.word_tokenize', 327),
('nltk.download', 298),
('nltk.corpus.stopwords.words', 257),
('nltk.tokenize.sent_tokenize', 126),
('nltk.stem.porter.PorterStemmer', 115),
('nltk.stem.wordnet.WordNetLemmatizer', 99),
('nltk.tag.pos_tag', 75),
('nltk.stem.snowball.SnowballStemmer', 48),
('nltk.data.path.append', 42),
('nltk.probability.FreqDist', 42),
('nltk.tokenize.RegexpTokenizer', 42),
('nltk.tokenize.TweetTokenizer', 35),
('nltk.corpus.wordnet.synsets', 33),
('nltk.data.load', 32),
('nltk.translate.bleu_score.corpus_bleu', 29)]
```

And then opens an interactive version of the following plot:
![usage](https://user-images.githubusercontent.com/37621491/147952784-57691744-b0e9-4ef1-a970-fe528bf1f029.png)

(Note that the true plot is interactive, but this copy for GitHub is just a png)

With the methods provided in the ``Module`` class, it becomes elementary to see which sections of code are frequently used, allowing you to prioritise these sections over rarely used sections.

---

``module_dependencies`` also provides ``Source``, wich implements functionality for mapping Python source code to the dependencies and imports within that file. For example:

```python
from module_dependencies import Source
from pprint import pprint

# This creates a Source instance for this file itself
src = Source.from_file(__file__)

pprint(src.dependencies())
pprint(src.imports())
```

This program outputs:
```python
['module_dependencies.Source.from_file', 'pprint.pprint']
['module_dependencies', 'pprint']
```

---

## Documentation
More detailed documentation, including examples and an API Reference, can be found in the [online documentation]().

## Installation
``module_dependencies`` can be installed directly via pip. It is recommended to set up a virtualenvironment before installation, although this is not strictly a requirement.

The command to install ``module_dependencies`` is:
```
pip install module_dependencies
```

Note that ``module_dependencies`` requires Python 3.8 onwards.
