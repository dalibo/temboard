"""alerting

Revision ID: cd5b518ab5cf
Revises: 81f0aef8a119
Create Date: 2020-03-25 16:56:26.929549

"""
import os.path

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cd5b518ab5cf'
down_revision = '81f0aef8a119'
branch_labels = None
depends_on = None


def sqlfile(name):
    directory = os.path.dirname(__file__)
    with open(os.path.join(directory, name + '.sql')) as fo:
        return sa.text(fo.read())


def upgrade():
    op.get_bind().execute(sqlfile('alerting'))
