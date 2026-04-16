"""Forecast tables — daily_aggregates, store_context, external_events, forecasts.

Revision ID: 004
Revises: 003
Create Date: 2026-04-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # daily_aggregates
    op.create_table('daily_aggregates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agg_date', sa.Date(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('net_sales', sa.Numeric(12, 2), server_default='0'),
        sa.Column('gross_sales', sa.Numeric(12, 2), server_default='0'),
        sa.Column('refund_total', sa.Numeric(12, 2), server_default='0'),
        sa.Column('comp_total', sa.Numeric(12, 2), server_default='0'),
        sa.Column('void_total', sa.Numeric(12, 2), server_default='0'),
        sa.Column('avg_ticket', sa.Numeric(8, 2), server_default='0'),
        sa.Column('order_count', sa.Integer(), server_default='0'),
        sa.Column('orders_dine_in', sa.Integer(), server_default='0'),
        sa.Column('orders_takeout', sa.Integer(), server_default='0'),
        sa.Column('orders_delivery', sa.Integer(), server_default='0'),
        sa.Column('orders_drive_through', sa.Integer(), server_default='0'),
        sa.Column('covers', sa.Integer(), nullable=True),
        sa.Column('total_labor_hours', sa.Numeric(8, 2), server_default='0'),
        sa.Column('total_labor_cost', sa.Numeric(10, 2), server_default='0'),
        sa.Column('labor_hours_kitchen', sa.Numeric(8, 2), server_default='0'),
        sa.Column('labor_hours_foh', sa.Numeric(8, 2), server_default='0'),
        sa.Column('labor_hours_bar', sa.Numeric(8, 2), server_default='0'),
        sa.Column('labor_hours_delivery', sa.Numeric(8, 2), server_default='0'),
        sa.Column('labor_hours_manager', sa.Numeric(8, 2), server_default='0'),
        sa.Column('labor_cost_ratio', sa.Numeric(5, 4), nullable=True),
        sa.Column('daypart_json', postgresql.JSONB(), nullable=True),
        sa.Column('top_skus_json', postgresql.JSONB(), nullable=True),
        sa.Column('category_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_daily_agg_location_date', 'daily_aggregates', ['location_id', 'agg_date'], unique=True)
    op.create_index('ix_daily_agg_location', 'daily_aggregates', ['location_id'])

    # store_context
    op.create_table('store_context',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('context_date', sa.Date(), nullable=False),
        sa.Column('context_type', sa.String(50), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('payload_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_store_ctx_location_date', 'store_context', ['location_id', 'context_date'])

    # external_events
    op.create_table('external_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('impact_estimate', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), server_default='0.5'),
        sa.Column('is_recurring', sa.Boolean(), server_default='false'),
        sa.Column('payload_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ext_event_date_type', 'external_events', ['event_date', 'event_type'])
    op.create_index('ix_ext_event_location', 'external_events', ['location_id', 'event_date'])

    # forecasts
    op.create_table('forecasts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_date', sa.Date(), nullable=False),
        sa.Column('horizon_days', sa.Integer(), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('expected_sales', sa.Float(), nullable=False),
        sa.Column('expected_orders', sa.Integer(), nullable=False),
        sa.Column('expected_covers', sa.Integer(), nullable=True),
        sa.Column('sales_low', sa.Float(), nullable=False),
        sa.Column('sales_high', sa.Float(), nullable=False),
        sa.Column('confidence_level', sa.Float(), server_default='0.8'),
        sa.Column('orders_by_channel_json', postgresql.JSONB(), nullable=True),
        sa.Column('daypart_json', postgresql.JSONB(), nullable=True),
        sa.Column('labor_hours_json', postgresql.JSONB(), nullable=True),
        sa.Column('top_skus_json', postgresql.JSONB(), nullable=True),
        sa.Column('risk_flags_json', postgresql.JSONB(), nullable=True),
        sa.Column('explanation', sa.String(1000), nullable=True),
        sa.Column('purchasing_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_forecast_location_target', 'forecasts', ['location_id', 'target_date'])
    op.create_index('ix_forecast_run', 'forecasts', ['run_id'])


def downgrade() -> None:
    op.drop_table('forecasts')
    op.drop_table('external_events')
    op.drop_table('store_context')
    op.drop_table('daily_aggregates')
