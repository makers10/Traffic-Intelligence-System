"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "traffic_readings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("junction_id", sa.String, nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column("speed_kmh", sa.Float, nullable=False),
        sa.Column("vehicle_density", sa.Integer, nullable=False),
        sa.Column("occupancy_pct", sa.Float),
        sa.Column("weather_condition", sa.String),
        sa.Column("temperature", sa.Float),
        sa.Column("visibility_m", sa.Float),
        sa.Column("raw_data", sa.JSON),
    )
    op.create_table(
        "congestion_predictions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("junction_id", sa.String, nullable=False, index=True),
        sa.Column("predicted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("forecast_time", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("congestion_level", sa.Float, nullable=False),
        sa.Column("predicted_speed", sa.Float),
        sa.Column("confidence", sa.Float),
        sa.Column("model_version", sa.String, default="v1"),
    )
    op.create_table(
        "accident_alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("junction_id", sa.String, nullable=False, index=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("severity", sa.String, nullable=False),
        sa.Column("speed_drop_pct", sa.Float),
        sa.Column("density_spike_pct", sa.Float),
        sa.Column("is_confirmed", sa.Boolean, default=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.String),
    )
    op.create_table(
        "weather_snapshots",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("junction_id", sa.String, nullable=False, index=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column("condition", sa.String),
        sa.Column("temperature", sa.Float),
        sa.Column("humidity", sa.Float),
        sa.Column("wind_speed", sa.Float),
        sa.Column("visibility_m", sa.Float),
        sa.Column("precipitation_mm", sa.Float),
        sa.Column("impact_score", sa.Float),
    )
    op.create_table(
        "traffic_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("event_type", sa.String, nullable=False),
        sa.Column("junction_id", sa.String, index=True),
        sa.Column("location", sa.String),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("expected_attendance", sa.Integer),
        sa.Column("impact_radius_km", sa.Float, default=2.0),
        sa.Column("impact_score", sa.Float),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("source", sa.String, default="manual"),
    )
    op.create_table(
        "signal_plans",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("junction_id", sa.String, nullable=False, index=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("congestion_level", sa.Float),
        sa.Column("green_duration_s", sa.Integer),
        sa.Column("red_duration_s", sa.Integer),
        sa.Column("cycle_time_s", sa.Integer),
        sa.Column("phases", sa.JSON),
        sa.Column("reason", sa.String),
    )
    op.create_table(
        "transport_readings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("junction_id", sa.String, nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column("rideshare_trips", sa.Integer, default=0),
        sa.Column("rideshare_avg_wait_min", sa.Float),
        sa.Column("metro_boardings", sa.Integer, default=0),
        sa.Column("bus_boardings", sa.Integer, default=0),
        sa.Column("road_pressure_index", sa.Float),
        sa.Column("transit_shift_score", sa.Float),
    )


def downgrade() -> None:
    for table in ["transport_readings", "signal_plans", "traffic_events",
                  "weather_snapshots", "accident_alerts", "congestion_predictions", "traffic_readings"]:
        op.drop_table(table)
