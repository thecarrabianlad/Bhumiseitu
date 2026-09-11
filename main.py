"""
main.py
-------
A tiny command-line entry point so you can try out P3 without writing
any code yourself.

Usage:
    python main.py examples/english.txt
    python main.py examples/hindi.txt
    python main.py examples/bad_ocr.txt

It just reads the given text file, feeds it into extract_land_record,
and pretty-prints the JSON result.
"""

import json
import sys

from app.extractor import extract_land_record


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <path_to_ocr_text_file>")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        ocr_text = f.read()

    result = extract_land_record(ocr_text)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
