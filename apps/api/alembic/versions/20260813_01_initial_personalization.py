"""Initial personalization schema.

Revision ID: 20260813_01
Revises:
Create Date: 2026-08-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260813_01"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    diet_type = postgresql.ENUM("OMNIVORE", "VEGETARIAN", "VEGAN", "EGGETARIAN", "PESCATARIAN", "HALAL", "OTHER", name="diet_type", create_type=False)
    postgresql.ENUM("OMNIVORE", "VEGETARIAN", "VEGAN", "EGGETARIAN", "PESCATARIAN", "HALAL", "OTHER", name="diet_type").create(op.get_bind(), checkfirst=True)
    op.create_table("users", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("display_name", sa.String(120), nullable=False), sa.Column("email", sa.String(320), nullable=True, unique=True), sa.Column("country", sa.String(100)), sa.Column("city", sa.String(100)), sa.Column("state_or_region", sa.String(100)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table("food_profiles", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True), sa.Column("diet_type", diet_type, nullable=False), sa.Column("spice_tolerance", sa.Integer(), nullable=False), sa.Column("adventurousness", sa.Integer(), nullable=False), sa.Column("usual_budget_min", sa.Numeric(10,2), nullable=False), sa.Column("usual_budget_max", sa.Numeric(10,2), nullable=False), sa.Column("usual_travel_radius_miles", sa.Numeric(6,2), nullable=False), sa.Column("prefers_delivery", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("prefers_pickup", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("prefers_dine_in", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_food_profiles_user_id", "food_profiles", ["user_id"])
    for table in ("cuisines", "comfort_foods", "allergies"):
        op.create_table(table, sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("name", sa.String(120 if table == "comfort_foods" else 100), nullable=False, unique=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False) if table == "cuisines" else sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
        op.create_index(f"ix_{table}_name", table, ["name"])
    op.create_table("user_cuisine_preferences", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("cuisine_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cuisines.id", ondelete="RESTRICT"), nullable=False), sa.Column("preference_level", sa.Integer(), nullable=False), sa.UniqueConstraint("user_id", "cuisine_id", name="user_cuisine"))
    op.create_table("user_comfort_foods", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("comfort_food_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("comfort_foods.id", ondelete="RESTRICT"), nullable=False), sa.UniqueConstraint("user_id", "comfort_food_id", name="user_comfort_food"))
    op.create_table("user_allergies", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("allergy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("allergies.id", ondelete="RESTRICT"), nullable=False), sa.Column("notes", sa.Text()), sa.UniqueConstraint("user_id", "allergy_id", name="user_allergy"))
    op.create_table("recommendation_interactions", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("restaurant_external_id", sa.String(255), nullable=False), sa.Column("restaurant_name", sa.String(255), nullable=False), sa.Column("cuisine", sa.String(100)), sa.Column("recommended_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("selected", sa.Boolean()), sa.Column("liked", sa.Boolean()), sa.Column("feedback_note", sa.Text()))

def downgrade() -> None:
    for table in ("recommendation_interactions", "user_allergies", "user_comfort_foods", "user_cuisine_preferences", "allergies", "comfort_foods", "cuisines", "food_profiles", "users"):
        op.drop_table(table)
    postgresql.ENUM(name="diet_type", create_type=False).drop(op.get_bind(), checkfirst=True)