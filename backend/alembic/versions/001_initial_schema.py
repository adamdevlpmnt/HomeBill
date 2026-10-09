"""initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-10-09 22:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'meters',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('meter_type', sa.String(length=32), nullable=False, unique=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('meter_number', sa.String(length=64), nullable=True),
        sa.Column('unit', sa.String(length=16), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
    )
    op.create_table(
        'readings',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('meter_id', sa.Integer(), sa.ForeignKey('meters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('read_at', sa.Date(), nullable=False),
        sa.Column('index_value', sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column('note', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('meter_id', 'read_at', name='uq_meter_read_at'),
    )
    op.create_table(
        'meter_events',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('meter_id', sa.Integer(), sa.ForeignKey('meters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=32), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('old_index_end', sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column('new_index_start', sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column('note', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'tariff_versions',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('meter_type', sa.String(length=32), nullable=False),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('source', sa.String(length=128), nullable=False),
        sa.Column('note', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'billing_cycles',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('cycle_code', sa.String(length=32), nullable=False),
        sa.Column('energy_group', sa.String(length=32), nullable=False),
        sa.Column('quarter', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_closed', sa.Boolean(), nullable=False, server_default='0'),
        sa.UniqueConstraint('energy_group', 'cycle_code', name='uq_cycle_energy_code'),
    )
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('billing_cycle_id', sa.Integer(), sa.ForeignKey('billing_cycles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('energy_group', sa.String(length=32), nullable=False),
        sa.Column('cycle_code', sa.String(length=32), nullable=False),
        sa.Column('invoice_number', sa.String(length=64), nullable=True),
        sa.Column('invoice_date', sa.Date(), nullable=True),
        sa.Column('electricity_billed_kwh', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('gas_billed_th', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('water_billed_m3', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('actual_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('estimated_amount', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('variance_amount', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('variance_pct', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('key', sa.String(length=64), nullable=False, unique=True),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('description', sa.String(length=256), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('settings')
    op.drop_table('invoices')
    op.drop_table('billing_cycles')
    op.drop_table('tariff_versions')
    op.drop_table('meter_events')
    op.drop_table('readings')
    op.drop_table('meters')
