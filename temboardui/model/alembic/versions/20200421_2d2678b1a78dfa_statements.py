"""statements

Revision ID: 2678b1a78dfa
Revises: cd5b518ab5cf
Create Date: 2020-04-21 14:14:10.650409

"""
import os.path

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2678b1a78dfa'
down_revision = '48dc1c585e8'
branch_labels = None
depends_on = None


def sqlfile(name):
    directory = os.path.dirname(__file__)
    with open(os.path.join(directory, name + '.sql')) as fo:
        return sa.text(fo.read())


def upgrade():
    op.get_bind().execute(sqlfile('statements'))
