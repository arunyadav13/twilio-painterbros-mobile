"""empty message

Revision ID: 6c4f7cafe0ae
Revises: 97b1b815d7c8
Create Date: 2023-01-10 02:57:23.920198

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c4f7cafe0ae'
down_revision = '97b1b815d7c8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('conversations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('subaccount_id', sa.Integer(), nullable=False),
    sa.Column('twilio_sid', sa.String(length=50), nullable=False),
    sa.Column('unique_name', sa.String(length=50), nullable=False),
    sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'DELETED', name='status'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['subaccount_id'], ['subaccounts.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('twilio_sid', 'deleted_at', name='unique__twilio_sid__deleted_at'),
    sa.UniqueConstraint('unique_name', 'deleted_at', name='unique__unique_name__deleted_at')
    )
    op.create_table('participants',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('twilio_sid', sa.String(length=50), nullable=False),
    sa.Column('conversation_id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('identity', sa.String(length=50), nullable=True),
    sa.Column('proxy_address', sa.String(length=50), nullable=True),
    sa.Column('address', sa.String(length=50), nullable=True),
    sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'DELETED', name='status'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('twilio_sid', 'deleted_at', name='unique__twilio_sid__deleted_at')
    )
    op.create_table('messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('participant_id', sa.Integer(), nullable=False),
    sa.Column('twilio_sid', sa.String(length=50), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('media', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'DELETED', name='status'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['participant_id'], ['participants.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('twilio_sid', 'deleted_at', name='unique__twilio_sid__deleted_at')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('messages')
    op.drop_table('participants')
    op.drop_table('conversations')
    # ### end Alembic commands ###