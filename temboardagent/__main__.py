import sys

from .cli import main

try:
    main()
except Exception as e:
    sys.stderr.write("FATAL: %s\n" % str(e))
    exit(1)
