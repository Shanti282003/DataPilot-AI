from typing import Dict, Any, List
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INSIGHT = "insight"
    INFO = "info"


class InsightEngine:
    """
    Evaluates computed dataset statistics, ranks business findings by severity,
    and compresses them into a lightweight fact-sheet for LLM synthesis.
    """

    @classmethod
    def evaluate_rules(
        cls,
        metadata: Dict[str, Any],
        quality: Dict[str, Any],
        schema: Dict[str, Any],
        stats: Dict[str, Any],
        outliers: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []

        # 1. Health Score & Data Quality Rules
        health_score = quality.get("health_score", 100)
        if health_score < 70:
            insights.append({
                "severity": Severity.CRITICAL.value,
                "category": "Data Quality",
                "title": "Low Dataset Health Score",
                "detail": f"Overall dataset health is {health_score}/100. Significant missing or duplicate records detected.",
                "importance_score": 95
            })

        # Duplicate Rows Check
        dup_pct = quality.get("duplicate_percentage", 0)
        if dup_pct > 0:
            insights.append({
                "severity": Severity.WARNING.value if dup_pct > 5 else Severity.INFO.value,
                "category": "Data Quality",
                "title": "Duplicate Records Present",
                "detail": f"Detected {quality.get('duplicate_rows')} duplicate rows ({dup_pct}% of dataset).",
                "importance_score": 75 if dup_pct > 5 else 40
            })

        # Missing Column Audit Rules
        for col, col_audit in quality.get("columns_audit", {}).items():
            miss_pct = col_audit.get("missing_percentage", 0)
            if miss_pct > 30:
                insights.append({
                    "severity": Severity.CRITICAL.value,
                    "category": "Completeness",
                    "title": f"High Missing Ratio in '{col}'",
                    "detail": f"Column '{col}' is missing {miss_pct}% of its values ({col_audit.get('missing_count')} nulls).",
                    "importance_score": 90
                })
            elif miss_pct > 10:
                insights.append({
                    "severity": Severity.WARNING.value,
                    "category": "Completeness",
                    "title": f"Moderate Missing Data in '{col}'",
                    "detail": f"Column '{col}' has {miss_pct}% missing values.",
                    "importance_score": 60
                })

        # 2. Outlier & Anomaly Rules
        for col, out_info in outliers.get("columns_with_outliers", {}).items():
            count = out_info.get("outlier_count", 0)
            pct = out_info.get("outlier_percentage", 0)
            samples = out_info.get("sample_outlier_values", [])
            insights.append({
                "severity": Severity.WARNING.value if pct > 5 else Severity.INSIGHT.value,
                "category": "Anomaly Detection",
                "title": f"Numerical Outliers in '{col}'",
                "detail": f"Found {count} anomalous values (e.g. {samples}) outside IQR fences [{out_info.get('lower_fence')}, {out_info.get('upper_fence')}].",
                "importance_score": 85
            })

        # 3. High Correlation Rules
        corrs = stats.get("correlations", {})
        processed_pairs = set()
        for col1, relations in corrs.items():
            for col2, r_val in relations.items():
                if col1 != col2 and (col2, col1) not in processed_pairs:
                    processed_pairs.add((col1, col2))
                    if abs(r_val) >= 0.7:
                        direction = "strong positive" if r_val > 0 else "strong negative"
                        insights.append({
                            "severity": Severity.INSIGHT.value,
                            "category": "Correlation",
                            "title": f"Strong Correlation: {col1} & {col2}",
                            "detail": f"Pearson r = {r_val} ({direction} linear relationship).",
                            "importance_score": 70
                        })

        # 4. Key Numeric Distributions (Mean vs Median Skewness)
        for col, col_data in stats.get("columns", {}).items():
            if col_data.get("type") == "numeric":
                num_s = col_data.get("statistics", {})
                mean = num_s.get("mean")
                median = num_s.get("median")
                skew = num_s.get("skewness", 0)
                if mean and median and abs(skew) > 1.5:
                    skew_dir = "right (positively)" if skew > 0 else "left (negatively)"
                    insights.append({
                        "severity": Severity.INFO.value,
                        "category": "Distribution",
                        "title": f"Skewed Distribution in '{col}'",
                        "detail": f"Mean (${mean}) is significantly different from Median (${median}), skewed {skew_dir}.",
                        "importance_score": 50
                    })

        # Sort all findings by importance score (Highest priority first)
        insights.sort(key=lambda x: x["importance_score"], reverse=True)
        return insights

    @classmethod
    def generate_llm_fact_sheet(
        cls,
        metadata: Dict[str, Any],
        quality: Dict[str, Any],
        schema: Dict[str, Any],
        stats: Dict[str, Any],
        outliers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Creates the ultra-compact ~300-token Fact Sheet ready for LLM consumption.
        """
        ranked_insights = cls.evaluate_rules(metadata, quality, schema, stats, outliers)

        fact_sheet = {
            "dataset_summary": {
                "file_name": metadata.get("filename"),
                "total_rows": quality.get("total_rows"),
                "total_columns": quality.get("total_columns"),
                "health_score": quality.get("health_score"),
                "duplicate_rows": quality.get("duplicate_rows")
            },
            "schema_overview": {col: info["detected_type"] for col, info in schema.items()},
            "top_prioritized_findings": ranked_insights[:8]  # Top 8 highest-importance facts
        }

        return fact_sheet