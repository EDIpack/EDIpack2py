from ctypes import *
import numpy as np
import os, sys
from pathlib import Path
import types
import pkgconfig
import warnings

#################################
# AUXILIARY FUNCTIONS
#################################


# dummy class, to be filled
class Link:
    def __init__(self, library):
        self.library = library
        try:
            self.has_ineq = bool(c_int.in_dll(self.library, "has_ineq").value)
        except Exception:
            self.has_ineq = None
            print("Cannot init link class: invalid library")
        self.Nineq = None
        self.dim_hloc = 0
        self.Nsym = None
        # utils: colors and bold text
        self.PURPLE = "\033[95m"
        self.CYAN = "\033[96m"
        self.DARKCYAN = "\033[36m"
        self.BLUE = "\033[94m"
        self.GREEN = "\033[92m"
        self.YELLOW = "\033[93m"
        self.RED = "\033[91m"
        self.BOLD = "\033[1m"
        self.UNDERLINE = "\033[4m"
        self.COLOREND = "\033[0m"


# function that will add a variable to the dummy class, will be called
# in variable definition
def add_global_variable(
    dynamic_name, dynamic_type, obj, dynamic_library, target_attribute="value"
):
    try:
        dynamic_type.in_dll(dynamic_library, dynamic_name)
    except:
        warnings.warn(
            f"Symbol '{dynamic_name}' not found in the DLL. Check library version."
        )
        return

    def getter(self):
        target_object = dynamic_type.in_dll(dynamic_library, dynamic_name)
        # If target_object has the attribute
        if hasattr(target_object, target_attribute):
            attrib = getattr(target_object, target_attribute)
            if isinstance(attrib, bytes):
                return attrib.decode()
            return attrib
        # If target_object is list-like or array-like
        if hasattr(target_object, "__len__") and not isinstance(target_object, str):
            return list(target_object)

    def setter(self, new_value):
        target_object = dynamic_type.in_dll(dynamic_library, dynamic_name)
        # If target_object is array-like
        if hasattr(target_object, "__len__") and not isinstance(target_object, str):
            if np.isscalar(new_value):
                new_value = [new_value]
            minlength = min(len(target_object), len(new_value))
            target_object[:minlength] = new_value[:minlength]
            return

        # If target_object has the attribute
        elif hasattr(target_object, target_attribute):
            if isinstance(new_value, str):
                new_value = new_value.encode()
            setattr(target_object, target_attribute, new_value)
            return

        else:
            print("Could not set variable")

    # Dynamically add the property to the class
    setattr(obj.__class__, dynamic_name, property(getter, setter))


######################################
# Load shared library with C-bindings
######################################

custompath = []
default_pc_dir = ".pkgconfig.d"
system = sys.platform
libext = ".dylib" if system == "darwin" else ".so"
libname = "edipack_cbindings"
pathlist = []

# 1st try: use custom env variable
try:
    pathlist += os.environ["EDIPACK_PATH"].split(os.pathsep)
except Exception:
    pass

# 2nd try: use pkgconfig directly
if pkgconfig.exists("edipack"):
    pathlist += [pkgconfig.variables(libname)["libdir"]]

# 3rd try: check PKG_CONFIG_PATH
else:
    try:
        os.environ["PKG_CONFIG_PATH"] += os.pathsep + os.path.join(
            Path.home(), default_pc_dir
        )
    except Exception:
        os.environ["PKG_CONFIG_PATH"] = os.path.join(Path.home(), default_pc_dir)
    if pkgconfig.exists("edipack"):
        pathlist += [pkgconfig.variables(libname)["libdir"]]

# 4th try: look in standard environment variables
try:
    pathlist += os.environ["LD_LIBRARY_PATH"].split(os.pathsep)
except Exception:
    pass
try:
    pathlist += os.environ["DYLD_LIBRARY_PATH"].split(os.pathsep)
except Exception:
    pass

# try loading the library
edipack_library = None
error_message = []

