"""Aggiunta colonna stato a Reservation

Revision ID: 160c60171f4a
Revises: 
Create Date: 2024-01-07 15:22:33.341038

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '160c60171f4a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('reservation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stato', sa.String(length=15), nullable=False, server_default='IlTuoValoreDiDefault'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('reservation', schema=None) as batch_op:
        batch_op.drop_column('stato')

    # ### end Alembic commands ###
