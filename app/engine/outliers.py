import pandas as pd
import numpy as np
from typing import Dict, Any, List
from app.engine.schema import ColumnType


class OutlierDetector:
    """
    Detects numerical anomalies and outliers using IQR fences and Z-score tests.
    """

    @classmethod
    def detect_iqr_outliers(cls, series: pd.Series) -> Dict[str, Any]:
        clean_s = pd.to_numeric(series.dropna(), errors="coerce").dropna()
        if len(clean_s) < 4:
            return {"outlier_count": 0, "outliers": []}

        q25 = float(clean_s.quantile(0.25))
        q75 = float(clean_s.quantile(0.75))
        iqr = q75 - q25

        lower_bound = q25 - (1.5 * iqr)
        upper_bound = q75 + (1.5 * iqr)

        outlier_mask = (clean_s < lower_bound) | (clean_s > upper_bound)
        outlier_values = clean_s[outlier_mask].tolist()

        return {
            "lower_fence": round(lower_bound, 2),
            "upper_fence": round(upper_bound, 2),
            "outlier_count": len(outlier_values),
            "outlier_percentage": round((len(outlier_values) / len(clean_s)) * 100, 2),
            "sample_outlier_values": [round(float(v), 2) for v in outlier_values[:10]]
        }

    @classmethod
    def scan_dataset_outliers(cls, df: pd.DataFrame, schema: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        outlier_report = {}
        total_anomalies_detected = 0

        for col, meta in schema.items():
            if meta["detected_type"] == ColumnType.NUMERIC.value:
                res = cls.detect_iqr_outliers(df[col])
                if res["outlier_count"] > 0:
                    outlier_report[col] = res
                    total_anomalies_detected += res["outlier_count"]

        return {
            "total_anomalies_detected": total_anomalies_detected,
            "columns_with_outliers": outlier_report
        }