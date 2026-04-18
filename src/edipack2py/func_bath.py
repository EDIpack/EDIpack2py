import ctypes as ct
import numpy as np
import os, sys
import types


# get_bath_dimension
def get_bath_dimension(self):
    """
    This function returns the correct dimension for the bath to be allocated \
    (for each impurity) given the parameters of the system.

    :return: a number which is the dimension of the bath array for each impurity.
    :rtype: int
    """
    get_bath_dimension_direct_wrap = self.library.get_bath_dimension_direct
    get_bath_dimension_direct_wrap.argtypes = None
    get_bath_dimension_direct_wrap.restype = ct.c_int

    get_bath_dimension_symmetries_wrap = self.library.get_bath_dimension_symmetries
    get_bath_dimension_symmetries_wrap.argtypes = [ct.c_int]
    get_bath_dimension_symmetries_wrap.restype = ct.c_int

    if self.get_bath_type() > 2:  # replica/general
        if self.Nsym is None:
            raise RuntimeError(
                "get_bath_dimension: no replica/general matrix is initialized "
            )
        else:
            bathdim = get_bath_dimension_symmetries_wrap(self.Nsym)
    else:
        bathdim = get_bath_dimension_direct_wrap()

    return bathdim


# init_hreplica
def set_hreplica(self, hvec, lambdavec):
    """

       This function is specific to :f:var:`bath_type` = :code:`=replica`. \
       It sets the basis of matrices and scalar parameters that, \
       upon linear combination, make up the bath replica.
        
       :type hvec: np.array(dtype=complex)
       :param hvec: array of bath matrices. They decompose the nonzero part of \
       the replica in a set. Each element of the set correspond to a \
       variational parameter.\
       That way the bath replica matrix is updated while preserving symmetries\
       of the user's choosing. The array can have the following shapes:

        * [ :code:`(Nnambu)` :math:`\\cdot` :data:`Nspin` :math:`\\cdot` \
        :data:`Norb` , :code:`(Nnambu)` :math:`\\cdot` :data:`Nspin` \
        :math:`\\cdot` :data:`Norb` , :code:`Nsym` ]:\
        3-dimensional, where Nnambu refers to the superconducting case and Nsym \
        is the number of matrices that make up the linear combination 
        * [:code:`(Nnambu)` :math:`\\cdot` :data:`Nspin` , :code:`(Nnambu)` \
        :data:`Nspin` ,  :data:`Norb` ,  :data:`Norb` , :code:`Nsym` ]:\
        5-dimensional, where Nnambu refers to the superconducting case and Nsym \
        is the number of matrices that make up the linear combination 
        
       :type lambdavec: np.array(dtype=float) 
       :param lambdavec: the array of coefficients of the linear combination.\
       This, along with the hybridizations V, are the fitting parameters of \
       the bath. The array has the following shape
       
        * [ :data:`Nbath` , :code:`Nsym` ]: for single-impurity DMFT, 2-dimensional,\
        where Nsym is the number of matrices that make up the linear combination 
        * [ :code:`Nlat`,  :data:`Nbath` , :code:`Nsym` ]: for real-space DMFT, \
        3-dimensional, where Nlat is the number of inequivalent impurity sites \
        and Nsym is the number of matrices that make up the linear combination 

       :raise ValueError: if the shapes of the arrays are inconsistent
         
       :return: Nothing
       :rtype: None
    """
    init_hreplica_symmetries_d5 = self.library.init_Hreplica_symmetries_d5
    init_hreplica_symmetries_d5.argtypes = [
        np.ctypeslib.ndpointer(dtype=complex, ndim=5, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=float, ndim=2, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
    ]
    init_hreplica_symmetries_d5.restype = None

    init_hreplica_symmetries_d3 = self.library.init_Hreplica_symmetries_d3
    init_hreplica_symmetries_d3.argtypes = [
        np.ctypeslib.ndpointer(dtype=complex, ndim=3, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=float, ndim=2, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
    ]
    init_hreplica_symmetries_d3.restype = None
    if self.has_ineq:
        init_hreplica_symmetries_lattice_d5 = (
            self.library.init_Hreplica_symmetries_lattice_d5
        )
        init_hreplica_symmetries_lattice_d5.argtypes = [
            np.ctypeslib.ndpointer(dtype=complex, ndim=5, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=float, ndim=3, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
        ]
        init_hreplica_symmetries_lattice_d5.restype = None

        init_hreplica_symmetries_lattice_d3 = (
            self.library.init_Hreplica_symmetries_lattice_d3
        )
        init_hreplica_symmetries_lattice_d3.argtypes = [
            np.ctypeslib.ndpointer(dtype=complex, ndim=3, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=float, ndim=3, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
        ]
        init_hreplica_symmetries_lattice_d3.restype = None

    aux_norb = ct.c_int.in_dll(self.library, "Norb").value
    aux_nspin = ct.c_int.in_dll(self.library, "Nspin").value
    dim_hvec = np.asarray(np.shape(hvec), dtype=np.int64, order="F")
    dim_lambdavec = np.asarray(np.shape(lambdavec), dtype=np.int64, order="F")

    self.Nsym = dim_lambdavec[1]

    # Arrays in Fortran ordering
    lambdavec = np.asfortranarray(lambdavec)
    hvec = np.asfortranarray(hvec)

    if len(dim_hvec) == 3:
        if len(dim_lambdavec) == 2:
            init_hreplica_symmetries_d3(hvec, dim_hvec, lambdavec, dim_lambdavec)
        elif len(dim_lambdavec) == 3:
            if self.has_ineq:
                init_hreplica_symmetries_lattice_d3(
                    hvec, dim_hvec, lambdavec, dim_lambdavec
                )
            else:
                raise RuntimeError(
                    "Can't use r-DMFT routines without installing EDIpack2ineq"
                )
        else:
            raise ValueError("Shape(lambdavec) != 2 or 3  in set_Hreplica")
    elif len(dim_hvec) == 5:
        if len(dim_lambdavec) == 2:
            init_hreplica_symmetries_d5(hvec, dim_hvec, lambdavec, dim_lambdavec)
        elif len(dim_lambdavec) == 3:
            if self.has_ineq:
                init_hreplica_symmetries_lattice_d5(
                    hvec, dim_hvec, lambdavec, dim_lambdavec
                )
            else:
                raise RuntimeError(
                    "Can't use r-DMFT routines without installing EDIpack2ineq"
                )
        else:
            raise ValueError("Shape(lambdavec) != 2 or 3  in set_Hreplica")
    else:
        raise ValueError("Shape(Hvec) != 3 or 5  in set_Hreplica")
    return


# init_hgeneral
def set_hgeneral(self, hvec, lambdavec):
    """
       This function is specific to :code:`BATH_TYPE=GENERAL`. It sets the \
       basis of matrices and scalar parameters that, upon linear combination, \
       make up the bath replica. \
       The input is the same as that of :func:`set_hreplica`.
        
       :type hvec: np.array(dtype=complex)
       :param hvec: array of bath matrices. They decompose the nonzero part of \
       the replica in a set.\
       Each element of the set correspond to a variational parameter.\
       That way the bath replica matrix is updated while preserving symmetries\
       of the user's choosing. The array can have the following shapes:

        * [:code:`(Nnambu)` :math:`\\cdot`:data:`Nspin` :math:`\\cdot` \
        :data:`Norb` , :code:`(Nnambu)` :math:`\\cdot` :data:`Nspin` \
        :math:`\\cdot` :data:`Norb` , :code:`Nsym` ]:\
        3-dimensional, where Nnambu refers to the superconducting case and Nsym \
        is the number of matrices that make up the linear combination 
        * [:code:`(Nnambu)` :math:`\\cdot` :data:`Nspin` , :code:`(Nnambu)` \
        :math:`\\cdot` :data:`Nspin` ,  :data:`Norb` ,  :data:`Norb` , :code:`Nsym` ]:\
        5-dimensional, where Nnambu refers to the superconducting case and Nsym is \
        the number of matrices that make up the linear combination 
        
       :type lambdavec: np.array(dtype=float) 
       :param lambdavec: the array of coefficients of the linear combination.\
       This, along with the hybridizations V, are the fitting parameters of \
       the bath. The array has the following shape
       
        * [ :data:`Nbath` , :code:`Nsym` ]: for single-impurity DMFT, 2-dimensional,\
        where Nsym is the number of matrices that make up the linear combination 
        * [ :code:`Nlat`,  :data:`Nbath` , :code:`Nsym` ]: for real-space DMFT, \
        3-dimensional, where Nlat is the number of inequivalent impurity sites \
        and Nsym is the number of matrices that make up the linear combination 

       :raise ValueError: if the shapes of the arrays are inconsistent
         
       :return: Nothing
       :rtype: None
    """
    init_hgeneral_symmetries_d5 = self.library.init_Hgeneral_symmetries_d5
    init_hgeneral_symmetries_d5.argtypes = [
        np.ctypeslib.ndpointer(dtype=complex, ndim=5, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=float, ndim=2, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
    ]
    init_hgeneral_symmetries_d5.restype = None

    init_hgeneral_symmetries_d3 = self.library.init_Hgeneral_symmetries_d3
    init_hgeneral_symmetries_d3.argtypes = [
        np.ctypeslib.ndpointer(dtype=complex, ndim=3, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=float, ndim=2, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
    ]
    init_hgeneral_symmetries_d3.restype = None

    if self.has_ineq:
        init_hgeneral_symmetries_lattice_d5 = (
            self.library.init_Hgeneral_symmetries_lattice_d5
        )
        init_hgeneral_symmetries_lattice_d5.argtypes = [
            np.ctypeslib.ndpointer(dtype=complex, ndim=5, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=float, ndim=3, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
        ]
        init_hgeneral_symmetries_lattice_d5.restype = None

        init_hgeneral_symmetries_lattice_d3 = (
            self.library.init_Hgeneral_symmetries_lattice_d3
        )
        init_hgeneral_symmetries_lattice_d3.argtypes = [
            np.ctypeslib.ndpointer(dtype=complex, ndim=3, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=float, ndim=3, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
        ]
        init_hgeneral_symmetries_lattice_d3.restype = None

    # Arrays in Fortran ordering
    lambdavec = np.asfortranarray(lambdavec)
    hvec = np.asfortranarray(hvec)

    aux_norb = ct.c_int.in_dll(self.library, "Norb").value
    aux_nspin = ct.c_int.in_dll(self.library, "Nspin").value
    dim_hvec = np.asarray(np.shape(hvec), dtype=np.int64, order="F")
    dim_lambdavec = np.asarray(np.shape(lambdavec), dtype=np.int64, order="F")

    self.Nsym = dim_lambdavec[1]

    if len(dim_hvec) == 3:
        if len(dim_lambdavec) == 2:
            init_hgeneral_symmetries_d3(hvec, dim_hvec, lambdavec, dim_lambdavec)
        elif len(dim_lambdavec) == 3:
            if self.has_ineq:
                init_hgeneral_symmetries_lattice_d3(
                    hvec, dim_hvec, lambdavec, dim_lambdavec
                )
            else:
                raise RuntimeError(
                    "Can't use r-DMFT routines without installing EDIpack2ineq"
                )
        else:
            raise ValueError("Shape(lambdavec) != 2 or 3  in set_Hgeneral")
    elif len(dim_hvec) == 5:
        if len(dim_lambdavec) == 2:
            init_hgeneral_symmetries_d5(hvec, dim_hvec, lambdavec, dim_lambdavec)
        elif len(dim_lambdavec) == 3:
            if self.has_ineq:
                init_hgeneral_symmetries_lattice_d5(
                    hvec, dim_hvec, lambdavec, dim_lambdavec
                )
            else:
                raise RuntimeError(
                    "Can't use r-DMFT routines without installing EDIpack2ineq"
                )
        else:
            raise ValueError("Shape(lambdavec) != 2 or 3  in set_Hgeneral")
    else:
        raise ValueError("Shape(Hvec) != 3 or 5  in set_Hgeneral")
    return


# break_symmetry_bath
def break_symmetry_bath(self, bath, field, sign, save=True):
    """
    
    This function breaks the spin symmetry of the bath, useful \
    for magnetic calculations to incite symmetry breaking.\
    Not compatible with :code:`REPLICA` or :code:`GENERAL` bath types.

    :type bath: np.array(dtype=float)
    :param bath: The user-accessible bath array
   
    :type field: float
    :param field: the magnitude of the symmetry-breaking shift
   
    :type sign: float or np.array(dtype=float)
    :param sign: the sign of the symmetry-breaking shift. In the case of \
     real-space DMFT, this function supports an array of floats of the same \
     shape of bath along dimension 0. If a scalar is passed, it is \
     automatically converted into a constant array of the appropriate 
     dimension. \
   
    :type save: bool
    :param save: whether to save the symmetry-broken bath for reading
   
    :return: the modified bath array
    :rtype: np.array(dtype=float) 
       
    """

    break_symmetry_bath_site = self.library.break_symmetry_bath_site
    break_symmetry_bath_site.argtypes = [
        np.ctypeslib.ndpointer(dtype=float, ndim=1, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
        ct.c_double,
        ct.c_double,
        ct.c_int,
    ]
    break_symmetry_bath_site.restype = None

    if self.has_ineq:
        break_symmetry_bath_ineq = self.library.break_symmetry_bath_ineq
        break_symmetry_bath_ineq.argtypes = [
            np.ctypeslib.ndpointer(dtype=float, ndim=1, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
            ct.c_double,
            np.ctypeslib.ndpointer(dtype=float, ndim=1, flags="F_CONTIGUOUS"),
            ct.c_int,
        ]
        break_symmetry_bath_ineq.restype = None

    if save:
        save_int = 1
    else:
        save_int = 0

    bath = np.ascontiguousarray(bath)
    bath_shape = np.asarray(np.shape(bath), dtype=np.int64, order="F")

    if (len(bath_shape)) == 1:
        break_symmetry_bath_site(bath, bath_shape, field, float(sign), save_int)
    else:
        if self.has_ineq:
            sign = sign * np.ones(bath_shape[0], order="F")
            break_symmetry_bath_ineq(bath, bath_shape, field, sign, save_int)
        else:
            raise RuntimeError(
                "Can't use r-DMFT routines without installing EDIpack2ineq"
            )
    bath = np.ascontiguousarray(bath)
    return bath


# spin_symmetrize_bath


def spin_symmetrize_bath(self, bath, save=True):
    """
       This function enforces equality of the opposite-spin components\
       of the bath array. Not compatible with :code:`REPLICA` or \
       :code:`GENERAL` bath types.

       :type bath: np.array(dtype=float)
       :param bath: The user-accessible bath array
          
       :type save: bool
       :param save: whether to save the symmetry-broken bath for reading
       
       :return: the modified bath array
       :rtype: np.array(dtype=float)
    """
    spin_symmetrize_bath_site = self.library.spin_symmetrize_bath_site
    spin_symmetrize_bath_site.argtypes = [
        np.ctypeslib.ndpointer(dtype=float, ndim=1, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
        ct.c_int,
    ]
    spin_symmetrize_bath_site.restypes = None
    if self.has_ineq:
        spin_symmetrize_bath_ineq = self.library.spin_symmetrize_bath_ineq
        spin_symmetrize_bath_ineq.argtypes = [
            np.ctypeslib.ndpointer(dtype=float, ndim=1, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
            ct.c_int,
        ]
        spin_symmetrize_bath_ineq.restypes = None
    if save:
        save_int = 1
    else:
        save_int = 0

    bath = np.asfortranarray(bath)
    bath_shape = np.asarray(np.shape(bath), dtype=np.int64, order="F")

    if (len(bath_shape)) == 1:
        spin_symmetrize_bath_site(bath, bath_shape, save_int)
    else:
        if self.has_ineq:
            spin_symmetrize_bath_ineq(bath, bath_shape, save_int)
        else:
            raise RuntimeError(
                "Can't use r-DMFT routines without installing EDIpack2ineq"
            )
    bath = np.ascontiguousarray(bath)
    return bath


# orb_symmetrize_bath
def orb_symmetrize_bath(self, bath, orb1, orb2, save=True):
    """
       This function enforces equality of the different-orbital components \
       of the bath array. Not compatible with :code:`REPLICA` or \
       :code:`GENERAL` bath types.

       :type bath: np.array(dtype=float)
       :param bath: The user-accessible bath array
       
       :type orb1: int
       :param orb1: first orbital index
       
       :type orb2: int
       :param orb2: second orbital index
          
       :type save: bool
       :param save: whether to save the symmetry-broken bath for reading
       
       :return: the modified bath array
       :rtype: np.array(dtype=float)
    """

    orb_symmetrize_bath_site = self.library.orb_symmetrize_bath_site
    orb_symmetrize_bath_site.argtypes = [
        np.ctypeslib.ndpointer(dtype=float, ndim=1, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
        ct.c_int,
    ]
    orb_symmetrize_bath_site.restypes = None
    if self.has_ineq:
        orb_symmetrize_bath_ineq = self.library.orb_symmetrize_bath_ineq
        orb_symmetrize_bath_ineq.argtypes = [
            np.ctypeslib.ndpointer(dtype=float, ndim=1, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
            ct.c_int,
        ]
        orb_symmetrize_bath_ineq.restypes = None

    if save:
        save_int = 1
    else:
        save_int = 0

    bath = np.asfortranarray(bath)
    bath_shape = np.asarray(np.shape(bath), dtype=np.int64, order="F")
    if (len(bath_shape)) == 1:
        orb_symmetrize_bath_site(bath, bath_shape, orb1 + 1, orb2 + 1, save_int)
    else:
        if self.has_ineq:
            orb_symmetrize_bath_ineq(bath, bath_shape, orb1 + 1, orb2 + 1, save_int)
        else:
            raise RuntimeError(
                "Can't use r-DMFT routines without installing EDIpack2ineq"
            )
    bath = np.ascontiguousarray(bath)
    return bath


# orb_equality_bath


def orb_equality_bath(self, bath, indx, save=True):
    """
       This function sets every orbital component to be equal to the \
       one of orbital :code:`indx`. Not compatible with :code:`REPLICA` or \
       :code:`GENERAL` bath types.

       :type bath: np.array(dtype=float)
       :param bath: The user-accessible bath array
       
       :type iorb: int 
       :param iorb: the orbital index to which every other will be set as equal
          
       :type save: bool
       :param save: whether to save the symmetry-broken bath for reading
       
       :raise ValueError: if the orbital index is out of bounds
       
       :return: the modified bath array
       :rtype: np.array(dtype=float) 
    """
    orb_equality_bath_site = self.library.orb_equality_bath_site
    orb_equality_bath_site.argtypes = [
        np.ctypeslib.ndpointer(dtype=float, ndim=1, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
        ct.c_int,
        ct.c_int,
    ]
    orb_equality_bath_site.restypes = None
    if self.has_ineq:
        orb_equality_bath_ineq = self.library.orb_equality_bath_ineq
        orb_equality_bath_ineq.argtypes = [
            np.ctypeslib.ndpointer(dtype=float, ndim=1, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
            ct.c_int,
            ct.c_int,
        ]
        orb_equality_bath_ineq.restypes = None

    aux_norb = ct.c_int.in_dll(self.library, "Norb").value
    if save:
        save_int = 1
    else:
        save_int = 0

    bath = np.asfortranarray(bath)
    bath_shape = np.asarray(np.shape(bath), dtype=np.int64, order="F")

    if (indx < 0) or (indx >= aux_norb):
        raise ValueError("orb_equality_bath: orbital index should be in [0,Norb]")
    else:
        indx = indx + 1  # python to fortran convention
        if (len(bath_shape)) == 1:
            orb_equality_bath_site(bath, bath_shape, indx, save_int)
        else:
            if self.has_ineq:
                orb_equality_bath_ineq(bath, bath_shape, indx, save_int)
            else:
                raise RuntimeError(
                    "Can't use r-DMFT routines without installing EDIpack2ineq"
                )
    bath = np.ascontiguousarray(bath)
    return bath


# ph_symmetrize_bath
def ph_symmetrize_bath(self, bath, save):
    """
       This function enforces particle-hole symmetry of the bath hybridization \
       function. Not compatible with :code:`REPLICA` or :code:`GENERAL` bath types.

       :type bath: np.array(dtype=float)
       :param bath: The user-accessible bath array
          
       :type save: bool
       :param save: whether to save the symmetry-broken bath for reading
       
       :return: the modified bath array
       :rtype: np.array(dtype=float) 
    """
    ph_symmetrize_bath_site = self.library.ph_symmetrize_bath_site
    ph_symmetrize_bath_site.argtypes = [
        np.ctypeslib.ndpointer(dtype=float, ndim=1, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
        ct.c_int,
    ]
    ph_symmetrize_bath_site.restypes = None
    if self.has_ineq:
        ph_symmetrize_bath_ineq = self.library.ph_symmetrize_bath_ineq
        ph_symmetrize_bath_ineq.argtypes = [
            np.ctypeslib.ndpointer(dtype=float, ndim=1, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
            ct.c_int,
        ]
    ph_symmetrize_bath_ineq.restypes = None
    if save:
        save_int = 1
    else:
        save_int = 0

    bath = np.asfortranarray(bath)
    bath_shape = np.asarray(np.shape(bath), dtype=np.int64, order="F")

    if (len(bath_shape)) == 1:
        ph_symmetrize_bath_site(bath, bath_shape, save_int)
    else:
        if self.has_ineq:
            ph_symmetrize_bath_ineq(bath, bath_shape, save_int)
        else:
            raise RuntimeError(
                "Can't use r-DMFT routines without installing EDIpack2ineq"
            )
    bath = np.ascontiguousarray(bath)
    return bath


# save array as .restart file
def save_array_as_bath(self, bath):
    """
       This function takes the user-accessible array and saves it in the \
       correct format for every bath type in the file :code:`hamiltonian.restart`

       :type bath: np.array(dtype=float)
       :param bath: The user-accessible bath array
       
       :return: Nothing
       :rtype: None
    """
    save_array_as_bath_site = self.library.save_array_as_bath_site
    save_array_as_bath_site.argtypes = [
        np.ctypeslib.ndpointer(dtype=float, ndim=1, flags="F_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
    ]
    save_array_as_bath_site.restypes = None
    if self.has_ineq:
        save_array_as_bath_ineq = self.library.save_array_as_bath_ineq
        save_array_as_bath_ineq.argtypes = [
            np.ctypeslib.ndpointer(dtype=float, ndim=2, flags="F_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="F_CONTIGUOUS"),
        ]
        save_array_as_bath_ineq.restypes = None

    bath = np.asfortranarray(bath)
    bath_shape = np.asarray(np.shape(bath), dtype=np.int64, order="F")

    if (len(bath_shape)) == 1:
        save_array_as_bath_site(bath, bath_shape)
    else:
        if self.has_ineq:
            save_array_as_bath_ineq(bath, bath_shape)
        else:
            raise RuntimeError(
                "Can't use r-DMFT routines without installing EDIpack2ineq"
            )
    return


# auxiliary functions to get/set bath structure. Only works for single-site.
# User has to do a loop on sites
def bath_inspect(self, bath=None, e=None, v=None, d=None, u=None, l=None):
    """
       This function translates between the user-accessible continuous \
       bath array and the bath components (energy level, hybridization and so on). \
       It functions in both ways, given the array returns the components and \
       vice-versa. It autonomously determines the type of bath and ED mode.

       :type bath: np.array(dtype=float)
       :param bath: The user-accessible bath array
       
       :type e: np.array(dtype=float)
       :param e: an array for the bath levels ( :f:var:`ed_mode` = \
        :code:`NORMAL, NONSU2, SUPERC`). It has dimension [ :data:`Nspin` , \
        :data:`Norb` ,  :data:`Nbath` ] for :code:`NORMAL` bath, \
        [ :data:`Nspin` ,  :data:`Nbath` ] for :code:`HYBRID` bath 
       
       :type v: np.array(dtype=float)
       :param v: an array for the bath hybridizations ( :f:var:`ed_mode` = \
        :code:`NORMAL, NONSU2, SUPERC`). It has dimension [ :data:`Nspin` , :data:`Norb` , \
        :data:`Nbath` ] for :code:`NORMAL` and :code:`HYBRID` bath. \
        For :code:`REPLICA` bath it has dimension [ :data:`Nbath` ] and for \
        :code:`GENERAL` bath it has dimension [ :data:`Nbath` , :data:`Nspin` \
        :math:`\\cdot` :data:`Norb` ]
       
       :type d: np.array(dtype=float)
       :param d: an array for the bath anomalous enery levels( :f:var:`ed_mode` \
        = :code:`SUPERC`). It has dimension [ :data:`Nspin` ,  :data:`Norb` , \
        :data:`Nbath` ] for :code:`NORMAL` bath, [ :data:`Nspin` , :data:`Nbath` ] \
        for :code:`HYBRID` bath
       
       :type u: np.array(dtype=float)
       :param u: an array for the bath spin off-diagonal hybridization \
        ( :f:var:`ed_mode` = :code:`NONSU2`). It has dimension [ :data:`Nspin`, \
        :data:`Norb` ,  :data:`Nbath` ] for :code:`NORMAL` and :code:`HYBRID` bath

       :type l: np.array(dtype=float)
       :param l: an array for the linear coefficients of the Replica matrix \
        linear combination ( :f:var:`bath_type` = :code:`REPLICA,GENERAL`). \
        It has dimension [ :data:`Nbath` , :code:`Nsym` ], the latter being \
        the number of terms on the linear combination

       :raise ValueError: if both :code:`bath` and some among :code:`e,u,v,d,l` \
        are provided, none is provided, the shapes are inconsistent \
        or the inputs are inconsistent with :f:var:`bath_type` and :f:var:`ed_mode` .

       :return: a dictionary containing the bath or the coefficients, with their name
       :rtype: dict
    """

    def arr(x):
        return np.asarray(x, order="F") if x is not None else None

    def flat(x):
        return np.ravel(x, order="C")

    def check(x, shape, name):
        if x.shape != shape:
            raise ValueError(f"{name} must be {shape}")

    def pack(vals, order, bathtype):
        if bathtype > 2:
            return {
                "bath": np.ascontiguousarray(
                    np.concatenate([[Nsym]] + [flat(vals[k]) for k in order])
                )
            }
        else:
            return {
                "bath": np.ascontiguousarray(
                    np.concatenate([flat(vals[k]) for k in order])
                )
            }

    def unpack(b, spec):
        out = {}
        i = 0
        for name, shape in spec["fields"].items():
            n = int(np.prod(shape))
            out[name] = np.ascontiguousarray(b[i : i + n].reshape(shape, order="C"))
            i += n
        return out

    Norb = ct.c_int.in_dll(self.library, "Norb").value
    Nspin = ct.c_int.in_dll(self.library, "Nspin").value
    Nbath = ct.c_int.in_dll(self.library, "Nbath").value
    Nsym = self.Nsym
    key = (self.get_ed_mode(), self.get_bath_type())
    shape3 = (Nspin, Norb, Nbath)

    SPEC = {
        (1, 1): dict(
            fields={"e": shape3, "v": shape3},
            order=["e", "v"],
        ),
        (2, 1): dict(
            fields={"e": shape3, "d": shape3, "v": shape3},
            order=["e", "d", "v"],
        ),
        (3, 1): dict(
            fields={"e": shape3, "v": shape3, "u": shape3},
            order=["e", "v", "u"],
        ),
        (1, 2): dict(
            fields={"e": (Nspin, Nbath), "v": shape3},
            order=["e", "v"],
        ),
        (2, 2): dict(
            fields={"e": (Nspin, Nbath), "d": (Nspin, Nbath), "v": shape3},
            order=["e", "d", "v"],
        ),
        (3, 2): dict(
            fields={"e": (Nspin, Nbath), "v": shape3, "u": shape3},
            order=["e", "v", "u"],
        ),
        (1, 3): dict(
            fields={"v": (Nbath,), "l": (Nbath, Nsym)},
            order=["v", "l"],
        ),
        (2, 3): dict(
            fields={"v": (Nbath,), "l": (Nbath, Nsym)},
            order=["v", "l"],
        ),
        (3, 3): dict(
            fields={"v": (Nbath,), "l": (Nbath, Nsym)},
            order=["v", "l"],
        ),
        (1, 4): dict(
            fields={"v": (Nbath, Nspin * Norb), "l": (Nbath, Nsym)},
            order=["v", "l"],
        ),
        (2, 4): dict(
            fields={"v": (Nbath, Nspin * Norb), "l": (Nbath, Nsym)},
            order=["v", "l"],
        ),
        (3, 4): dict(
            fields={"v": (Nbath, Nspin * Norb), "l": (Nbath, Nsym)},
            order=["v", "l"],
        ),
    }

    spec = SPEC.get(key)
    if spec is None:
        raise ValueError("bath_inspect: unsupported ED/bath combination")
    if bath is None:
        source = {"e": e, "v": v, "d": d, "u": u, "l": l}
        vals = {}
        for k, shape in spec["fields"].items():
            vals[k] = arr(source[k])
            check(vals[k], shape, k)
        return pack(vals, spec["order"], key[1])
    else:
        bath = np.asarray(bath, order="F")
        Nb_dim = self.get_bath_dimension()
        if bath.shape[0] != Nb_dim:
            raise ValueError("bath_inspect: bath has wrong length")
        if key[1] > 2:
            if bath[0] != Nsym:
                raise ValueError("bath_inspect: bath[0] is not Nsym")
            bath = bath[1:]
        result = unpack(bath, spec)
        return {k: result[k] for k in spec["order"]}
