Functions
==============

The user-accessible functions of `EDIpack2py` are methods of the :data:`global_env` class. They act as interfaces to functions and subroutines of `EDIpack`. Depending on whether the Fortran library was built with :code:`-DWITH_INEQ` or not, the `EDIpack2py` function will accept parameters that relate to real-space DMFT problems (such as the number of inequivalent sites :data:`Nlat` ). If the real-space DMFT module is not available, a :code:`RuntimeError` will be raised. Refer to the EDIpack :ref:`installation instructions <edipack:edipack_install>` for more details.


.. toctree::
   :maxdepth: 1
   :glob:

   funcs/*




