import ctypes as ct
import importlib


try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:  # For Python <3.8
    from importlib_metadata import version, PackageNotFoundError

try:
    __version__ = version("edipack2py")
except PackageNotFoundError:
    __version__ = "unknown"


######################################
# Load shared library with C-bindings
######################################

from edipack2py import module_utils

edipack_library = module_utils.load_edipack_library("edipack_cbindings")
global_env = module_utils.dynamic_library_interface(edipack_library)

######################################
# GLOBAL VARIABLES
######################################

global_vars_dict = {
    "Nbath": ct.c_int,
    "Norb": ct.c_int,
    "Nspin": ct.c_int,
    "Nloop": ct.c_int,
    "Nph": ct.c_int,
    "Nsuccess": ct.c_int,
    "Lmats": ct.c_int,
    "Lreal": ct.c_int,
    "Ltau": ct.c_int,
    "Lfit": ct.c_int,
    "Lpos": ct.c_int,
    "Uloc": ct.ARRAY(ct.c_double, 5),
    "pair_field": ct.ARRAY(ct.c_double, 15),
    "Ust": ct.c_double,
    "Jh": ct.c_double,
    "Jx": ct.c_double,
    "Jp": ct.c_double,
    "xmu": ct.c_double,
    "beta": ct.c_double,
    "dmft_error": ct.c_double,
    "eps": ct.c_double,
    "wini": ct.c_double,
    "wfin": ct.c_double,
    "xmin": ct.c_double,
    "xmax": ct.c_double,
    "sb_field": ct.c_double,
    "nread": ct.c_double,
    "ed_total_ud": ct.c_bool,
    "ed_twin": ct.c_bool,
    "chispin_flag": ct.c_bool,
    "chidens_flag": ct.c_bool,
    "chipair_flag": ct.c_bool,
    "chiexct_flag": ct.c_bool,
    "rdm_flag": ct.c_bool,
}


for varname, vartype in global_vars_dict.items():
    global_env.add_global_variable(varname, vartype)


######################################
# GLOBAL FUNCTIONS
######################################

global_funcs_dict = {
    "func_parse_umatrix": ["reset_umatrix", "add_twobody_operator"],
    "func_read_input": ["read_input"],
    "func_aux_funx": [
        "get_bath_type",
        "get_ed_mode",
        "set_hloc",
        "search_variable",
        "check_convergence",
    ],
    "func_bath": [
        "get_bath_dimension",
        "set_hreplica",
        "set_hgeneral",
        "break_symmetry_bath",
        "spin_symmetrize_bath",
        "orb_symmetrize_bath",
        "orb_equality_bath",
        "ph_symmetrize_bath",
        "save_array_as_bath",
        "bath_inspect",
    ],
    "func_main": ["init_solver", "solve", "finalize_solver"],
    "func_io": [
        "build_sigma",
        "build_gimp",
        "get_sigma",
        "get_gimp",
        "get_g0and",
        "get_delta",
        "get_dens",
        "get_mag",
        "get_docc",
        "get_phi",
        "get_eimp",
        "get_chi",
        "get_impurity_rdm",
    ],
    "func_bath_fit": ["chi2_fitgf"],
}

for modname, funcnames in global_funcs_dict.items():
    mod = importlib.import_module(f"edipack2py.{modname}")
    for fname in funcnames:
        global_env.add_method(getattr(mod, fname))
