"""empty message

Revision ID: 9c7591de9271
Revises: a65774c03dc7
Create Date: 2023-01-16 21:29:41.073955

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c7591de9271'
down_revision = 'a65774c03dc7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('contacts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tenant_id', sa.String(length=100), nullable=False),
    sa.Column('number', sa.String(length=20), nullable=False),
    sa.Column('first_name', sa.String(length=100), nullable=True),
    sa.Column('last_name', sa.String(length=100), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('type', sa.String(length=25), nullable=True),
    sa.Column('status', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['tenant_id'], ['subaccounts.tenant_id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('number', 'tenant_id', 'deleted_at', name='unique__number__tenant_id__deleted_at')
    )
    with op.batch_alter_table('conversation_participants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('contact_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(None, 'contacts', ['contact_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('conversation_participants', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('contact_id')

    op.drop_table('contacts')
    # ### end Alembic commands ###
