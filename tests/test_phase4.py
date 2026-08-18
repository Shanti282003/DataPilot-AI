import json
from app.engine.detector import FileDetector
from app.engine.schema import SchemaClassifier
from app.engine.auditor import DataAuditor
from app.engine.statistics import StatisticsEngine
from app.engine.outliers import OutlierDetector
from app.engine.insights import InsightEngine

# 1. Full Pipeline Execution
with open("data/samples/employees.csv", "rb") as f:
    df, metadata = FileDetector.load_dataframe_from_bytes(f.read(), "employees.csv")

schema = SchemaClassifier.infer_schema(df)
quality = DataAuditor.audit_quality(df)
stats = StatisticsEngine.profile_dataset(df, schema)
outliers = OutlierDetector.scan_dataset_outliers(df, schema)

# 2. Run Insight Engine Fact Compressor
fact_sheet = InsightEngine.generate_llm_fact_sheet(metadata, quality, schema, stats, outliers)

print("\n" + "="*50)
print("🚀 COMPRESSED LLM FACT SHEET (~300 TOKENS):")
print(json.dumps(fact_sheet, indent=2))
print("="*50 + "\n")