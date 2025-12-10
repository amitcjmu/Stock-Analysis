"""
Client CRUD Handler - Modularized Implementation

This module preserves backward compatibility while splitting the original
client_crud_handler.py file into logical components:
- queries.py: Read operations (get, list, stats, conversions)
- commands.py: Write operations (create, update, delete)

All original imports remain functional for backward compatibility.
"""

from .commands import ClientCommandOperations
from .queries import ClientQueryOperations


class ClientCRUDHandler:
    """
    Main handler class that delegates to modularized operations.
    Preserves the original API interface for backward compatibility.
    """

    # Expose query operations as static methods
    get_client = ClientQueryOperations.get_client
    list_clients = ClientQueryOperations.list_clients
    get_dashboard_stats = ClientQueryOperations.get_dashboard_stats
    _convert_client_to_response = ClientQueryOperations._convert_client_to_response

    # Expose command operations as static methods
    create_client = ClientCommandOperations.create_client
    update_client = ClientCommandOperations.update_client
    delete_client = ClientCommandOperations.delete_client
    bulk_delete_clients = ClientCommandOperations.bulk_delete_clients


# Export all public APIs for backward compatibility
__all__ = [
    "ClientCRUDHandler",
    "ClientQueryOperations",
    "ClientCommandOperations",
]
