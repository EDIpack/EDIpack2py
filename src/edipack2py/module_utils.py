import ctypes as ct
import numpy as np
import os, sys
from pathlib import Path
import types
import pkgconfig
import warnings


#############################################
# Function that finds and loads the library #
#############################################


def load_edipack_library(libname="edipack_cbindings"):
    custompath = []
    default_pc_dir = ".pkgconfig.d"
    system = sys.platform
    libext = ".dylib" if system == "darwin" else ".so"
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
            edipack_library = ct.CDLL(libfile)
            break
        except Exception as e:
            error_message.append(str(e))
    else:
        raise RuntimeError("Library loading failed.\n" + "\n".join(error_message))

    return edipack_library


#############################################
# Class that interfaces the edipack library #
#############################################
class dynamic_library_interface:
    # init class
    def __init__(self, library):
        self.library = library
        try:
            self.has_ineq = bool(ct.c_int.in_dll(self.library, "has_ineq").value)
        except Exception:
            self.has_ineq = None
            print("Cannot init dynamic_library_interface class: invalid library")
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

    # Add global variable to interface class
    def add_global_variable(self, dynamic_name, dynamic_type, target_attribute="value"):
        # Fail early if symbol missing
        try:
            dynamic_type.in_dll(self.library, dynamic_name)
        except ValueError:
            warnings.warn(f"Symbol '{dynamic_name}' not found in the DLL.")
            return

        def getter(_self):
            target_object = dynamic_type.in_dll(self.library, dynamic_name)
            if hasattr(target_object, target_attribute):
                attrib = getattr(target_object, target_attribute)
                if isinstance(attrib, bytes):
                    return attrib.decode()
                return attrib
            if hasattr(target_object, "__len__") and not isinstance(target_object, str):
                return list(target_object)

        def setter(_self, new_value):
            target_object = dynamic_type.in_dll(self.library, dynamic_name)
            if hasattr(target_object, "__len__") and not isinstance(target_object, str):
                if np.isscalar(new_value):
                    new_value = [new_value]
                minlength = min(len(target_object), len(new_value))
                target_object[:minlength] = new_value[:minlength]
                return
            elif hasattr(target_object, target_attribute):
                if isinstance(new_value, str):
                    new_value = new_value.encode()
                setattr(target_object, target_attribute, new_value)
                return
            else:
                print("Could not set variable")

        setattr(self.__class__, dynamic_name, property(getter, setter))

    # add method to interface class
    def add_method(self, func, name=None):
        if name is None:
            name = func.__name__
        # Bind the function to this instance
        bound_method = types.MethodType(func, self)
        setattr(self, name, bound_method)
