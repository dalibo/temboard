import os
import sys
import warnings

if True:  # Vendoring
    parent_dir = os.path.abspath(os.path.dirname(__file__))
    vendor_dir = os.path.join(parent_dir, "_vendor")
    sys.path.append(vendor_dir)

from .version import __version__  # noqa

if "DEBUG" not in os.environ and "CI" not in os.environ:
    warnings.filterwarnings("ignore")
