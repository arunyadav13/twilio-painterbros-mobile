"""empty message

Revision ID: c09d3c40ca1e
Revises: b05f04e904ce
Create Date: 2022-12-23 09:27:37.424494

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c09d3c40ca1e'
down_revision = 'b05f04e904ce'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('subaccounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('messaging_service_sid', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('a2p_10dlc_campaign_sid', sa.String(length=50), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('subaccounts', schema=None) as batch_op:
        batch_op.drop_column('a2p_10dlc_campaign_sid')
        batch_op.drop_column('messaging_service_sid')

    # ### end Alembic commands ###
