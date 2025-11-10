import os
import PyPDF2
from docx import Document
import openpyxl

# ------------------------------
# File-specific search functions
# ------------------------------
def search_pdf(file_path, search_text, case_sensitive, lines_before=2, lines_after=2):
    matches = []
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if not text:
                    continue
                lines = text.replace("\r", "\n").split("\n")
                if len(lines) < 3:
                    lines = text.split(". ")
                for i, line in enumerate(lines):
                    line_to_search = line if case_sensitive else line.lower()
                    search_to_find = search_text if case_sensitive else search_text.lower()
                    if search_to_find in line_to_search:
                        start = max(0, i - lines_before)
                        end = min(len(lines), i + lines_after + 1)
                        context = "\n".join(lines[start:end])
                        matches.append((page_num, context))
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
    return matches

def search_docx(file_path, search_text, case_sensitive, lines_before=2, lines_after=2):
    matches = []
    try:
        doc = Document(file_path)
        all_lines = [para.text for para in doc.paragraphs]
        for i, line in enumerate(all_lines):
            line_to_search = line if case_sensitive else line.lower()
            search_to_find = search_text if case_sensitive else search_text.lower()
            if search_to_find in line_to_search:
                start = max(0, i - lines_before)
                end = min(len(all_lines), i + lines_after + 1)
                context = "\n".join(all_lines[start:end])
                matches.append((i + 1, context))
    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
    return matches

def search_xlsx(file_path, search_text, case_sensitive):
    matches = []
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        for sheet in wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                for cell in row:
                    if cell is None:
                        continue
                    cell_str = str(cell)
                    cell_to_search = cell_str if case_sensitive else cell_str.lower()
                    search_to_find = search_text if case_sensitive else search_text.lower()
                    if search_to_find in cell_to_search:
                        matches.append((sheet.title, cell_str))
    except Exception as e:
        print(f"Error reading XLSX {file_path}: {e}")
    return matches

# ------------------------------
# Generic searcher function
# ------------------------------
def searcher(folder, search_text, extensions="*", case_sensitive=False, recursive=True, lines_before=2, lines_after=2, stop_flag=None):
    """
    Search text in multiple file types inside a folder (with optional recursion).
    Returns a list of results:
        [(file_path, [(line_or_page, context), ...]), ...]
    
    - extensions: comma-separated list (e.g. ".txt,.py,.pdf,.docx,.xlsx") or "*" for all
    - stop_flag: optional mutable object (e.g. dict) to stop search externally: {'stop': True}
    """
    if extensions == "*" or extensions == "":
        ext_list = None
    else:
        ext_list = [("." + ext.strip().lstrip(".")).lower() for ext in extensions.split(",") if ext.strip()]

    results = []
    total_files = 0
    total_matches = 0

    for root_dir, _, files in os.walk(folder):
        if stop_flag and stop_flag.get('stop'):
            break
        for filename in files:
            if stop_flag and stop_flag.get('stop'):
                break
            if ext_list and not any(filename.lower().endswith(ext) for ext in ext_list):
                continue
            file_path = os.path.join(root_dir, filename)
            total_files += 1
            matches = []

            if filename.lower().endswith('.pdf'):
                matches = search_pdf(file_path, search_text, case_sensitive, lines_before, lines_after)
            elif filename.lower().endswith('.docx'):
                matches = search_docx(file_path, search_text, case_sensitive, lines_before, lines_after)
            elif filename.lower().endswith('.xlsx'):
                matches = search_xlsx(file_path, search_text, case_sensitive)
            else:
                # Plain text files
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            line_to_search = line if case_sensitive else line.lower()
                            search_to_find = search_text if case_sensitive else search_text.lower()
                            if search_to_find in line_to_search:
                                start = max(0, i - lines_before)
                                end = min(len(lines), i + lines_after + 1)
                                context = "".join(lines[start:end]).strip()
                                matches.append((i + 1, context))
                except Exception as e:
                    print(f"Cannot open {file_path}: {e}")

            if matches:
                total_matches += len(matches)
                results.append((file_path, matches))

        if not recursive:
            break

    return results, total_files, total_matches
