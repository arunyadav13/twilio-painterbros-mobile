"""empty message

Revision ID: 97b1b815d7c8
Revises: 94212122dba2
Create Date: 2023-01-04 15:18:22.197954

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '97b1b815d7c8'
down_revision = '94212122dba2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('call_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('subaccount_id', sa.Integer(), nullable=False),
    sa.Column('call_sid', sa.String(length=50), nullable=False),
    sa.Column('conference_sid', sa.String(length=50), nullable=False),
    sa.Column('source_number', sa.String(length=50), nullable=False),
    sa.Column('source_name', sa.String(length=50), nullable=True),
    sa.Column('source_phone_number_id', sa.Integer(), nullable=True),
    sa.Column('source_user_id', sa.String(length=100), nullable=True),
    sa.Column('destination_number', sa.String(length=50), nullable=False),
    sa.Column('destination_name', sa.String(length=50), nullable=True),
    sa.Column('destination_phone_number_id', sa.Integer(), nullable=True),
    sa.Column('destination_user_id', sa.String(length=100), nullable=True),
    sa.Column('log_for_user_id', sa.String(length=100), nullable=False),
    sa.Column('call_status', sa.String(length=20), nullable=False),
    sa.Column('direction', sa.String(length=50), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('meta_data', sa.JSON(), nullable=True),
    sa.Column('call_duration', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'DELETED', name='status'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['destination_phone_number_id'], ['phone_numbers.id'], ),
    sa.ForeignKeyConstraint(['source_phone_number_id'], ['phone_numbers.id'], ),
    sa.ForeignKeyConstraint(['subaccount_id'], ['subaccounts.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('call_sid', 'conference_sid', 'deleted_at', name='unique__call_sid__conference_sid__deleted_at')
    )
    op.create_table('voicemails',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('call_log_id', sa.Integer(), nullable=True),
    sa.Column('twilio_sid', sa.String(length=50), nullable=False),
    sa.Column('call_sid', sa.String(length=50), nullable=False),
    sa.Column('recording_start_at', sa.DateTime(), nullable=False),
    sa.Column('duration', sa.Integer(), nullable=False),
    sa.Column('transcribed_text', sa.Text(), nullable=True),
    sa.Column('recording_status', sa.String(length=50), nullable=False),
    sa.Column('pushed_to_s3', sa.Boolean(), nullable=False),
    sa.Column('s3_path', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['call_log_id'], ['call_logs.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('call_sid'),
    sa.UniqueConstraint('twilio_sid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('voicemails')
    op.drop_table('call_logs')
    # ### end Alembic commands ###
