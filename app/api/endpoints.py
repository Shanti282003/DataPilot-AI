from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.analyzer import AnalyzerService
from app.services.ai_service import AIService
from app.models.db_models import DatasetRecord
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()


class ChatRequestDTO(BaseModel):
    question: str


@router.post("/analyze/upload", summary="Upload CSV dataset, analyze, and save to DB")
async def upload_and_analyze(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    valid_extensions = (".csv", ".tsv", ".txt")
    if not file.filename.lower().endswith(valid_extensions):
        raise HTTPException(status_code=400, detail="Please upload CSV/TSV.")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    report = AnalyzerService.analyze_file(file_bytes, file.filename)

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


@router.post("/datasets/{dataset_id}/summary", summary="Generate AI Executive Summary for dataset")
async def generate_ai_summary(dataset_id: int, db: Session = Depends(get_db)):
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    fact_sheet = {
        "dataset_summary": {
            "file_name": record.filename,
            "total_rows": record.rows_count,
            "total_columns": record.columns_count,
            "health_score": record.health_score,
            "duplicate_rows": record.duplicate_rows
        },
        "schema_overview": {col: meta["detected_type"] for col, meta in record.schema_json.items()},
        "top_prioritized_findings": record.insights_json[:8]
    }

    ai_summary = await AIService.generate_executive_summary(fact_sheet)
    return {"dataset_id": record.id, "summary": ai_summary}


@router.post("/datasets/{dataset_id}/chat", summary="Ask a natural language question about the dataset")
async def ask_dataset_question(
    dataset_id: int,
    payload: ChatRequestDTO,
    db: Session = Depends(get_db)
):
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    context = {
        "quality": record.quality_json,
        "schema": record.schema_json,
        "statistics": record.stats_json,
        "outliers": record.outliers_json
    }

    answer = await AIService.answer_question(payload.question, context)
    return {
        "dataset_id": record.id,
        "question": payload.question,
        "answer": answer
    }