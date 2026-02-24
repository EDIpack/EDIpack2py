from ctypes import *
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
    "Nbath": c_int,
    "Norb": c_int,
    "Nspin": c_int,
    "Nloop": c_int,
    "Nph": c_int,
    "Nsuccess": c_int,
    "Lmats": c_int,
    "Lreal": c_int,
    "Ltau": c_int,
    "Lfit": c_int,
    "Lpos": c_int,
    "Uloc": ARRAY(c_double, 5),
    "pair_field": ARRAY(c_double, 15),
    "Ust": c_double,
    "Jh": c_double,
    "Jx": c_double,
    "Jp": c_double,
    "xmu": c_double,
    "beta": c_double,
    "dmft_error": c_double,
    "eps": c_double,
    "wini": c_double,
    "wfin": c_double,
    "xmin": c_double,
    "xmax": c_double,
    "sb_field": c_double,
    "nread": c_double,
    "ed_total_ud": c_bool,
    "ed_twin": c_bool,
    "chispin_flag": c_bool,
    "chidens_flag": c_bool,
    "chipair_flag": c_bool,
    "chiexct_flag": c_bool,
    "rdm_flag": c_bool,
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
