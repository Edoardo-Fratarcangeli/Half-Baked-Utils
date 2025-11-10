#  Grep With Powershell 7+

A modern, minimalistic **file text search tool** built with **Python and
Tkinter**, featuring a fully custom interface with a draggable title
bar, dark theme, and smart search features.

------------------------------------------------------------------------

## ✨ Features

-   🗂️ **Search inside files** (supports `.txt`, or text files, `.pdf`, `.docx`, `.xlsx`, and
    others)\
-   🔍 **Highlight matches in red** inside file contents\
-   📚 **Context control:** choose how many lines *before* and *after*
    to show around each match\
-   📁 **Recursive folder search** option\
-   🧩 **Filter by file extensions** (e.g. `.txt, myfile.txt, .pdf`)\
-   🪟 **Custom title bar** with minimize and close buttons\
-   ⚙️ **Lightweight UI** built with pure Tkinter --- no external UI
    frameworks\
-   💾 **Save search results** to a `.txt` file\
-   🧠 **Status bar** showing search progress and summary

------------------------------------------------------------------------

## 🖼️ Screenshot

> Example:\
> ![Preview](docs/preview.jpg)

------------------------------------------------------------------------

## 🚀 How to Run

> Clone the repository, install dependencies and run .py

Or build it by yourself...

``` bash
pyinstaller --noconsole --onefile --icon=icon.ico <NAMEOFPYFILE>.py
```

> Download and run exe

``` bash
bin/GrepWithPowershell.exe
```

------------------------------------------------------------------------

## ⚙️ Configuration

You can modify these settings inside the UI:

  Setting                  Description
  ------------------------ ----------------------------------------
  **Folder Path**          The root directory where to search
  **Search Text**          The keyword or phrase to look for
  **File Extensions**      Filter by extensions (comma-separated)
  **Lines Before/After**   Number of surrounding context lines
  **Case Sensitive**       Match exact case
  **Recursive Search**     Include subfolders

------------------------------------------------------------------------

## 🧠 Technical Overview

-   Built in **Python 3.10+**
-   GUI framework: **Tkinter**
-   PDF parsing: **PyMuPDF (fitz)**
-   Cross-platform: works on Windows, macOS, and Linux

------------------------------------------------------------------------

## 💡 Future Improvements

-   🔎 Regex-based search\
-   🌗 Optional light/dark themes\
-   🪟 Multi-tab interface for multiple searches

------------------------------------------------------------------------

## 🧑‍💻 Author

**Edoardo Fratarcangeli**\
