"""
Bulk Data Upload and Processing Service

Handles bulk data entry, CSV/Excel uploads, template-based data entry,
and batch processing for manual collection workflows.

Agent Team B3 - Task B3.2
"""

import asyncio
import io
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

import pandas as pd

from ..collection_flow.data_transformation import DataTransformationService
from ..collection_flow.quality_scoring import QualityAssessmentService


class BulkDataFormat(str, Enum):
    """Supported bulk data formats"""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    TSV = "tsv"


class ProcessingStatus(str, Enum):
    """Bulk processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


class ValidationSeverity(str, Enum):
    """Validation issue severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class BulkDataValidationIssue:
    """Individual validation issue in bulk data"""
    row_number: int
    column: str
    field_id: str
    severity: ValidationSeverity
    message: str
    suggested_value: Optional[str] = None
    auto_correctable: bool = False


@dataclass
class BulkDataProcessingResult:
    """Result of bulk data processing operation"""
    upload_id: str
    status: ProcessingStatus
    total_rows: int
    processed_rows: int
    successful_rows: int
    failed_rows: int
    validation_issues: List[BulkDataValidationIssue]
    processing_time_seconds: float
    data_quality_score: float
    created_at: datetime
    completed_at: Optional[datetime] = None


@dataclass
class BulkTemplate:
    """Template for bulk data entry"""
    template_id: str
    name: str
    description: str
    application_types: List[str]
    critical_attributes: List[str]
    column_mappings: Dict[str, str]  # CSV column -> form field mapping
    validation_rules: Dict[str, Any]
    example_data: List[Dict[str, Any]]
    created_at: datetime
    version: str = "1.0"


@dataclass
class GridDataEntry:
    """Individual grid data entry for bulk form"""
    application_id: UUID
    application_name: str
    field_values: Dict[str, Any]
    validation_status: str
    completion_percentage: float
    last_updated: datetime


