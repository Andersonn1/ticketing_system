"""Application Components"""

from .ticket_table.load_table_data import load_mock_tickets
from .ticket_table.ticket_table import ticket_table

__all__ = ["ticket_table", "load_mock_tickets"]