for ipath in pathlist:
    try:
        libfile = os.path.join(ipath, "lib" + libname + libext)
        edipack_library = CDLL(libfile)
        break
    except Exception as e:
        error_message.append(str(e))
else:
    print("Library loading failed. List of error messages:")
    print(*error_message, sep="\n")


####################################################################
# Create the global_env class (this is what the python module sees)
####################################################################

global_env = Link(edipack_library)

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
    add_global_variable(varname, vartype, global_env, edipack_library)


######################################
# GLOBAL FUNCTIONS
######################################

# parse umatrix
try:
    from . import func_parse_umatrix

    global_env.reset_umatrix = types.MethodType(
        func_parse_umatrix.reset_umatrix, global_env
    )
    global_env.add_twobody_operator = types.MethodType(
        func_parse_umatrix.add_twobody_operator, global_env
    )
except Exception:
    pass

# read_input
from . import func_read_input

global_env.read_input = types.MethodType(func_read_input.read_input, global_env)

# aux_funx
from . import func_aux_funx

global_env.get_bath_type = types.MethodType(func_aux_funx.get_bath_type, global_env)
global_env.get_ed_mode = types.MethodType(func_aux_funx.get_ed_mode, global_env)

global_env.set_hloc = types.MethodType(func_aux_funx.set_hloc, global_env)
global_env.search_variable = types.MethodType(func_aux_funx.search_variable, global_env)
global_env.check_convergence = types.MethodType(
    func_aux_funx.check_convergence, global_env
)

# bath
from . import func_bath

global_env.get_bath_dimension = types.MethodType(
    func_bath.get_bath_dimension, global_env
)
global_env.set_hreplica = types.MethodType(func_bath.set_hreplica, global_env)
global_env.set_hgeneral = types.MethodType(func_bath.set_hgeneral, global_env)
global_env.break_symmetry_bath = types.MethodType(
    func_bath.break_symmetry_bath, global_env
)
global_env.spin_symmetrize_bath = types.MethodType(
    func_bath.spin_symmetrize_bath, global_env
)
global_env.orb_symmetrize_bath = types.MethodType(
    func_bath.orb_symmetrize_bath, global_env
)
global_env.orb_equality_bath = types.MethodType(func_bath.orb_equality_bath, global_env)
global_env.ph_symmetrize_bath = types.MethodType(
    func_bath.ph_symmetrize_bath, global_env
)
global_env.save_array_as_bath = types.MethodType(
    func_bath.save_array_as_bath, global_env
)

global_env.bath_inspect = types.MethodType(func_bath.bath_inspect, global_env)


# main
from . import func_main

global_env.init_solver = types.MethodType(func_main.init_solver, global_env)
global_env.solve = types.MethodType(func_main.solve, global_env)
global_env.finalize_solver = types.MethodType(func_main.finalize_solver, global_env)

# io
from . import func_io

global_env.build_sigma = types.MethodType(func_io.build_sigma, global_env)
global_env.build_gimp = types.MethodType(func_io.build_gimp, global_env)
global_env.get_sigma = types.MethodType(func_io.get_sigma, global_env)
global_env.get_gimp = types.MethodType(func_io.get_gimp, global_env)
global_env.get_g0and = types.MethodType(func_io.get_g0and, global_env)
global_env.get_delta = types.MethodType(func_io.get_delta, global_env)
global_env.get_dens = types.MethodType(func_io.get_dens, global_env)
global_env.get_mag = types.MethodType(func_io.get_mag, global_env)
global_env.get_docc = types.MethodType(func_io.get_docc, global_env)
global_env.get_phi = types.MethodType(func_io.get_phi, global_env)
global_env.get_eimp = types.MethodType(func_io.get_eimp, global_env)
global_env.get_chi = types.MethodType(func_io.get_chi, global_env)
global_env.get_impurity_rdm = types.MethodType(func_io.get_impurity_rdm, global_env)

# bath_fit
from . import func_bath_fit

global_env.chi2_fitgf = types.MethodType(func_bath_fit.chi2_fitgf, global_env)
