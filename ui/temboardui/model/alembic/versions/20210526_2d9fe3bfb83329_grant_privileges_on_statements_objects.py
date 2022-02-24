"""Grant privileges on statements objects

Revision ID: 9fe3bfb83329
Revises: d2120f410bb5
Create Date: 2021-05-26 14:35:33.395124

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '9fe3bfb83329'
down_revision = 'd2120f410bb5'
branch_labels = None
depends_on = None


def sqlfile(name):
    op.execute("""
    GRANT ALL ON SCHEMA statements TO temboard;
    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA statements TO temboard;
    GRANT ALL ON ALL TABLES IN SCHEMA statements TO temboard;
    GRANT ALL ON ALL SEQUENCES IN SCHEMA statements TO temboard;
    """)


def upgrade():
    pass
