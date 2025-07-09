Basic usage
==============

Module import
--------------
Upon import, the `edipack2py` python module will try to load the dynamic library :data:`libedipack_cbindings.so` , provided by `EDIpack` and containing the c-fortran bindings. The module will try the following routes, in order of priority:

* As a first choice, the user can override the location of the library by exporting an environment variable called :code:`EDIPACK_PATH` .
* By default, the module detects the presence of the Fortran libraries via `pkg-config`. If `EDIpack` was loaded as an environment module, the import will automatically work. 
* The `EDIpack` library provides a `.pc` , located by default in the :code:`~/.pkgconfig.d` directory. If the environment variable :code:`PKG_CONFIG_PATH` is set to include the location of the `.pc` file, loading the library via `pkg-config` will work as well.
* As a last resort :code:`LD_LIBRARY_PATH` and :code:`DYLD_LIBRARY_PATH` are scanned. 

If none of the previous attempts succeeds, the module will not not load correctly and an error message will be printed. 

The `EDIpack <https://www.github.com/EDIpack/EDIpack/>`_ library offers, as an independent module, an interface for real-space DMFT functions (see relevant `documentation <https://edipack.github.io/EDIpack/>`_). `EDIpack2py` is in principle capable of solving real-space DMFT problems, provided the Fortran libraries were compiled with the real-space DMFT support enabled. If that is not the case, the python module will disable the real-space DMFT functions, and invoking them will result in a :code:`RuntimeError`. The user can check the availability of the real-space DMFT interface by printing the value of :code:`edipack2py.global_env.has_ineq`.

The `edipack2py` module consists mainly of a class called :code:`global_env`. The global variables and the functions of the `EDIpack` library that are exposed to the user are properties and methods of this class. The class needs to be imported at the beginning of the python script, along with other useful modules. `Numpy <https://numpy.org/>`_ is necessary, while `mpi4py <https://mpi4py.readthedocs.io/en/stable/>`_ is strongly recommended.

.. code-block:: python

    import numpy as np
    import mpi4py
    from mpi4py import MPI
    from edipack2py import global_env as ed
    import os,sys



Minimal DMFT loop
-------------------

An example driver is provided in the :code:`examples` folder of the `EDIpack2py` repository. The basic steps to follow to run a single DMFT loop are the following:

Read the input file

.. code-block:: python

    ed.read_input("inputED.conf")
    
This will read an input file or generate a template one if no such file is found. The template will have the :code:`used.` prefix, which will need to be removed. An `example <https://raw.githubusercontent.com/EDIpack/EDIpack2py/refs/heads/main/examples/inputED.conf>`_ of input file with a brief description of the relevant global variables is provided in the EDIpack repo.
    
Set the local Hamiltonian

.. code-block:: python

    ed.set_hloc(hloc=Hloc)
    
If  :f:var:`bath_type`  is :code:`REPLICA` or :code:`GENERAL`, the replica matrix has to be initialized via

.. code-block:: python

    ed.set_hreplica(hvec, lambdavec)
    ed.set_general(hvec, lambdavec)
    
where :code:`hvec` and :code:`lambdavec` are arrays of the proper size (see function documentation).

The solver needs to be initialized via 

.. code-block:: python

    bath = ed.init_solver()
    
Optionally, such as when real-space DMFT is used, the bath can be already allocated as an array, the dimension of which has to be given by the output of :code:`Nb` = :func:`ed.get_bath_dimension` for single-impurity DMFT and :code:`[Nlat,Nb]` for real-space DMFT, where :code:`Nlat` is the number of inequivalent impurities

The impurity problem is then solved via 

.. code-block:: python

    ed.solve(bath)
    
The self-energy needs to be retrieved in order to calculate the local lattice Green's function, via

.. code-block:: python

    Sigma = ed.get_sigma(axis="m")
    
The local Green's function calculation is left to the user, as well as that of the Weiss field or the Delta function, to be fitted by the new bath.
This latter step happens via 

.. code-block:: python

    bath = ed.chi2_fitgf(Delta,bath,ispin=0,iorb=0)
    
(check the function documentation for more details), but alternatively a fitting routine of the user's choice can be employed.
Convergence can be checked via

.. code-block:: python

    err,converged=ed.check_convergence(Delta[0,0,0,0,:],ed.dmft_error,1,ed.Nloop)
    
and, finally, the solution environment can be cleaned up via

.. code-block:: python

    ed.finalize_solver()
    
some or all of the steps above can be inserted in the DMFT convergence loop.
