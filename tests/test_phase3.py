import json
from app.engine.detector import FileDetector
from app.engine.schema import SchemaClassifier
from app.engine.statistics import StatisticsEngine
from app.engine.outliers import OutlierDetector

# Load sample
with open("data/samples/employees.csv", "rb") as f:
    df, _ = FileDetector.load_dataframe_from_bytes(f.read(), "employees.csv")

schema = SchemaClassifier.infer_schema(df)

# Run Statistics Profiler
stats = StatisticsEngine.profile_dataset(df, schema)
print("\n" + "="*50)
print("📊 STATISTICAL PROFILE:")
print(json.dumps(stats, indent=2))

# Run Outlier Detector
outliers = OutlierDetector.scan_dataset_outliers(df, schema)
print("\n" + "="*50)
print("🚨 ANOMALY & OUTLIER REPORT:")
print(json.dumps(outliers, indent=2))
print("="*50 + "\n")