import pandas as pd
from typing import Dict, Any, List


class DataAuditor:
    """
    Audits dataset completeness, duplicates, and calculates an overall Data Health Score.
    """

    @classmethod
    def audit_quality(cls, df: pd.DataFrame) -> Dict[str, Any]:
        total_rows = len(df)
        total_cols = len(df.columns)

        if total_rows == 0:
            return {
                "total_rows": 0,
                "total_columns": total_cols,
                "duplicate_rows": 0,
                "duplicate_percentage": 0.0,
                "health_score": 0,
                "columns_audit": {},
                "warnings": ["Dataset is completely empty."]
            }

        # 1. Duplicate Rows Check
        duplicate_rows_count = int(df.duplicated().sum())
        duplicate_pct = round((duplicate_rows_count / total_rows) * 100, 2)

        # 2. Missing Values Check Per Column
        columns_audit = {}
        total_missing_cells = 0
        total_cells = total_rows * total_cols
        warnings: List[str] = []

        for col in df.columns:
            missing_count = int(df[col].isnull().sum())
            total_missing_cells += missing_count
            missing_pct = round((missing_count / total_rows) * 100, 2)

            columns_audit[col] = {
                "missing_count": missing_count,
                "missing_percentage": missing_pct,
                "is_completely_empty": missing_count == total_rows
            }

            # Generate Warning rules
            if missing_pct > 50:
                warnings.append(f"Column '{col}' has {missing_pct}% missing values (High Severity).")
            elif missing_pct > 20:
                warnings.append(f"Column '{col}' has {missing_pct}% missing values (Moderate Severity).")

        if duplicate_pct > 5:
            warnings.append(f"Dataset has {duplicate_pct}% duplicate rows ({duplicate_rows_count} rows).")

        # 3. Calculate Overall Data Health Score (0 - 100)
        # Weighted: 70% Completeness + 30% Uniqueness
        completeness_score = max(0.0, (1 - (total_missing_cells / total_cells))) * 100 if total_cells > 0 else 0
        uniqueness_score = max(0.0, (1 - (duplicate_rows_count / total_rows))) * 100 if total_rows > 0 else 0

        health_score = int(round((completeness_score * 0.7) + (uniqueness_score * 0.3)))

        return {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "total_cells": total_cells,
            "total_missing_cells": total_missing_cells,
            "duplicate_rows": duplicate_rows_count,
            "duplicate_percentage": duplicate_pct,
            "health_score": health_score,
            "columns_audit": columns_audit,
            "warnings": warnings
        }