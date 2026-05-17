from pathlib import Path
from app.ai.extraction import extract_text

# Base directory -> apps/api
BASE_DIR = Path(__file__).resolve().parent.parent

# Test files (inside apps/api/)
files = [
    (BASE_DIR / "sample.txt", "txt"),
    (BASE_DIR / "sample.pdf", "pdf"),
    (BASE_DIR / "sample.docx", "docx"),
]

for file_path, file_type in files:
    print(f"\n--- Testing {file_path.name} ---")

    # Convert Path -> string (important for your extraction function)
    text = extract_text(str(file_path), file_type)

    if text:
        print("✅ SUCCESS")
        print("Preview:", text[:200])
    else:
        print("❌ FAILED (empty output)")