# -*- coding: utf-8 -*-

import sys

from ..usermgmt import hash_password


def display_usage():
    sys.stdout.write(
        "Usage: temboard-agent-password <username>:<password>\n"
        "\n"
        "Build an authentication string for temboard-agent based on "
        "username/password couple.\n"
        "\n"
        "Options:\n"
        "  -h, --help           show this help message and exit\n")
    exit(0)


def main():
    if len(sys.argv) != 2:
        display_usage()
    if sys.argv[1] == "-h" or sys.argv == "--help":
        display_usage()
    expl = str(sys.argv[1]).split(':')
    if len(expl) != 2:
        display_usage()
    sys.stdout.write("%s:%s\n" % (
        expl[0],
        hash_password(expl[0], expl[1]).decode('utf-8'))
    )
    exit(0)


if __name__ == '__main__':
    main()
