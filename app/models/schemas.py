from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class FileMetadataDTO(BaseModel):
    filename: str
    encoding: str
    delimiter: str
    raw_size_bytes: int
    rows_loaded: int
    columns_loaded: int


class DataQualityDTO(BaseModel):
    total_rows: int
    total_columns: int
    total_cells: int
    total_missing_cells: int
    duplicate_rows: int
    duplicate_percentage: float
    health_score: int
    columns_audit: Dict[str, Any]
    warnings: List[str]


class AnalysisResponseDTO(BaseModel):
    success: bool = True
    metadata: FileMetadataDTO
    schema_definition: Dict[str, Any]
    quality_audit: DataQualityDTO
    statistics: Dict[str, Any]
    outliers: Dict[str, Any]
    fact_sheet: Dict[str, Any]
    executive_insights: List[Dict[str, Any]]