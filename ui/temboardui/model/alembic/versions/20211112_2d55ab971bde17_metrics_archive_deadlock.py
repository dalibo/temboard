"""metrics-archive-deadlock

Revision ID: 55ab971bde17
Revises: 67f52879da15
Create Date: 2021-11-12 10:24:47.899243

"""
import os.path

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '55ab971bde17'
down_revision = '67f52879da15'
branch_labels = None
depends_on = None


def sqlfile(name):
    directory = os.path.dirname(__file__)
    with open(os.path.join(directory, name + '.sql')) as fo:
        return sa.text(fo.read())


def upgrade():
    name = os.path.basename(__file__)
    name, _ = name.rsplit('.', 1)
    op.get_bind().execute(sqlfile(name))
