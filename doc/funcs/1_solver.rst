.. _solver:

Impurity Problem Initialization, Solution and Finalization
================================================================

These functions initialize, solve and finalize the impurity problem. They can be invoked inside or outside the DMFT loop. The solution environment can be completely reconstructed from the bath parameters array and the global variables.

.. autofunction:: edipack2py.global_env.finalize_solver

.. autofunction:: edipack2py.global_env.init_solver

.. autofunction:: edipack2py.global_env.set_hloc

.. autofunction:: edipack2py.global_env.solve


