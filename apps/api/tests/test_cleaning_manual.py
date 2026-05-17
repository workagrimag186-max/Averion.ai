from app.ai.cleaning import clean_text

test_cases = [
    None,
    "",
    "Hello     world",
    "Line1\n\n\n\nLine2",
    "----\nImportant content\n****",
    "   Leading and trailing spaces   ",
    "Text\twith\ttabs",
    "Normal text.\n\nAnother paragraph."
]

for i, text in enumerate(test_cases):
    print(f"\n--- Test Case {i+1} ---")
    cleaned = clean_text(text)
    
    print("Original:", repr(text))
    print("Cleaned :", repr(cleaned))