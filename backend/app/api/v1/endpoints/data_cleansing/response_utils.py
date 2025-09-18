"""
Streaming Response Utilities for Data Cleansing Exports
Functions for creating and configuring streaming CSV responses.
"""

import io
from fastapi.responses import StreamingResponse


def create_csv_streaming_response(csv_content: str, filename: str) -> StreamingResponse:
    """Create a streaming response for CSV content.

    Args:
        csv_content: The CSV content as string
        filename: The filename for the download

    Returns:
        StreamingResponse configured for CSV download
    """
    # Convert CSV content to bytes and create stream
    csv_bytes = csv_content.encode("utf-8")
    csv_stream = io.BytesIO(csv_bytes)
    csv_stream.seek(0)

    # Return CSV as streaming response with headers for browser compatibility
    return StreamingResponse(
        csv_stream,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(len(csv_bytes)),
            "Cache-Control": "no-cache",
            "Content-Type": "text/csv; charset=utf-8",
        },
    )


def create_empty_csv_response(
    flow_id: str, export_type: str = "cleaned"
) -> StreamingResponse:
    """Create empty CSV response when no data is available.

    Args:
        flow_id: The flow identifier for filename generation
        export_type: Type of export ('raw' or 'cleaned') for filename

    Returns:
        StreamingResponse for empty CSV file
    """
    from .csv_utils import create_empty_csv_content, generate_filename

    csv_content = create_empty_csv_content(flow_id, export_type)
    filename = generate_filename(flow_id, export_type, is_empty=True)

    return create_csv_streaming_response(csv_content, filename)
