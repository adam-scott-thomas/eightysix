"""Forecast contract v1 — 10 normalized tables replacing flat forecasts table.

Revision ID: 005
Revises: 004
Create Date: 2026-04-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old flat table
    op.drop_table('forecasts')

    # 1. forecast_runs
    op.create_table('forecast_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('as_of_ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('forecast_start_date', sa.Date(), nullable=False),
        sa.Column('forecast_end_date', sa.Date(), nullable=False),
        sa.Column('model_name', sa.String(50), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('model_family', sa.String(20), nullable=False),
        sa.Column('model_champion', sa.Boolean(), server_default='true'),
        sa.Column('real_history_days', sa.Integer(), server_default='0'),
        sa.Column('synthetic_history_days', sa.Integer(), server_default='0'),
        sa.Column('aggregate_days_used', sa.Integer(), server_default='0'),
        sa.Column('max_actual_date', sa.Date(), nullable=True),
        sa.Column('source_coverage_json', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('degraded_reasons_json', postgresql.JSONB(), server_default='[]'),
        sa.Column('run_notes_json', postgresql.JSONB(), server_default='[]'),
        sa.Column('generated_by', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fcrun_location_ts', 'forecast_runs', ['location_id', 'as_of_ts'])

    # 2. forecast_days
    op.create_table('forecast_days',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_date', sa.Date(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('horizon_days', sa.Integer(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('confidence_band', sa.String(10), nullable=False),
        sa.Column('sales_point', sa.Float(), nullable=False),
        sa.Column('sales_low', sa.Float(), nullable=False),
        sa.Column('sales_high', sa.Float(), nullable=False),
        sa.Column('orders_point', sa.Float(), nullable=False),
        sa.Column('orders_low', sa.Float(), nullable=False),
        sa.Column('orders_high', sa.Float(), nullable=False),
        sa.Column('labor_hours_point', sa.Float(), nullable=False),
        sa.Column('labor_hours_low', sa.Float(), nullable=False),
        sa.Column('labor_hours_high', sa.Float(), nullable=False),
        sa.Column('avg_ticket_point', sa.Float(), nullable=True),
        sa.Column('avg_ticket_low', sa.Float(), nullable=True),
        sa.Column('avg_ticket_high', sa.Float(), nullable=True),
        sa.Column('covers_point', sa.Integer(), nullable=True),
        sa.Column('covers_low', sa.Integer(), nullable=True),
        sa.Column('covers_high', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['forecast_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fcday_run', 'forecast_days', ['run_id'])
    op.create_index('ix_fcday_run_date', 'forecast_days', ['run_id', 'target_date'])

    # 3. forecast_day_channels
    op.create_table('forecast_day_channels',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('day_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel', sa.String(20), nullable=False),
        sa.Column('sales_point', sa.Float(), nullable=False),
        sa.Column('sales_low', sa.Float(), nullable=False),
        sa.Column('sales_high', sa.Float(), nullable=False),
        sa.Column('orders_point', sa.Float(), nullable=False),
        sa.Column('orders_low', sa.Float(), nullable=False),
        sa.Column('orders_high', sa.Float(), nullable=False),
        sa.Column('mix_share_point', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['day_id'], ['forecast_days.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 4. forecast_day_dayparts
    op.create_table('forecast_day_dayparts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('day_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('daypart', sa.String(20), nullable=False),
        sa.Column('sales_point', sa.Float(), nullable=False),
        sa.Column('sales_low', sa.Float(), nullable=False),
        sa.Column('sales_high', sa.Float(), nullable=False),
        sa.Column('orders_point', sa.Float(), nullable=False),
        sa.Column('orders_low', sa.Float(), nullable=False),
        sa.Column('orders_high', sa.Float(), nullable=False),
        sa.Column('labor_hours_point', sa.Float(), nullable=False),
        sa.Column('labor_hours_low', sa.Float(), nullable=False),
        sa.Column('labor_hours_high', sa.Float(), nullable=False),
        sa.Column('mix_share_point', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['day_id'], ['forecast_days.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 5. forecast_day_alerts
    op.create_table('forecast_day_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('day_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_type', sa.String(30), nullable=False),
        sa.Column('severity_0_to_100', sa.Float(), nullable=False),
        sa.Column('threshold_band', sa.String(10), nullable=False),
        sa.Column('message', sa.String(500), nullable=False),
        sa.ForeignKeyConstraint(['day_id'], ['forecast_days.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 6. forecast_day_drivers
    op.create_table('forecast_day_drivers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('day_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feature_key', sa.String(50), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('direction', sa.String(10), nullable=False),
        sa.Column('impact_pct', sa.Float(), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(20), nullable=False),
        sa.ForeignKeyConstraint(['day_id'], ['forecast_days.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 7. forecast_day_recommendations
    op.create_table('forecast_day_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('day_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rec_type', sa.String(30), nullable=False),
        sa.Column('priority', sa.String(10), nullable=False),
        sa.Column('message', sa.String(500), nullable=False),
        sa.Column('delta_value', sa.Float(), nullable=True),
        sa.Column('delta_unit', sa.String(20), nullable=True),
        sa.ForeignKeyConstraint(['day_id'], ['forecast_days.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 8. forecast_day_actuals
    op.create_table('forecast_day_actuals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('day_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('sales', sa.Float(), nullable=False),
        sa.Column('orders', sa.Integer(), nullable=False),
        sa.Column('labor_hours', sa.Float(), nullable=False),
        sa.Column('avg_ticket', sa.Float(), nullable=True),
        sa.Column('covers', sa.Integer(), nullable=True),
        sa.Column('channels_json', postgresql.JSONB(), nullable=True),
        sa.Column('dayparts_json', postgresql.JSONB(), nullable=True),
        sa.Column('sales_abs_error', sa.Float(), nullable=True),
        sa.Column('sales_pct_error', sa.Float(), nullable=True),
        sa.Column('orders_abs_error', sa.Float(), nullable=True),
        sa.Column('orders_pct_error', sa.Float(), nullable=True),
        sa.Column('labor_abs_error', sa.Float(), nullable=True),
        sa.Column('labor_pct_error', sa.Float(), nullable=True),
        sa.Column('in_sales_band', sa.Boolean(), nullable=True),
        sa.Column('in_orders_band', sa.Boolean(), nullable=True),
        sa.Column('in_labor_band', sa.Boolean(), nullable=True),
        sa.Column('bias_direction', sa.String(10), nullable=True),
        sa.ForeignKeyConstraint(['day_id'], ['forecast_days.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fcactuals_day', 'forecast_day_actuals', ['day_id'], unique=True)

    # 9. forecast_backtest_snapshots
    op.create_table('forecast_backtest_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('scored_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('history_window_days', sa.Integer(), nullable=False),
        sa.Column('horizon_buckets_json', postgresql.JSONB(), nullable=False),
        sa.Column('overall_model_score_0_to_100', sa.Float(), nullable=False),
        sa.Column('promoted', sa.Boolean(), server_default='false'),
        sa.ForeignKeyConstraint(['run_id'], ['forecast_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fcbacktest_run', 'forecast_backtest_snapshots', ['run_id'], unique=True)


def downgrade() -> None:
    op.drop_table('forecast_backtest_snapshots')
    op.drop_table('forecast_day_actuals')
    op.drop_table('forecast_day_recommendations')
    op.drop_table('forecast_day_drivers')
    op.drop_table('forecast_day_alerts')
    op.drop_table('forecast_day_dayparts')
    op.drop_table('forecast_day_channels')
    op.drop_table('forecast_days')
    op.drop_table('forecast_runs')

    # Recreate old flat table (minimal — just enough for rollback)
    op.create_table('forecasts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_date', sa.Date(), nullable=False),
        sa.Column('horizon_days', sa.Integer(), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('expected_sales', sa.Float(), nullable=False),
        sa.Column('expected_orders', sa.Integer(), nullable=False),
        sa.Column('sales_low', sa.Float(), nullable=False),
        sa.Column('sales_high', sa.Float(), nullable=False),
        sa.Column('confidence_level', sa.Float()),
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
