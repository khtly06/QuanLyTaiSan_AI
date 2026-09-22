"""Database models package."""

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

from app.models.asset import Asset
from app.models.category import Category
from app.models.department import Department
from app.models.disposal import Disposal
from app.models.inventory import Inventory, InventoryDetail
from app.models.repair import Repair
from app.models.transfer import Transfer
from app.models.user import User

__all__ = [
    "db",
    "Asset",
    "Category",
    "Department",
    "Disposal",
    "Inventory",
    "InventoryDetail",
    "Repair",
    "Transfer",
    "User",
]
