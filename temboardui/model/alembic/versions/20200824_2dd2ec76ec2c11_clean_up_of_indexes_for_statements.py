"""Clean up of indexes for statements

Revision ID: d2ec76ec2c11
Revises: 3f789ade4fa7
Create Date: 2020-08-24 10:47:50.095304

"""
import os.path

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2ec76ec2c11'
down_revision = '3f789ade4fa7'
branch_labels = None
depends_on = None


def sqlfile(name):
    directory = os.path.dirname(__file__)
    with open(os.path.join(directory, name + '.sql')) as fo:
        return sa.text(fo.read())


def upgrade():
    op.get_bind().execute(sqlfile("20200824_statements_indexes_cleanup"))
