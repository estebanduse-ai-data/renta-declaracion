"""merge_0002_y_ajuste_post_inicial

Revision ID: 4c32c83f5aa4
Revises: 0002_resultado_liquidacion, 33827e5c8222
Create Date: 2026-07-24 20:13:03.842433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c32c83f5aa4'
down_revision: Union[str, None] = ('0002_resultado_liquidacion', '33827e5c8222')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