class BulkDataService:
    """Service for handling bulk data upload and processing operations"""
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Maximum number of rows to process
    MAX_ROWS = 1000
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {
        '.csv': BulkDataFormat.CSV,
        '.xlsx': BulkDataFormat.EXCEL,
        '.xls': BulkDataFormat.EXCEL,
        '.json': BulkDataFormat.JSON,
        '.tsv': BulkDataFormat.TSV
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_transformation_service = DataTransformationService()
        self.quality_service = QualityAssessmentService()
        self._processing_jobs = {}  # In-memory store for demo purposes

    async def upload_bulk_data(
        self,
        file_content: bytes,
        filename: str,
        template_id: Optional[str] = None,
        form_id: str = None
    ) -> BulkDataProcessingResult:
        """
        Upload and process bulk data file.
        
        Core implementation of B3.2 - bulk data upload and processing.
        Supports CSV, Excel, JSON, and TSV formats with validation and transformation.
        """
        upload_id = str(uuid4())
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Processing bulk upload {upload_id} - file: {filename}")
            
            # Validate file
            self._validate_file(file_content, filename)
            
            # Detect format and parse data
            data_format = self._detect_format(filename)
            raw_data = await self._parse_file_content(file_content, data_format)
            
            # Apply template mapping if provided
            if template_id:
                template = await self._get_template(template_id)
                raw_data = self._apply_template_mapping(raw_data, template)
            
            # Validate and transform data
            validation_issues = await self._validate_bulk_data(raw_data, form_id)
            transformed_data = await self._transform_bulk_data(raw_data, validation_issues)
            
            # Calculate processing results
            total_rows = len(raw_data)
            successful_rows = len([row for row in transformed_data if row.get('_validation_status') == 'valid'])
            failed_rows = len([issue for issue in validation_issues if issue.severity == ValidationSeverity.ERROR])
            
            # Calculate data quality score
            quality_score = await self._calculate_bulk_quality_score(transformed_data, validation_issues)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = BulkDataProcessingResult(
                upload_id=upload_id,
                status=ProcessingStatus.COMPLETED if failed_rows == 0 else ProcessingStatus.PARTIALLY_COMPLETED,
                total_rows=total_rows,
                processed_rows=total_rows,
                successful_rows=successful_rows,
                failed_rows=failed_rows,
                validation_issues=validation_issues,
                processing_time_seconds=processing_time,
                data_quality_score=quality_score,
                created_at=start_time,
                completed_at=datetime.now()
            )
            
            # Store results for retrieval
            self._processing_jobs[upload_id] = {
                'result': result,
                'transformed_data': transformed_data
            }
            
            self.logger.info(f"Bulk upload {upload_id} completed - {successful_rows}/{total_rows} rows successful")
            return result
            
        except Exception as e:
            self.logger.error(f"Bulk upload {upload_id} failed: {str(e)}")
            return BulkDataProcessingResult(
                upload_id=upload_id,
                status=ProcessingStatus.FAILED,
                total_rows=0,
                processed_rows=0,
                successful_rows=0,
                failed_rows=0,
                validation_issues=[BulkDataValidationIssue(
                    row_number=0,
                    column="file",
                    field_id="upload",
                    severity=ValidationSeverity.ERROR,
                    message=f"Upload processing failed: {str(e)}"
                )],
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                data_quality_score=0.0,
                created_at=start_time,
                completed_at=datetime.now()
            )

    async def process_grid_data(
        self,
        grid_entries: List[GridDataEntry],
        form_id: str
    ) -> BulkDataProcessingResult:
        """
        Process data from bulk grid interface.
        
        Handles data entered through the bulk grid UI component,
        validating and transforming multiple application entries simultaneously.
        """
        upload_id = f"grid_{uuid4()}"
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Processing grid data {upload_id} - {len(grid_entries)} entries")
            
            # Convert grid entries to standard format
            raw_data = []
            for entry in grid_entries:
                row_data = {
                    'application_id': str(entry.application_id),
                    'application_name': entry.application_name,
                    **entry.field_values
                }
                raw_data.append(row_data)
            
            # Validate grid data
            validation_issues = await self._validate_bulk_data(raw_data, form_id)
            
            # Transform data
            transformed_data = await self._transform_bulk_data(raw_data, validation_issues)
            
            # Calculate results
            total_rows = len(grid_entries)
            successful_rows = len([row for row in transformed_data if row.get('_validation_status') == 'valid'])
            failed_rows = len([issue for issue in validation_issues if issue.severity == ValidationSeverity.ERROR])
            
            quality_score = await self._calculate_bulk_quality_score(transformed_data, validation_issues)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = BulkDataProcessingResult(
                upload_id=upload_id,
                status=ProcessingStatus.COMPLETED if failed_rows == 0 else ProcessingStatus.PARTIALLY_COMPLETED,
                total_rows=total_rows,
                processed_rows=total_rows,
                successful_rows=successful_rows,
                failed_rows=failed_rows,
                validation_issues=validation_issues,
                processing_time_seconds=processing_time,
                data_quality_score=quality_score,
                created_at=start_time,
                completed_at=datetime.now()
            )
            
            self._processing_jobs[upload_id] = {
                'result': result,
                'transformed_data': transformed_data
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Grid processing {upload_id} failed: {str(e)}")
            return BulkDataProcessingResult(
                upload_id=upload_id,
                status=ProcessingStatus.FAILED,
                total_rows=len(grid_entries),
                processed_rows=0,
                successful_rows=0,
                failed_rows=len(grid_entries),
                validation_issues=[],
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                data_quality_score=0.0,
                created_at=start_time,
                completed_at=datetime.now()
            )

    async def generate_bulk_template(
        self,
        critical_attributes: List[str],
        application_types: List[str] = None,
        include_examples: bool = True
    ) -> BulkTemplate:
        """
        Generate a bulk data entry template for specific critical attributes.
        
        Creates CSV/Excel templates with proper column headers, validation rules,
        and example data to guide bulk data entry.
        """
        template_id = f"template_{uuid4()}"
        
        # Define column mappings based on critical attributes
        column_mappings = {}
        validation_rules = {}
        
        # Standard columns always included
        column_mappings['application_name'] = 'Application Name'
        column_mappings['application_id'] = 'Application ID (Optional)'
        
        # Add columns for each critical attribute
        for attr in critical_attributes:
            column_mappings[f'field_{attr}'] = self._get_attribute_label(attr)
            validation_rules[f'field_{attr}'] = self._get_attribute_validation_rules(attr)
        
        # Generate example data if requested
        example_data = []
        if include_examples:
            example_data = self._generate_example_data(critical_attributes, application_types or ['web_application'])
        
        template = BulkTemplate(
            template_id=template_id,
            name=f"Bulk Data Template - {len(critical_attributes)} Attributes",
            description=f"Template for bulk entry of {', '.join(critical_attributes)} attributes",
            application_types=application_types or ['generic'],
            critical_attributes=critical_attributes,
            column_mappings=column_mappings,
            validation_rules=validation_rules,
            example_data=example_data,
            created_at=datetime.now()
        )
        
        self.logger.info(f"Generated bulk template {template_id} for attributes: {critical_attributes}")
        return template

    async def export_template_csv(self, template: BulkTemplate) -> str:
        """Export bulk template as CSV content"""
        
        # Create header row
        headers = list(template.column_mappings.values())
        
        # Create example rows
        rows = []
        for example in template.example_data:
            row = []
            for field_id, header in template.column_mappings.items():
                value = example.get(field_id, '')
                row.append(str(value))
            rows.append(row)
        
        # Generate CSV content
        df = pd.DataFrame(rows, columns=headers)
        csv_content = df.to_csv(index=False)
        
        return csv_content

    async def get_processing_status(self, upload_id: str) -> Optional[BulkDataProcessingResult]:
        """Get the status of a bulk processing job"""
        job = self._processing_jobs.get(upload_id)
        return job['result'] if job else None

    async def get_processed_data(self, upload_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get the processed data from a bulk upload"""
        job = self._processing_jobs.get(upload_id)
        return job['transformed_data'] if job else None

    def _validate_file(self, file_content: bytes, filename: str) -> None:
        """Validate uploaded file"""
        
        # Check file size
        if len(file_content) > self.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum allowed size of {self.MAX_FILE_SIZE / 1024 / 1024}MB")
        
        # Check file extension
        file_path = Path(filename)
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            supported = ', '.join(self.SUPPORTED_EXTENSIONS.keys())
            raise ValueError(f"Unsupported file format. Supported formats: {supported}")

    def _detect_format(self, filename: str) -> BulkDataFormat:
        """Detect file format from filename"""
        file_path = Path(filename)
        return self.SUPPORTED_EXTENSIONS.get(file_path.suffix.lower(), BulkDataFormat.CSV)

    async def _parse_file_content(self, file_content: bytes, data_format: BulkDataFormat) -> List[Dict[str, Any]]:
        """Parse file content based on format"""
        
        try:
            if data_format == BulkDataFormat.CSV:
                df = pd.read_csv(io.BytesIO(file_content))
            elif data_format == BulkDataFormat.TSV:
                df = pd.read_csv(io.BytesIO(file_content), sep='\t')
            elif data_format == BulkDataFormat.EXCEL:
                df = pd.read_excel(io.BytesIO(file_content))
            elif data_format == BulkDataFormat.JSON:
                json_data = json.loads(file_content.decode('utf-8'))
                df = pd.DataFrame(json_data)
            else:
                raise ValueError(f"Unsupported format: {data_format}")
            
            # Validate row count
            if len(df) > self.MAX_ROWS:
                raise ValueError(f"File contains {len(df)} rows, maximum allowed is {self.MAX_ROWS}")
            
            # Convert to list of dictionaries
            return df.to_dict(orient='records')
            
        except Exception as e:
            raise ValueError(f"Failed to parse file content: {str(e)}")

    def _apply_template_mapping(self, raw_data: List[Dict[str, Any]], template: BulkTemplate) -> List[Dict[str, Any]]:
        """Apply template column mappings to raw data"""
        
        mapped_data = []
        reverse_mapping = {v: k for k, v in template.column_mappings.items()}
        
        for row in raw_data:
            mapped_row = {}
            for csv_column, value in row.items():
                if csv_column in reverse_mapping:
                    field_id = reverse_mapping[csv_column]
                    mapped_row[field_id] = value
                else:
                    # Keep unmapped columns as is
                    mapped_row[csv_column] = value
            mapped_data.append(mapped_row)
        
        return mapped_data

    async def _validate_bulk_data(self, data: List[Dict[str, Any]], form_id: str) -> List[BulkDataValidationIssue]:
        """Validate bulk data against form rules"""
        
        validation_issues = []
        
        for row_idx, row in enumerate(data, 1):
            # Check required fields
            if not row.get('application_name'):
                validation_issues.append(BulkDataValidationIssue(
                    row_number=row_idx,
                    column='application_name',
                    field_id='application_name',
                    severity=ValidationSeverity.ERROR,
                    message='Application name is required'
                ))
            
            # Validate each field based on critical attributes
            for field_id, value in row.items():
                if field_id.startswith('field_'):
                    attribute_name = field_id.replace('field_', '')
                    issues = self._validate_attribute_value(attribute_name, value, row_idx, field_id)
                    validation_issues.extend(issues)
        
        return validation_issues

    def _validate_attribute_value(self, attribute_name: str, value: Any, row_number: int, field_id: str) -> List[BulkDataValidationIssue]:
        """Validate a single attribute value"""
        
        issues = []
        
        # Skip validation for empty values (handled by required field validation)
        if not value or str(value).strip() == '':
            return issues
        
        value_str = str(value).strip()
        
        # Attribute-specific validation
        if attribute_name == 'os_version':
            valid_os = ['windows_server_2019', 'windows_server_2016', 'ubuntu_20.04', 'rhel_8', 'centos_7']
            if value_str.lower() not in [os.lower() for os in valid_os]:
                issues.append(BulkDataValidationIssue(
                    row_number=row_number,
                    column=field_id,
                    field_id=field_id,
                    severity=ValidationSeverity.WARNING,
                    message=f'Unrecognized OS version: {value_str}',
                    suggested_value='Please verify the OS version format'
                ))
        
        elif attribute_name == 'business_criticality':
            valid_criticality = ['mission_critical', 'business_critical', 'important', 'standard', 'low']
            if value_str.lower() not in valid_criticality:
                issues.append(BulkDataValidationIssue(
                    row_number=row_number,
                    column=field_id,
                    field_id=field_id,
                    severity=ValidationSeverity.ERROR,
                    message=f'Invalid business criticality: {value_str}',
                    suggested_value='Must be one of: mission_critical, business_critical, important, standard, low'
                ))
        
        elif attribute_name in ['specifications', 'integration_dependencies', 'data_characteristics']:
            # These fields should have substantial content
            if len(value_str) < 20:
                issues.append(BulkDataValidationIssue(
                    row_number=row_number,
                    column=field_id,
                    field_id=field_id,
                    severity=ValidationSeverity.WARNING,
                    message='Field appears to have insufficient detail (less than 20 characters)',
                    suggested_value='Please provide more detailed information'
                ))
        
        return issues

    async def _transform_bulk_data(self, data: List[Dict[str, Any]], validation_issues: List[BulkDataValidationIssue]) -> List[Dict[str, Any]]:
        """Transform and normalize bulk data"""
        
        transformed_data = []
        error_rows = {issue.row_number for issue in validation_issues if issue.severity == ValidationSeverity.ERROR}
        
        for row_idx, row in enumerate(data, 1):
            transformed_row = row.copy()
            
            # Add validation status
            if row_idx in error_rows:
                transformed_row['_validation_status'] = 'invalid'
            else:
                transformed_row['_validation_status'] = 'valid'
            
            # Normalize data using data transformation service
            transformed_row = await self.data_transformation_service.normalize_collected_data(transformed_row)
            
            # Add metadata
            transformed_row['_row_number'] = row_idx
            transformed_row['_processed_at'] = datetime.now().isoformat()
            
            transformed_data.append(transformed_row)
        
        return transformed_data

    async def _calculate_bulk_quality_score(self, transformed_data: List[Dict[str, Any]], validation_issues: List[BulkDataValidationIssue]) -> float:
        """Calculate overall quality score for bulk data"""
        
        if not transformed_data:
            return 0.0
        
        # Base score from validation
        total_rows = len(transformed_data)
        error_count = len([issue for issue in validation_issues if issue.severity == ValidationSeverity.ERROR])
        warning_count = len([issue for issue in validation_issues if issue.severity == ValidationSeverity.WARNING])
        
        validation_score = max(0.0, 1.0 - (error_count * 0.5 + warning_count * 0.1) / total_rows)
        
        # Completeness score
        valid_rows = len([row for row in transformed_data if row.get('_validation_status') == 'valid'])
        completeness_score = valid_rows / total_rows if total_rows > 0 else 0.0
        
        # Calculate weighted final score
        final_score = (validation_score * 0.6 + completeness_score * 0.4)
        
        return min(1.0, max(0.0, final_score))

    async def _get_template(self, template_id: str) -> BulkTemplate:
        """Retrieve bulk template by ID"""
        # For now, return a default template - in production this would query the database
        return BulkTemplate(
            template_id=template_id,
            name="Default Template",
            description="Default bulk data template",
            application_types=["generic"],
            critical_attributes=["technology_stack", "business_criticality"],
            column_mappings={
                "application_name": "Application Name",
                "field_technology_stack": "Technology Stack",
                "field_business_criticality": "Business Criticality"
            },
            validation_rules={},
            example_data=[],
            created_at=datetime.now()
        )

    def _get_attribute_label(self, attribute_name: str) -> str:
        """Get user-friendly label for critical attribute"""
        labels = {
            'os_version': 'Operating System & Version',
            'technology_stack': 'Technology Stack',
            'business_criticality': 'Business Criticality',
            'architecture_pattern': 'Architecture Pattern',
            'integration_dependencies': 'Integration Dependencies',
            'security_requirements': 'Security Requirements',
            'compliance_constraints': 'Compliance Requirements'
        }
        return labels.get(attribute_name, attribute_name.replace('_', ' ').title())

    def _get_attribute_validation_rules(self, attribute_name: str) -> Dict[str, Any]:
        """Get validation rules for critical attribute"""
        return {
            'required': True,
            'type': 'string',
            'min_length': 1 if attribute_name in ['os_version', 'business_criticality'] else 10
        }

    def _generate_example_data(self, critical_attributes: List[str], application_types: List[str]) -> List[Dict[str, Any]]:
        """Generate example data for template"""
        
        examples = []
        
        # Generate 3 example rows
        for i in range(3):
            example = {
                'application_name': f'Example Application {i+1}',
                'application_id': f'app-{i+1:03d}'
            }
            
            for attr in critical_attributes:
                if attr == 'os_version':
                    example[f'field_{attr}'] = ['windows_server_2019', 'ubuntu_20.04', 'rhel_8'][i]
                elif attr == 'technology_stack':
                    example[f'field_{attr}'] = ['Java, Spring Boot, Oracle', 'Python, Django, PostgreSQL', '.NET Core, SQL Server'][i]
                elif attr == 'business_criticality':
                    example[f'field_{attr}'] = ['mission_critical', 'business_critical', 'important'][i]
                elif attr == 'architecture_pattern':
                    example[f'field_{attr}'] = ['monolith', 'microservices', 'layered'][i]
                else:
                    example[f'field_{attr}'] = f'Example {attr.replace("_", " ")} value for application {i+1}'
            
            examples.append(example)
        
        return examples