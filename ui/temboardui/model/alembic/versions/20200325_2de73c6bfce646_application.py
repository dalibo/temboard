"""application

Revision ID: e73c6bfce646
Revises:
Create Date: 2020-03-25 15:33:58.563183

"""
import os.path

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e73c6bfce646'
down_revision = None
branch_labels = None
depends_on = None


def sqlfile(name):
    directory = os.path.dirname(__file__)
    with open(os.path.join(directory, name + '.sql')) as fo:
        return sa.text(fo.read())


def upgrade():
    op.get_bind().execute(sqlfile('application'))
