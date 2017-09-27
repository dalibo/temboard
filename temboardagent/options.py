def define_common_arguments(parser):
    parser.add_argument(
        '-c', '--config',
        action='store', dest='configfile',
        default='/etc/temboard-agent/temboard-agent.conf',
        help="Configuration file. Default: %(default)s",
    )
