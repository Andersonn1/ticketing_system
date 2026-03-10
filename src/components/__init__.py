"""Application Components"""

from .ticket_table.ticket_table import ticket_table

# Legacy helper kept for developer workflows; runtime paths should use
# `ServiceTicketService` and should not call `load_mock_tickets` directly.
from .ticket_table.load_table_data import load_mock_tickets

__all__ = ["ticket_table", "load_mock_tickets"]
