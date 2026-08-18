import json
from app.engine.detector import FileDetector
from app.engine.schema import SchemaClassifier
from app.engine.auditor import DataAuditor

# 1. Read raw bytes from our sample CSV
with open("data/samples/employees.csv", "rb") as f:
    file_bytes = f.read()

# 2. Test File Detector
df, metadata = FileDetector.load_dataframe_from_bytes(file_bytes, "employees.csv")
print("\n" + "="*50)
print("📌 FILE METADATA:")
print(json.dumps(metadata, indent=2))

# 3. Test Schema Classifier
schema = SchemaClassifier.infer_schema(df)
print("\n" + "="*50)
print("📌 DETECTED SCHEMA:")
print(json.dumps(schema, indent=2))

# 4. Test Data Auditor
quality = DataAuditor.audit_quality(df)
print("\n" + "="*50)
print("📌 DATA QUALITY AUDIT:")
print(json.dumps(quality, indent=2))
print("="*50 + "\n")