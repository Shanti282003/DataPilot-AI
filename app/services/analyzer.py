import pandas as pd
from typing import Dict, Any
from app.engine.detector import FileDetector
from app.engine.schema import SchemaClassifier
from app.engine.auditor import DataAuditor
from app.engine.statistics import StatisticsEngine
from app.engine.outliers import OutlierDetector
from app.engine.insights import InsightEngine


class AnalyzerService:
    """
    Coordinates the entire deterministic data analysis pipeline.
    """

    @classmethod
    def analyze_file(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        # 1. Detect & Load DataFrame
        df, metadata = FileDetector.load_dataframe_from_bytes(file_bytes, filename)

        # 2. Dynamic Schema Inference
        schema = SchemaClassifier.infer_schema(df)

        # 3. Data Quality Audit
        quality = DataAuditor.audit_quality(df)

        # 4. Statistical Profiling
        stats = StatisticsEngine.profile_dataset(df, schema)

        # 5. Outlier Detection
        outliers = OutlierDetector.scan_dataset_outliers(df, schema)

        # 6. Rule Evaluation & Facts Compression
        insights = InsightEngine.evaluate_rules(metadata, quality, schema, stats, outliers)
        fact_sheet = InsightEngine.generate_llm_fact_sheet(metadata, quality, schema, stats, outliers)

        return {
            "success": True,
            "metadata": metadata,
            "schema_definition": schema,
            "quality_audit": quality,
            "statistics": stats,
            "outliers": outliers,
            "fact_sheet": fact_sheet,
            "executive_insights": insights
        }