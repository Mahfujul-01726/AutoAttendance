# LaTeX Thesis Compilation Guide

## System-Specific Instructions

### Windows Users

#### Option 1: Using MiKTeX (Easiest for Windows)

1. **Install MiKTeX**
   - Download from: https://miktex.org/download
   - Run the installer (choose "Install MiKTeX for all users" or just you)
   - During installation, select "Yes" for automatic package installation

2. **Compile the Document**
   - Open Command Prompt (cmd.exe)
   - Navigate to your project:
     ```cmd
     cd C:\path\to\AutoAttendance
     ```
   - Run compilation:
     ```cmd
     pdflatex main.tex
     pdflatex main.tex
     ```
   - Your PDF will be in `main.pdf`

3. **Alternative: Using Batch File**
   - Create a file named `compile.bat` in the project folder:
     ```batch
     @echo off
     pdflatex -interaction=nonstopmode main.tex
     pdflatex -interaction=nonstopmode main.tex
     echo.
     echo Compilation complete! Check main.pdf
     pause
     ```
   - Double-click `compile.bat` to run

#### Option 2: Using TeXStudio (GUI Editor)

1. **Download TeXStudio**
   - Visit: https://www.texstudio.org/
   - Download for Windows

2. **Configure TeXStudio**
   - Open TeXStudio
   - Go to Options → Configure TeXStudio
   - Build → PDF Chain: Select "pdflatex"

3. **Compile**
   - Open `main.tex` in TeXStudio
   - Click the green "Build & View" button (or press F5)
   - PDF will open automatically

#### Option 3: Using Overleaf (Online, No Installation)

1. Go to https://www.overleaf.com
2. Sign up (free account available)
3. Create new project → Upload project
4. Upload all files from AutoAttendance folder
5. Overleaf compiles automatically

---

### macOS Users

#### Option 1: Using MacTeX (Recommended)

1. **Install MacTeX**
   - Visit: https://www.tug.org/mactex/
   - Download MacTeX.pkg (about 4GB)
   - Run installer (requires admin password)
   - Installation takes ~15-30 minutes

2. **Compile the Document**
   - Open Terminal (Applications → Utilities → Terminal)
   - Navigate to project:
     ```bash
     cd ~/path/to/AutoAttendance
     ```
   - Run:
     ```bash
     pdflatex main.tex
     pdflatex main.tex
     ```

3. **Using Homebrew (Smaller Installation)**
   ```bash
   brew install mactex
   ```

#### Option 2: Using TeXShop (Included with MacTeX)

1. After installing MacTeX, TeXShop is automatically installed
2. Open TeXShop (Applications → TeX)
3. Open `main.tex` in TeXShop
4. Click "Typeset" button
5. PDF opens automatically in PDF viewer

#### Option 3: Create a Shell Script

Create `compile.sh`:
```bash
#!/bin/bash
cd "$(dirname "$0")"
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
echo "Compilation complete!"
open main.pdf
```

Make executable and run:
```bash
chmod +x compile.sh
./compile.sh
```

---

### Linux Users (Ubuntu/Debian)

#### Option 1: Using TeX Live Package Manager

1. **Install TeX Live**
   ```bash
   sudo apt-get update
   sudo apt-get install texlive-full
   ```
   (This installs all packages - recommended)

   Or minimal installation:
   ```bash
   sudo apt-get install texlive texlive-fonts-recommended
   ```

2. **Compile**
   ```bash
   cd ~/path/to/AutoAttendance
   pdflatex main.tex
   pdflatex main.tex
   ```

#### Option 2: Using Fedora/RHEL

```bash
sudo dnf install texlive-scheme-full
cd ~/path/to/AutoAttendance
pdflatex main.tex
pdflatex main.tex
```

#### Option 3: Create a Make-based Solution

Using the included Makefile:
```bash
cd ~/path/to/AutoAttendance
make pdf        # Compile
make view       # Compile and open
make clean      # Remove temporary files
```

#### Option 4: Using Docker (Advanced)

Create `Dockerfile`:
```dockerfile
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y texlive-full
WORKDIR /thesis
CMD ["bash"]
```

