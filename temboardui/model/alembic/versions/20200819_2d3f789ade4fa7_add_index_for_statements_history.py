"""add index for statements_history

Revision ID: 3f789ade4fa7
Revises: 2678b1a78dfa
Create Date: 2020-08-19 10:46:16.178215

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '3f789ade4fa7'
down_revision = '2678b1a78dfa'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE INDEX ON statements.statements_history '
               'USING GIST (agent_address, agent_port, dbid, coalesce_range);')
