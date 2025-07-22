"""
GCP Adapter Utilities

Common utility functions used across the GCP adapter.
"""

from typing import Any, Dict


def proto_to_dict(proto_message) -> Dict[str, Any]:
    """Convert protobuf message to dictionary"""
    try:
        from google.protobuf.json_format import MessageToDict
        return MessageToDict(proto_message, preserving_proto_field_name=True)
    except Exception:
        return {}
        

def extract_resource_name(resource_name: str) -> str:
    """Extract display name from GCP resource name"""
    if "/" in resource_name:
        return resource_name.split("/")[-1]
    return resource_name