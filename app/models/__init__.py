"""
SQLAlchemy models package.

Importing this module ensures all models are registered with the
declarative Base so that Alembic auto-generates migrations correctly.
"""

from app.models.user import User             # noqa: F401
from app.models.property import Property      # noqa: F401
from app.models.property_image import PropertyImage  # noqa: F401
from app.models.connection import Connection  # noqa: F401
from app.models.review import Review          # noqa: F401
