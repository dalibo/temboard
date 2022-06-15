import os
import warnings

from .version import __version__  # noqa


if 'DEBUG' not in os.environ and 'CI' not in os.environ:
    warnings.filterwarnings('ignore')
