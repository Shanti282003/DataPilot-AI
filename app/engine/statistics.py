import pandas as pd
import numpy as np
from typing import Dict, Any
from app.engine.schema import ColumnType, SchemaClassifier


class StatisticsEngine:
    """
    Computes rigorous deterministic mathematical statistics for datasets.
    """

    @classmethod
    def calculate_numeric_stats(cls, series: pd.Series) -> Dict[str, Any]:
        clean_s = pd.to_numeric(series.dropna(), errors="coerce").dropna()
        if len(clean_s) == 0:
            return {}

        q25 = float(clean_s.quantile(0.25))
        median = float(clean_s.median())
        q75 = float(clean_s.quantile(0.75))
        std_val = float(clean_s.std()) if len(clean_s) > 1 else 0.0
        skew_val = float(clean_s.skew()) if len(clean_s) > 2 else 0.0

        return {
            "count": int(len(clean_s)),
            "mean": round(float(clean_s.mean()), 2),
            "median": round(median, 2),
            "std": round(std_val, 2),
            "min": round(float(clean_s.min()), 2),
            "max": round(float(clean_s.max()), 2),
            "q25": round(q25, 2),
            "q75": round(q75, 2),
            "iqr": round(q75 - q25, 2),
            "skewness": round(skew_val, 2)
        }

    @classmethod
    def calculate_categorical_stats(cls, series: pd.Series) -> Dict[str, Any]:
        clean_s = series.dropna().astype(str)
        if len(clean_s) == 0:
            return {}

        value_counts = clean_s.value_counts()
        total_valid = len(clean_s)

        top_categories = [
            {"value": str(val), "count": int(count), "percentage": round((count / total_valid) * 100, 2)}
            for val, count in value_counts.head(5).items()
        ]

        mode_val = str(value_counts.index[0]) if len(value_counts) > 0 else None

        return {
            "distinct_count": int(clean_s.nunique()),
            "mode": mode_val,
            "top_categories": top_categories
        }

    @classmethod
    def calculate_correlation_matrix(cls, df: pd.DataFrame, schema: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        numeric_cols = [col for col, meta in schema.items() if meta["detected_type"] == ColumnType.NUMERIC.value]
        if len(numeric_cols) < 2:
            return {}

        num_df = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
        corr = num_df.corr(method="pearson").round(2).fillna(0.0)

        # Convert to nested dictionary for clean JSON representation
        return corr.to_dict()

    @classmethod
    def profile_dataset(cls, df: pd.DataFrame, schema: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        column_summaries = {}

        for col, meta in schema.items():
            col_type = meta["detected_type"]

            if col_type == ColumnType.NUMERIC.value:
                column_summaries[col] = {
                    "type": col_type,
                    "statistics": cls.calculate_numeric_stats(df[col])
                }
            elif col_type in (ColumnType.CATEGORICAL.value, ColumnType.BOOLEAN.value):
                column_summaries[col] = {
                    "type": col_type,
                    "statistics": cls.calculate_categorical_stats(df[col])
                }
            else:
                column_summaries[col] = {
                    "type": col_type,
                    "statistics": {"non_null_count": int(df[col].dropna().count())}
                }

        correlations = cls.calculate_correlation_matrix(df, schema)

        return {
            "columns": column_summaries,
            "correlations": correlations
        }