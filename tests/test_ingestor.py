import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from modules.ingestor import DocumentIngestor

def test_ingestion():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    files = [
        os.path.join(data_dir, "sample_ai_engineering.docx"),
        os.path.join(data_dir, "sample_cloud_architecture.pptx"),
        os.path.join(data_dir, "sample_python_concurrency.pdf"),
    ]
    
    for f in files:
        assert os.path.exists(f), f"File {f} does not exist"
        res = DocumentIngestor.ingest_file(f)
        print(f"PASS: {res.filename} parsed successfully!")
        print(f"      Type: {res.file_type}, Stats: {res.stats}")
        assert len(res.markdown) > 50, "Markdown content too short"
        assert len(res.sections) > 0, "No sections parsed"
        print(f"      Section count: {len(res.sections)}")

    print("\nALL INGESTION TESTS PASSED SUCCESSFULLY! ✅")

if __name__ == "__main__":
    test_ingestion()
