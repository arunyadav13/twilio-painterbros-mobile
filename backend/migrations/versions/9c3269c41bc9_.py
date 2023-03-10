"""empty message

Revision ID: 9c3269c41bc9
Revises: 9c7591de9271
Create Date: 2023-01-17 17:08:22.629856

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '9c3269c41bc9'
down_revision = '9c7591de9271'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('contacts', schema=None) as batch_op:
        batch_op.drop_column('first_name')
        batch_op.drop_column('last_name')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('contacts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_name', mysql.VARCHAR(length=100), nullable=True))
        batch_op.add_column(sa.Column('first_name', mysql.VARCHAR(length=100), nullable=True))

    # ### end Alembic commands ###
