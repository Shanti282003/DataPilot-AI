from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from app.core.database import Base


class DatasetRecord(Base):
    """
    Stores dataset upload history and cached mathematical profiling reports.
    """
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Key queryable metrics
    rows_count = Column(Integer, nullable=False)
    columns_count = Column(Integer, nullable=False)
    health_score = Column(Integer, nullable=False)
    duplicate_rows = Column(Integer, default=0)

    # Hybrid JSON payloads for full analysis caching
    metadata_json = Column(JSON, nullable=False)
    schema_json = Column(JSON, nullable=False)
    quality_json = Column(JSON, nullable=False)
    stats_json = Column(JSON, nullable=False)
    outliers_json = Column(JSON, nullable=False)
    insights_json = Column(JSON, nullable=False)