"""Add comment field to instances table

Revision ID: 48dc1c585e8
Revises: cd5b518ab5cf
Create Date: 2020-07-06 11:02:05.598278

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '48dc1c585e8'
down_revision = 'cd5b518ab5cf'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('instances',
                  sa.Column('comment', sa.UnicodeText),
                  schema='application')


def downgrade():
    op.drop_column('instances', 'comment', schema='application')
