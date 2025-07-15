"""
Data Import API Examples - Python Client Implementation.

This file provides complete working examples for all data import API endpoints.
"""

import requests
import json
import base64
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
import time


class DataImportClient:
    """Client for interacting with the Data Import API."""
    
    def __init__(self, base_url: str, token: str, client_id: str, engagement_id: str):
        """
        Initialize the Data Import API client.
        
        Args:
            base_url: API base URL (e.g., "https://api.yourdomain.com")
            token: Bearer authentication token
            client_id: Client account ID
            engagement_id: Engagement ID
        """
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {token}",
            "X-Client-Account-ID": client_id,
            "X-Engagement-ID": engagement_id,
            "Content-Type": "application/json"
        }
    
    def import_csv_file(self, file_path: str, import_type: str) -> Dict[str, Any]:
        """
        Import a CSV file from disk.
        
        Args:
            file_path: Path to the CSV file
            import_type: Type of import (servers, applications, etc.)
            
        Returns:
            API response containing import ID and flow ID
        """
        # Read and parse CSV file
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        # Get file metadata
        import os
        file_stats = os.stat(file_path)
        
        # Prepare request
        request_data = {
            "file_data": data,
            "metadata": {
                "filename": os.path.basename(file_path),
                "size": file_stats.st_size,
                "type": "text/csv"
            },
            "upload_context": {
                "intended_type": import_type,
                "upload_timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        # Send request
        response = requests.post(
            f"{self.base_url}/api/v1/data-import/store-import",
            headers=self.headers,
            json=request_data
        )
        
        response.raise_for_status()
        return response.json()
    
    def import_data_direct(self, data: List[Dict[str, Any]], filename: str, import_type: str) -> Dict[str, Any]:
        """
        Import data directly without reading from file.
        
        Args:
            data: List of dictionaries representing CSV rows
            filename: Filename for tracking
            import_type: Type of import
            
        Returns:
            API response
        """
        request_data = {
            "file_data": data,
            "metadata": {
                "filename": filename,
                "size": len(json.dumps(data).encode('utf-8')),
                "type": "text/csv"
            },
            "upload_context": {
                "intended_type": import_type,
                "upload_timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/data-import/store-import",
            headers=self.headers,
            json=request_data
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_import_status(self, import_id: str) -> Dict[str, Any]:
        """Get the status of an import operation."""
        response = requests.get(
            f"{self.base_url}/api/v1/data-import/import/{import_id}/status",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_latest_import(self) -> Dict[str, Any]:
        """Get the most recent import for the current context."""
        response = requests.get(
            f"{self.base_url}/api/v1/data-import/latest-import",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_import_completion(self, import_id: str, timeout: int = 300) -> Dict[str, Any]:
        """
        Wait for an import to complete with polling.
        
        Args:
            import_id: Import ID to monitor
            timeout: Maximum wait time in seconds
            
        Returns:
            Final import status
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_import_status(import_id)
            
            if status["import_status"]["status"] in ["completed", "failed"]:
                return status
            
            # Wait before next poll
            time.sleep(5)
        
        raise TimeoutError(f"Import {import_id} did not complete within {timeout} seconds")
    
    def cancel_import(self, import_id: str) -> Dict[str, Any]:
        """Cancel an ongoing import operation."""
        response = requests.delete(
            f"{self.base_url}/api/v1/data-import/import/{import_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def retry_failed_import(self, import_id: str) -> Dict[str, Any]:
        """Retry a failed import operation."""
        response = requests.post(
            f"{self.base_url}/api/v1/data-import/import/{import_id}/retry",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


# Example Usage
def main():
    """Demonstrate usage of the Data Import API client."""
    
    # Initialize client
    client = DataImportClient(
        base_url="https://api.yourdomain.com",
        token="your-bearer-token",
        client_id="1",
        engagement_id="1"
    )
    
    # Example 1: Import server data directly
    print("Example 1: Direct Server Data Import")
    print("-" * 50)
    
    server_data = [
        {
            "server_name": "prod-web-01",
            "ip_address": "10.0.1.10",
            "os": "Ubuntu 20.04",
            "cpu_cores": 8,
            "memory_gb": 16,
            "storage_gb": 500,
            "environment": "production",
            "business_unit": "Sales",
            "application": "Web Portal"
        },
        {
            "server_name": "prod-db-01",
            "ip_address": "10.0.1.20",
            "os": "RHEL 8",
            "cpu_cores": 16,
            "memory_gb": 64,
            "storage_gb": 2000,
            "environment": "production",
            "business_unit": "Sales",
            "application": "Customer Database"
        },
        {
            "server_name": "dev-app-01",
            "ip_address": "10.0.2.10",
            "os": "CentOS 7",
            "cpu_cores": 4,
            "memory_gb": 8,
            "storage_gb": 200,
            "environment": "development",
            "business_unit": "Engineering",
            "application": "API Service"
        }
    ]
    
    try:
        result = client.import_data_direct(
            data=server_data,
            filename="servers_inventory.csv",
            import_type="servers"
        )
        print(f"Import successful!")
        print(f"Import ID: {result['data_import_id']}")
        print(f"Flow ID: {result['flow_id']}")
        print(f"Total Records: {result['total_records']}")
        print()
        
        # Wait for completion
        print("Waiting for import to complete...")
        final_status = client.wait_for_import_completion(result['data_import_id'])
        print(f"Import completed with status: {final_status['import_status']['status']}")
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            print("Error: An incomplete discovery flow already exists")
            error_detail = e.response.json()
            print(f"Existing flow: {error_detail.get('existing_flow', {}).get('flow_id')}")
            print("Recommendations:")
            for rec in error_detail.get('recommendations', []):
                print(f"  - {rec}")
        else:
            print(f"HTTP Error: {e}")
    
    print()
    
    # Example 2: Import from CSV file
    print("Example 2: Import from CSV File")
    print("-" * 50)
    
    # Create a sample CSV file
    csv_content = """app_name,version,server_name,technology_stack,criticality
CustomerPortal,2.3.4,prod-web-01,Java Spring Boot,High
InventoryAPI,1.8.2,prod-app-01,Python FastAPI,Medium
AnalyticsEngine,3.0.1,prod-analytics-01,Apache Spark,High
MobileBackend,1.5.0,prod-mobile-01,Node.js,Medium
PaymentGateway,2.1.0,prod-payment-01,Java Spring,Critical"""
    
    with open("applications.csv", "w") as f:
        f.write(csv_content)
    
    try:
        result = client.import_csv_file(
            file_path="applications.csv",
            import_type="applications"
        )
        print(f"Applications import successful!")
        print(f"Import ID: {result['data_import_id']}")
        
    except Exception as e:
        print(f"Error importing applications: {e}")
    
    print()
    
    # Example 3: Check import status
    print("Example 3: Check Import Status")
    print("-" * 50)
    
    try:
        latest = client.get_latest_import()
        if latest['success'] and latest['import_metadata']:
            import_id = latest['import_metadata']['import_id']
            status = client.get_import_status(import_id)
            print(f"Import ID: {import_id}")
            print(f"Status: {status['import_status']['status']}")
            print(f"Progress: {status['import_status'].get('progress', 0)}%")
            print(f"Current Phase: {status['import_status'].get('current_phase', 'Unknown')}")
    except Exception as e:
        print(f"Error checking status: {e}")
    
    print()
    
    # Example 4: Error handling for validation errors
    print("Example 4: Handling Validation Errors")
    print("-" * 50)
    
    invalid_data = [
        {
            "server_name": "",  # Invalid: empty server name
            "ip_address": "not-an-ip",  # Invalid: bad IP format
            "os": "Ubuntu 20.04"
        }
    ]
    
    try:
        result = client.import_data_direct(
            data=invalid_data,
            filename="invalid_servers.csv",
            import_type="servers"
        )
    except requests.exceptions.HTTPError as e:
        print(f"Expected validation error: {e.response.status_code}")
        print(f"Error details: {e.response.json()}")
    
    print()
    
    # Example 5: Batch import with progress monitoring
    print("Example 5: Batch Import with Progress Monitoring")
    print("-" * 50)
    
    # Generate larger dataset
    large_dataset = []
    for i in range(100):
        large_dataset.append({
            "server_name": f"server-{i:03d}",
            "ip_address": f"10.0.{i // 256}.{i % 256}",
            "os": "Ubuntu 20.04" if i % 2 == 0 else "RHEL 8",
            "cpu_cores": 4 + (i % 4) * 4,
            "memory_gb": 8 + (i % 8) * 8,
            "storage_gb": 100 + (i % 10) * 100
        })
    
    try:
        result = client.import_data_direct(
            data=large_dataset,
            filename="large_server_inventory.csv",
            import_type="servers"
        )
        
        import_id = result['data_import_id']
        print(f"Large import started: {import_id}")
        
        # Monitor progress
        while True:
            status = client.get_import_status(import_id)
            current_status = status['import_status']['status']
            progress = status['import_status'].get('progress', 0)
            
            print(f"\rProgress: {progress}% - Status: {current_status}", end="")
            
            if current_status in ["completed", "failed"]:
                print()  # New line
                break
            
            time.sleep(2)
        
        print(f"Final status: {current_status}")
        
    except Exception as e:
        print(f"Error in batch import: {e}")


if __name__ == "__main__":
    main()