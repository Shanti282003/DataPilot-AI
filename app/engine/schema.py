import pandas as pd
import numpy as np
from enum import Enum
from typing import Dict, Any, List


class ColumnType(str, Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    IDENTIFIER = "identifier"
    TEXT = "text"


class SchemaClassifier:
    """
    Infers the semantic data type of each column in a DataFrame.
    """

    @classmethod
    def infer_column_type(cls, series: pd.Series) -> ColumnType:
        # Drop null values for inspection
        non_null_series = series.dropna()
        if len(non_null_series) == 0:
            return ColumnType.TEXT

        # 1. Check for Boolean
        if pd.api.types.is_bool_dtype(series):
            return ColumnType.BOOLEAN

        unique_vals = set(non_null_series.astype(str).str.lower().unique())
        if unique_vals.issubset({"true", "false", "1", "0", "yes", "no", "t", "f"}):
            return ColumnType.BOOLEAN

        # 2. Check for Unique Identifier (High uniqueness ratio + ID keywords)
        total_rows = len(series)
        unique_count = series.nunique()
        col_name = str(series.name).lower()
        is_id_name = any(kw in col_name for kw in ["id", "uuid", "guid", "code", "key", "pk"])

        if (unique_count == total_rows or (unique_count / total_rows > 0.95)) and is_id_name:
            return ColumnType.IDENTIFIER

        # 3. Check for Numeric
        if pd.api.types.is_numeric_dtype(series):
            # If numeric but only has 2-5 distinct integer values, could be categorical
            if unique_count <= 5 and total_rows > 50:
                return ColumnType.CATEGORICAL
            return ColumnType.NUMERIC

        # 4. Check for Datetime (Try parsing a sample)
        if pd.api.types.is_datetime64_any_dtype(series):
            return ColumnType.DATETIME

        # Sample test for date strings (YYYY-MM-DD, etc.)
        sample_values = non_null_series.astype(str).head(20)
        try:
            pd.to_datetime(sample_values, format="mixed")
            # If 80%+ of non-null values parse as date, mark as datetime
            return ColumnType.DATETIME
        except (ValueError, TypeError, OverflowError):
            pass

        # 5. Check for Categorical vs Freeform Text
        # If unique values are small relative to total rows, it's categorical (e.g. Department, Gender)
        cardinality_ratio = unique_count / total_rows if total_rows > 0 else 1.0
        avg_str_len = non_null_series.astype(str).str.len().mean()

        if unique_count <= 50 or cardinality_ratio < 0.2:
            return ColumnType.CATEGORICAL
        elif avg_str_len > 100:
            return ColumnType.TEXT

        return ColumnType.CATEGORICAL

    @classmethod
    def infer_schema(cls, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Scans all columns and returns a structured schema definition.
        """
        schema_map = {}
        for col in df.columns:
            col_type = cls.infer_column_type(df[col])
            schema_map[col] = {
                "detected_type": col_type.value,
                "pandas_dtype": str(df[col].dtype),
                "unique_count": int(df[col].nunique()),
                "sample_values": df[col].dropna().head(3).tolist()
            }
        return schema_map