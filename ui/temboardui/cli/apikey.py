import logging
try:
    from secrets import choice
except ImportError:  # For Python 3.5 and lower
    from random import choice
import string
import sys
from textwrap import dedent

from .app import app
from ..toolkit.app import SubCommand
from ..toolkit.errors import UserError
from ..model import Session
from ..model.orm import ApiKeys


logger = logging.getLogger(__name__)


@app.command
class ApiKey(SubCommand):
    """ Manage API keys. """

    def main(self, args):
        raise UserError("Missing sub-command. See --help for details.")


@ApiKey.command
class Create(SubCommand):
    """ Create a new API key. """

    def define_arguments(self, parser):
        parser.add_argument(
            "--comment",
            help="Define a custom comment.",
        )

    def main(self, args):
        session = Session()
        key = ApiKeys.insert(
            secret=generate_secret(),
            comment=args.comment,
        ).with_session(session).scalar()
        session.commit()

        sys.stdout.write(dedent("""\
        Id,Secret,Comment,Expiration
        {key.id},"{key.secret}","{comment}",{edate}
        """).format(
            comment=key.comment or '',
            edate=key.edate.isoformat(),
            key=key,
        ))


@ApiKey.command
class List(SubCommand):
    """ List active keys. """

    def main(self, args):
        session = Session()

        sys.stdout.write("Id,Secret,Comment,Creation,Expiration\n")
        for key in ApiKeys.select_active().with_session(session).all():
            sys.stdout.write(dedent("""\
            {key.id},"{key.secret}","{comment}",{cdate},{edate}
            """).format(
                comment=key.comment or '',
                cdate=key.cdate.isoformat(),
                edate=key.edate.isoformat(),
                key=key,
            ))


@ApiKey.command
class Delete(SubCommand):
    """ Delete a key. """

    def define_arguments(self, parser):
        parser.add_argument(
            "id", type=int,
            help="Target key id.",
        )

    def main(self, args):
        session = Session()
        key = ApiKeys.delete(args.id).with_session(session).scalar()
        session.commit()

        if key:
            logger.info("Deleted API key #%s (%s).", key.id, key.comment)
        else:
            logger.info("No API key deleted.")


@ApiKey.command
class Purge(SubCommand):
    """ Purge expired. """

    def main(self, args):
        session = Session()
        res = ApiKeys.purge().with_session(session).all()
        count = 0
        for key in res:
            logger.info("Deleted API key #%s (%s).", key.id, key.comment)
            count += 1
        session.commit()

        if count:
            logger.info("Purged %d keys.", count)
        else:
            logger.info("No expired keys to purge.")


_SECRET_LETTERS = string.ascii_letters + string.digits + '+/-_'


def generate_secret(length=40):
    return ''.join(choice(_SECRET_LETTERS) for _ in range(length))
