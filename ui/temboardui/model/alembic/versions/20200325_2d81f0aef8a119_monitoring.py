"""monitoring

Revision ID: 81f0aef8a119
Revises: e73c6bfce646
Create Date: 2020-03-25 16:50:03.723607

"""
import os.path

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '81f0aef8a119'
down_revision = 'e73c6bfce646'
branch_labels = None
depends_on = None


def sqlfile(name):
    directory = os.path.dirname(__file__)
    with open(os.path.join(directory, name + '.sql')) as fo:
        return sa.text(fo.read())


def upgrade():
    op.get_bind().execute(sqlfile('monitoring'))
