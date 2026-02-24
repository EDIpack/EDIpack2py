.. _edipack2py_install:

EDIpack2py Installation
========================


Anaconda
------------

We provide Linux and MacOS packages for the `Anaconda <https://www.anaconda.com/>`_ distribution. Packages are available for Python version 3.10 and later. The `EDIpack` package contains the `edipack2py` python module as well as the `EDIpack <https://www.github.com/EDIpack/EDIpack/>`_ and `SciFortran <https://www.github.com/scifortran/scifortran/>`_ libraries.
Once a command-line tool such as `conda <https://www.anaconda.com/>`_ or `mamba <https://mamba.readthedocs.io/en/latest/>`_ is installed, an environment using one of the available python version can be created, and then the EDIpack package can be installed:

.. code-block:: shell

   conda create -n edipack
   conda activate edipack
   conda install -c conda-forge -c edipack edipack


the `edipack2py` python module can then be directly imported.


Install with pip
---------------------

See the package page on `pypi <https://pypi.org/project/edipack2py/>`_ .


Install from source
---------------------

The python module `edipack2py` requires the

* `SciFortran`_

* `EDIpack`_

libraries to be installed beforehand, please see related documentation
to install such Fortran libraries. Once both are set up, the python module can be installed from the root repository folder via

.. code-block:: shell

   pip install . --break-system-packages
   
The latter option may not be required in all cases, but it is in recent versions of Debian and OSX. Since EDIpack2py is currently not packaged by any distro, this will not create problems. If the user is using a virtual environment, the option is not necessary.





