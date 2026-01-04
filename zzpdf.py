from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName

# Step 1: Create a base PDF with ReportLab
base_pdf = "base.pdf"
c = canvas.Canvas(base_pdf, pagesize=letter)
c.drawString(100, 750, "Name:")
c.save()

# Step 2: Add a form field using pdfrw
pdf = PdfReader(base_pdf)
annotation = PdfDict(
    FT=PdfName('Tx'),                      # Text field
    Type=PdfName('Annot'),
    Subtype=PdfName('Widget'),
    Rect=[150, 735, 350, 755],             # x1, y1, x2, y2
    T='Name',                              # Field name
    V='',                                  # Default value
    Ff=0,                                  # Flags
    DA='/Helv 12 Tf 0 g'                   # Default appearance
)

# Attach field to the page and document
pdf.Root.AcroForm = PdfDict(Fields=[annotation])
pdf.pages[0].Annots = [annotation]

# Write final PDF
PdfWriter().write("form.pdf", pdf)
