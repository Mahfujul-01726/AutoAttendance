# Makefile for LaTeX thesis compilation

.PHONY: all clean pdf view help

# Default target
all: pdf

# Generate PDF
pdf:
	pdflatex -interaction=nonstopmode main.tex
	pdflatex -interaction=nonstopmode main.tex

# Clean up temporary files
clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot *.fdb_latexmk *.fls
	rm -f *.synctex.gz *.auxlock

# Clean all including PDF
distclean: clean
	rm -f main.pdf

# View PDF (Linux/Mac)
view: pdf
	@command -v xdg-open >/dev/null 2>&1 && xdg-open main.pdf || open main.pdf

# Help
help:
	@echo "Available targets:"
	@echo "  make pdf        - Generate PDF (default)"
	@echo "  make clean      - Remove temporary files"
	@echo "  make distclean  - Remove all generated files including PDF"
	@echo "  make view       - Generate PDF and open it"
	@echo "  make help       - Show this help message"
