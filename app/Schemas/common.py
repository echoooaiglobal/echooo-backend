# Create a new file: app/Schemas/common.py
# This will contain reusable schemas across the application

from pydantic import BaseModel
from typing import Optional

class PaginationInfo(BaseModel):
    """Reusable pagination information schema"""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool