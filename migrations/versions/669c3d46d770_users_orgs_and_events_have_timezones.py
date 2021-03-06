"""Users, orgs, and events have timezones

Revision ID: 669c3d46d770
Revises: 66bc67e7a8d5
Create Date: 2015-12-24 12:54:22.373114

"""

# revision identifiers, used by Alembic.
revision = '669c3d46d770'
down_revision = '66bc67e7a8d5'

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event', sa.Column('timezone', sa.String(length=50), nullable=True))
    op.add_column('organization_user', sa.Column('timezone', sa.String(length=50), nullable=True))
    op.add_column('user', sa.Column('timezone', sa.String(length=50), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'timezone')
    op.drop_column('organization_user', 'timezone')
    op.drop_column('event', 'timezone')
    ### end Alembic commands ###
