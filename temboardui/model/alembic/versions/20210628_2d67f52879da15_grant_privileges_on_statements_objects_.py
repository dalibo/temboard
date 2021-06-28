"""Grant privileges on statements objects (bis)

Revision ID: 67f52879da15
Revises: 9fe3bfb83329
Create Date: 2021-06-28 12:05:25.116638

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '67f52879da15'
down_revision = '9fe3bfb83329'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    GRANT ALL ON SCHEMA statements TO temboard;
    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA statements TO temboard;
    GRANT ALL ON ALL TABLES IN SCHEMA statements TO temboard;
    GRANT ALL ON ALL SEQUENCES IN SCHEMA statements TO temboard;
    """)
