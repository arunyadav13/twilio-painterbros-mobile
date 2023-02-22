"""empty message

Revision ID: ef9f71a00dc6
Revises: aeaca18210d5
Create Date: 2022-12-26 13:24:30.846986

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ef9f71a00dc6'
down_revision = 'aeaca18210d5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('phone_numbers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('subaccount_id', sa.Integer(), nullable=False),
    sa.Column('number', sa.String(length=20), nullable=False),
    sa.Column('twilio_sid', sa.String(length=50), nullable=False),
    sa.Column('emergency_addr_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['emergency_addr_id'], ['emergency_addresses.id'], ),
    sa.ForeignKeyConstraint(['subaccount_id'], ['subaccounts.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('number', 'deleted_at', name='unique__number__deleted_at'),
    sa.UniqueConstraint('twilio_sid', 'deleted_at', name='unique__twilio_sid__deleted_at')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('phone_numbers')
    # ### end Alembic commands ###
