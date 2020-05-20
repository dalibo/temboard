"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
import os.path

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def sqlfile(name):
    directory = os.path.dirname(__file__)
    with open(os.path.join(directory, name + '.sql')) as fo:
        return sa.text(fo.read())


def upgrade():
    op.get_bind().execute(sqlfile("FIXME"))