Build and run:
```bash
docker build -t latex-thesis .
docker run -v ~/path/to/AutoAttendance:/thesis latex-thesis
cd /thesis && pdflatex main.tex && pdflatex main.tex
```

---

### All Platforms: Online Solutions

#### Using Overleaf (Easiest - No Installation)

1. Go to https://www.overleaf.com
2. Sign up (free account: 1 project limit; paid: unlimited)
3. Create project → Upload project → Select files
4. Upload all AutoAttendance files
5. Click "Recompile" button
6. Download PDF

**Advantages:**
- No installation required
- Real-time collaboration possible
- Automatic backup
- Works on any device
- Professional PDF output

**Disadvantages:**
- Requires internet connection
- Free tier has project limit

#### Using CoCalc

1. Go to https://cocalc.com/
2. Create account
3. Create new project
4. Upload AutoAttendance files
5. Open Terminal in CoCalc
6. Run compilation commands
7. Download PDF

---

## Detailed Compilation Explanation

### What Happens When You Run pdflatex

First run:
```
pdflatex main.tex
↓
Reads main.tex
↓
Processes \include and \input commands
↓
Reads all chapter files
↓
Builds Table of Contents (stored in .toc file)
↓
Generates main.pdf (with ??? for TOC page numbers)
```

Second run:
```
pdflatex main.tex
↓
Uses .toc file from first run
↓
Generates correct page numbers in TOC
↓
Generates final main.pdf
```

This is why you need to run `pdflatex` twice!

---

## Troubleshooting by Error Message

### Error: "command not found: pdflatex"
**Cause:** LaTeX not installed or not in PATH
**Solution:** 
- Install appropriate LaTeX distribution (see above)
- Restart terminal/command prompt after installation

### Error: "File 'chapter1.tex' not found"
**Cause:** Running pdflatex from wrong directory
**Solution:**
- Ensure you're in the AutoAttendance directory
- Check file names match exactly (case-sensitive on Linux/Mac)

### Error: "Undefined control sequence"
**Cause:** Missing LaTeX package or typo
**Solution:**
- Run pdflatex again (may auto-install on MiKTeX)
- Check for typos in main.tex or chapter files

### Warning: "Underfull hbox"
**Cause:** Text fitting issues (usually harmless)
**Solution:** Usually safe to ignore, or adjust text

### Compilation Takes Very Long
**Cause:** First run with MiKTeX downloading packages
**Solution:** This is normal; subsequent runs are faster

---

## Performance Tips

### Fast Compilation
1. Use `-interaction=nonstopmode` flag:
   ```bash
   pdflatex -interaction=nonstopmode main.tex
   ```

2. Clean temporary files before compiling:
   ```bash
   rm -f *.aux *.log *.out *.toc  # Linux/Mac
   del *.aux *.log *.out *.toc    # Windows
   ```

3. Skip viewing PDF during compilation

### Faster Development Workflow
1. Comment out non-essential chapters in main.tex during editing
2. Use `\documentclass[draft]{book}` for draft mode
3. Disable TOC generation during editing

---

## Verification Checklist

After successful compilation, check:
- [ ] `main.pdf` file exists
- [ ] PDF file size > 500KB
- [ ] PDF opens in reader without errors
- [ ] Title page displays correctly
- [ ] Table of Contents has page numbers
- [ ] All chapters are included
- [ ] Equations render correctly
- [ ] Tables display properly

---

## Next Steps

1. Choose your preferred method from above
2. Follow the installation instructions for your OS
3. Navigate to project directory
4. Run compilation command twice
5. Open and verify `main.pdf`

## Additional Resources

- **Official TeX Live:** https://tug.org/texlive/
- **MiKTeX:** https://miktex.org/
- **Overleaf Tutorials:** https://www.overleaf.com/learn
- **TeX Stack Exchange:** https://tex.stackexchange.com/
- **CTAN Package Search:** https://ctan.org/

---

**Good luck with your LaTeX compilation!**

If you encounter issues not covered here, visit TeX Stack Exchange or Overleaf support.
