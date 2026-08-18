from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.services.analyzer import AnalyzerService
from app.models.schemas import AnalysisResponseDTO
from app.models.db_models import DatasetRecord
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()


@router.post("/analyze/upload", summary="Upload CSV dataset, analyze, and save to DB")
async def upload_and_analyze(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Accepts CSV file, runs analysis, and saves snapshot to database."""
    valid_extensions = (".csv", ".tsv", ".txt")
    if not file.filename.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format. Please upload CSV/TSV ({valid_extensions})."
        )

    file_bytes = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(status_code=413, detail="File exceeds upload limit.")
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 1. Run deterministic pipeline
    report = AnalyzerService.analyze_file(file_bytes, file.filename)

    # 2. Save snapshot to Database
    record = DatasetRecord(
        filename=report["metadata"]["filename"],
        rows_count=report["quality_audit"]["total_rows"],
        columns_count=report["quality_audit"]["total_columns"],
        health_score=report["quality_audit"]["health_score"],
        duplicate_rows=report["quality_audit"]["duplicate_rows"],
        metadata_json=report["metadata"],
        schema_json=report["schema_definition"],
        quality_json=report["quality_audit"],
        stats_json=report["statistics"],
        outliers_json=report["outliers"],
        insights_json=report["executive_insights"]
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    report["dataset_id"] = record.id
    return report


@router.get("/datasets", summary="List all previously analyzed datasets")
def list_datasets(db: Session = Depends(get_db)):
    """Fetches list of all dataset upload histories."""
    records = db.query(DatasetRecord).order_by(DatasetRecord.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "created_at": r.created_at.isoformat(),
            "rows_count": r.rows_count,
            "columns_count": r.columns_count,
            "health_score": r.health_score,
            "duplicate_rows": r.duplicate_rows
        }
        for r in records
    ]


@router.get("/datasets/{dataset_id}", summary="Get cached analysis report by ID")
def get_dataset_by_id(dataset_id: int, db: Session = Depends(get_db)):
    """Loads a previously computed analysis instantly from DB cache."""
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset record not found.")

    return {
        "dataset_id": record.id,
        "filename": record.filename,
        "created_at": record.created_at.isoformat(),
        "metadata": record.metadata_json,
        "schema_definition": record.schema_json,
        "quality_audit": record.quality_json,
        "statistics": record.stats_json,
        "outliers": record.outliers_json,
        "executive_insights": record.insights_json
    }