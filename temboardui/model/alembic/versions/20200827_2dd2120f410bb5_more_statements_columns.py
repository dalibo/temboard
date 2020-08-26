"""empty message

Revision ID: d2120f410bb5
Revises: d2ec76ec2c11
Create Date: 2020-08-27 10:30:54.910664

"""
import os.path

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2120f410bb5'
down_revision = 'd2ec76ec2c11'
branch_labels = None
depends_on = None


def sqlfile(name):
    directory = os.path.dirname(__file__)
    with open(os.path.join(directory, name + '.sql')) as fo:
        return sa.text(fo.read())


def upgrade():
    op.get_bind().execute(sqlfile("20200827_more_statements_columns"))
