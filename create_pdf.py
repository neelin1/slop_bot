from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib import colors

def create_pdf(input_file, output_file):
    # Create basic styles
    styles = getSampleStyleSheet()
    
    # Create custom styles with unique names
    title_style = ParagraphStyle(name='CustomTitle', fontName='Helvetica-Bold', fontSize=16, spaceAfter=12, spaceBefore=6)
    subtitle_style = ParagraphStyle(name='CustomSubtitle', fontName='Helvetica-Bold', fontSize=14, spaceAfter=10, spaceBefore=10)
    body_style = ParagraphStyle(name='CustomBody', fontName='Helvetica', fontSize=11, leading=14, alignment=TA_JUSTIFY, spaceAfter=8)
    list_style = ParagraphStyle(name='CustomList', fontName='Helvetica', fontSize=11, leftIndent=20, spaceAfter=5)

    # Read the input file
    with open(input_file, 'r') as f:
        content = f.read()

    # Process the content
    paragraphs = []
    for block in content.split('\n\n'):
        block = block.strip()
        if block.startswith('## '):
            # Main title
            paragraphs.append(Paragraph(block[3:], title_style))
        elif block.startswith('### '):
            # Subtitle
            paragraphs.append(Paragraph(block[4:], subtitle_style))
        elif block.startswith('- '):
            # List item
            paragraphs.append(Paragraph(block, list_style))
        elif block.startswith('1. ') or block.startswith('2. ') or block.startswith('3. '):
            # Numbered list item
            paragraphs.append(Paragraph(block, list_style))
        else:
            # Normal paragraph
            paragraphs.append(Paragraph(block, body_style))

    # Create the PDF
    doc = SimpleDocTemplate(output_file, pagesize=letter, 
                          rightMargin=72, leftMargin=72, 
                          topMargin=72, bottomMargin=72)
    doc.build(paragraphs)
    print(f'PDF created: {output_file}')

if __name__ == "__main__":
    create_pdf('sample_content.txt', 'quantum_computing.pdf') 