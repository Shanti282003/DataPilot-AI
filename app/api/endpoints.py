from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.services.analyzer import AnalyzerService
from app.models.schemas import AnalysisResponseDTO
from app.core.config import settings

router = APIRouter()


@router.post("/analyze/upload", response_model=AnalysisResponseDTO, summary="Upload CSV dataset for automated profiling")
async def upload_and_analyze(file: UploadFile = File(...)):
    """
    Accepts CSV/TSV file upload, validates format & size, and returns
    complete deterministic mathematical analysis.
    """
    # 1. Validate file extension
    valid_extensions = (".csv", ".tsv", ".txt")
    if not file.filename.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Please upload a CSV or TSV file ({valid_extensions})."
        )

    # 2. Read bytes safely
    file_bytes = await file.read()

    # 3. Validate size limit (Prevent RAM exhaustion)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum upload size limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )

    # 4. Run Analysis Pipeline
    try:
        report = AnalyzerService.analyze_file(file_bytes, file.filename)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing dataset: {str(e)}"
        )


@router.get("/analyze/sample", response_model=AnalysisResponseDTO, summary="Run analysis on built-in sample employees dataset")
def analyze_sample():
    """Test endpoint that runs analysis on the built-in employees.csv sample."""
    sample_path = "data/samples/employees.csv"
    try:
        with open(sample_path, "rb") as f:
            file_bytes = f.read()
        return AnalyzerService.analyze_file(file_bytes, "employees.csv")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Sample file not found on server.")