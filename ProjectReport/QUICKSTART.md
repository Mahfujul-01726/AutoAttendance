# Quick Start Guide - LaTeX Thesis Compilation

## Prerequisites Installation

### Windows

1. **Download MiKTeX**
   - Visit: https://miktex.org/download
   - Download MiKTeX installer
   - Run the installer and follow instructions
   - MiKTeX will automatically download required packages on first use

2. **Optional: Download TeXStudio (Editor)**
   - Visit: https://www.texstudio.org/
   - Download and install TeXStudio

### macOS

1. **Using Homebrew (recommended)**
   ```bash
   brew install mactex
   ```

2. **Or download MacTeX**
   - Visit: https://www.tug.org/mactex/
   - Download and run the installer

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install texlive-full
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install texlive-scheme-full
```

## Compilation Methods

### Method 1: Using Command Line

1. Open terminal/command prompt
2. Navigate to the thesis directory:
   ```bash
   cd path/to/AutoAttendance
   ```
3. Run compilation:
   ```bash
   pdflatex main.tex
   pdflatex main.tex
   ```
4. Output file: `main.pdf`

### Method 2: Using Makefile (Linux/Mac)

```bash
cd path/to/AutoAttendance
make pdf          # Compile to PDF
make view         # Compile and open PDF
make clean        # Remove temporary files
```

### Method 3: Using TeXStudio

1. Open TeXStudio
2. Click "File" → "Open" and select `main.tex`
3. Click the "Build & View" button (or press F5)
4. PDF will open automatically

### Method 4: Using Overleaf (Online)

1. Go to https://www.overleaf.com
2. Create a new project
3. Upload all files from the AutoAttendance folder
4. Overleaf will automatically compile and display the PDF

### Method 5: Using Online LaTeX Compilers

- https://www.overleaf.com (Recommended)
- https://www.cocalc.com (Google Colab alternative)
- https://repl.it (Simple online editor)

## Troubleshooting

### Problem: "Command not found: pdflatex"

**Solution:** LaTeX is not installed or not in system PATH
- Install LaTeX distribution (see Prerequisites section)
- Restart terminal/command prompt after installation

### Problem: Undefined control sequence

**Solution:** Missing LaTeX package
- MiKTeX (Windows): Will auto-install missing packages
- Other systems: May need manual installation

### Problem: File not found

**Solution:** Ensure you're in correct directory
```bash
cd /path/to/AutoAttendance
ls -la  # or "dir" on Windows to verify files exist
```

### Problem: TOC shows page numbers as "??"

**Solution:** This is normal - run pdflatex twice:
```bash
pdflatex main.tex
pdflatex main.tex
```

### Problem: Bibliography entries not showing

**Solution:** 
```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Project Structure

```
AutoAttendance/
├── main.tex                 # Main file - START HERE
├── chapters/
│   ├── chapter1.tex        # Introduction
│   ├── chapter2.tex        # Literature Review
│   ├── chapter3.tex        # Related Studies
│   ├── chapter4.tex        # Methodology
│   ├── chapter5.tex        # Results
│   ├── chapter6.tex        # Conclusion
│   ├── abstract.tex
│   └── declaration.tex
├── Makefile                # Compilation helper (Linux/Mac)
└── README.md
```

## Customization Tips

### Change Line Spacing

In `main.tex`, modify:
```latex
\onehalfspacing    % for 1.5 spacing
\doublespacing     % for double spacing
\singlespacing     % for single spacing
```

### Add Custom Packages

In the preamble of `main.tex`:
```latex
\usepackage{your-package}
```

### Modify Margins

```latex
\usepackage[margin=1.25in]{geometry}  % Adjust values as needed
```

## Useful Resources

- Overleaf Tutorials: https://www.overleaf.com/learn
- CTAN (Packages): https://ctan.org/
- TeX Stack Exchange: https://tex.stackexchange.com/

## File Generation Timeline

When you run pdflatex, it generates:
- `.pdf` - Your final PDF document
- `.aux` - Auxiliary information
- `.log` - Compilation log
- `.toc` - Table of contents data
- `.lof` - List of figures data
- `.lot` - List of tables data

You can safely delete these temporary files after getting your PDF.

## Support

For LaTeX questions, visit:
- https://tex.stackexchange.com/
- https://www.overleaf.com/learn

## Next Steps

1. ✅ Install LaTeX (see Prerequisites)
2. ✅ Verify installation: `pdflatex --version`
3. ✅ Navigate to AutoAttendance folder
4. ✅ Run: `pdflatex main.tex` twice
5. ✅ Open generated `main.pdf`

Good luck with your thesis!
