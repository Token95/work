import pdfplumber
import os
import re

pdf_path = input("Drop your PDF path here and press enter: ").strip('"')

if not os.path.exists(pdf_path):
    print("[-] Error : File not found. Check the path and try again.")
else:
    with pdfplumber.open(pdf_path) as pdf:
       print(f"\nTotal pages: {len(pdf.pages)}")
       
       # Scan all pages and collect all text
       full_text = ""
       for i, page in enumerate(pdf.pages):
           page_text = page.extract_text() or ""
           full_text += page_text
           print(f"\n--- PAGE {i + 1} ---\n")
           print(page_text)
