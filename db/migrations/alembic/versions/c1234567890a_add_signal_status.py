"""Add NO_TOMADA and SIN_RESPUESTA to signals status.

Revision ID: c1234567890a
Revises: b500dbed383f
Create Date: 2026-01-15
"""

from alembic import op

revision = "c1234567890a"
down_revision = "b500dbed383f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Primero eliminar el constraint existente
    op.execute("""
        ALTER TABLE signals 
        DROP CONSTRAINT IF EXISTS signals_status_check
    """)

    # Agregar el constraint actualizado con los nuevos status
    op.execute("""
        ALTER TABLE signals 
        ADD CONSTRAINT signals_status_check 
        CHECK (status IN ('EMITIDA', 'TOMADA', 'NO_TOMADA', 'SIN_RESPUESTA', 'CERRADA', 'CANCELADA'))
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE signals 
        DROP CONSTRAINT IF EXISTS signals_status_check
    """)

    op.execute("""
        ALTER TABLE signals 
        ADD CONSTRAINT signals_status_check 
        CHECK (status IN ('EMITIDA', 'TOMADA', 'CERRADA', 'CANCELADA'))
    """)
