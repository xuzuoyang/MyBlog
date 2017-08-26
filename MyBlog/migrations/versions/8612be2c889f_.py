"""empty message

Revision ID: 8612be2c889f
Revises: 880ab3963c44
Create Date: 2017-08-26 21:51:16.850244

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '8612be2c889f'
down_revision = '880ab3963c44'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('postthumbs',
    sa.Column('post_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('post_id', 'user_id')
    )
    op.create_table('commentthumbs',
    sa.Column('comment_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('comment_id', 'user_id')
    )
    op.add_column('comments', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.drop_column('posts', 'thumb_up')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('posts', sa.Column('thumb_up', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.drop_column('comments', 'parent_id')
    op.drop_table('commentthumbs')
    op.drop_table('postthumbs')
    # ### end Alembic commands ###
