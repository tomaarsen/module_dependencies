
module_dependencies
===================

The ``module_dependencies`` Python module can be used to determine which sections of some arbitrary Python module are most frequently used,
allowing you to prioritise your development efforts appropriately. For example::

   >>> from module_dependencies import Module
   >>> module = Module("nltk", count=1000)
   >>> module.plot()

.. raw:: html
   :file: images/nltk_usage.html

Beyond simply plotting this data, it can also be returned in machine-readable formats.
See the general `Module`_ documentation for more information.

----

Alternatively, ``module_dependencies`` allows for determining the dependencies or imports of a given Python file, for example::

   from module_dependencies import Source
   from pprint import pprint

   # This creates a Source instance for this file itself
   src = Source.from_file(__file__)

   pprint(src.dependencies())
   pprint(src.imports())

This program outputs::

   ['module_dependencies.Source.from_file', 'pprint.pprint']
   ['module_dependencies', 'pprint']

See the general `Source`_ documentation for more information.

Furthermore, the general `API Reference`_ documentation has more examples and details on ``module_dependencies``.

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: module_dependencies
   :titlesonly:

   Home <self>
   API Reference <api/module_dependencies>
   Module Index <py-modindex>
   GitHub <https://github.com/tomaarsen/module_dependencies>

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Installation

   install

.. _Module: api/module_dependencies.module.html
.. _Source: api/module_dependencies.source.html
.. _API Reference: api/module_dependencies.html
