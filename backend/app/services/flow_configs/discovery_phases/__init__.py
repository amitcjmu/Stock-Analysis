"""Discovery flow phase configurations"""

from .asset_inventory_phase import get_asset_inventory_phase
from .data_cleansing_phase import get_data_cleansing_phase
from .data_import_phase import get_data_import_phase
from .data_validation_phase import get_data_validation_phase
from .field_mapping_phase import get_field_mapping_phase

__all__ = [
    "get_data_import_phase",
    "get_data_validation_phase",
    "get_field_mapping_phase",
    "get_data_cleansing_phase",
    "get_asset_inventory_phase",
]
