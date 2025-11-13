#!/usr/bin/env python3
"""
Convert news_capsules.md to a properly formatted PDF
Requirements: pip install reportlab markdown
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re
from datetime import datetime

def parse_markdown_capsules(md_file):
    """Parse the markdown file and extract structured data"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by horizontal rules
    capsules = content.split('---')
    capsules = [c.strip() for c in capsules if c.strip()]
    
    parsed_data = []
    
    for capsule in capsules:
        lines = capsule.split('\n')
        data = {
            'title': '',
            'summary': '',
            'pyq': [],
            'syllabus': []
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Title (starts with ###)
            if line.startswith('###'):
                data['title'] = line.replace('###', '').replace('—', '-').strip()
                current_section = 'summary'
            
            # Section headers
            elif line.startswith('**Relevant PYQ**'):
                current_section = 'pyq'
            elif line.startswith('**Relevant Syllabus**'):
                current_section = 'syllabus'
            
            # List items
            elif line.startswith('-') and current_section in ['pyq', 'syllabus']:
                item = line[1:].strip()
                data[current_section].append(item)
            
            # Summary text
            elif current_section == 'summary' and not line.startswith('**'):
                if data['summary']:
                    data['summary'] += ' ' + line
                else:
                    data['summary'] = line
        
        if data['title']:
            parsed_data.append(data)
    
    return parsed_data

def create_styles():
    """Create custom paragraph styles"""
    styles = getSampleStyleSheet()
    
    # Title style - Large and bold
    styles.add(ParagraphStyle(
        name='CapsuleTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor='#1a1a1a',
        spaceAfter=12,
        spaceBefore=8,
        leading=20,
        fontName='Helvetica-Bold'
    ))
    
    # Summary style
    styles.add(ParagraphStyle(
        name='Summary',
        parent=styles['BodyText'],
        fontSize=11,
        textColor='#2c2c2c',
        spaceAfter=10,
        alignment=TA_JUSTIFY,
        leading=16
    ))
    
    # Section header style (PYQ, Syllabus)
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor='#333333',
        spaceAfter=6,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    ))
    
    # List item style
    styles.add(ParagraphStyle(
        name='ListItem',
        parent=styles['BodyText'],
        fontSize=10,
        textColor='#404040',
        leftIndent=20,
        spaceAfter=6,
        leading=14
    ))
    
    return styles

def create_pdf(input_md, output_pdf):
    """Generate PDF from markdown file"""
    
    # Parse markdown
    capsules = parse_markdown_capsules(input_md)
    
    if not capsules:
        print("No capsules found in markdown file!")
        return
    
    # Create PDF
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = create_styles()
    story = []
    
    # Add header
    header = Paragraph(
        "<b>UPSC News Capsules</b>",
        styles['Title']
    )
    story.append(header)
    
    date_para = Paragraph(
        f"Generated on: {datetime.now().strftime('%d %B %Y')}",
        styles['Normal']
    )
    story.append(date_para)
    story.append(Spacer(1, 0.3*inch))
    
    # Add each capsule
    for idx, capsule in enumerate(capsules):
        # Title
        title = Paragraph(
            f"<b>{capsule['title']}</b>",
            styles['CapsuleTitle']
        )
        story.append(title)
        
        # Summary
        if capsule['summary']:
            summary = Paragraph(capsule['summary'], styles['Summary'])
            story.append(summary)
            story.append(Spacer(1, 0.15*inch))
        
        # PYQ Section
        if capsule['pyq']:
            pyq_header = Paragraph("<b>Relevant PYQ</b>", styles['SectionHeader'])
            story.append(pyq_header)
            
            for item in capsule['pyq']:
                # Clean up formatting
                item = item.replace('**', '')
                bullet = Paragraph(f"• {item}", styles['ListItem'])
                story.append(bullet)
            
            story.append(Spacer(1, 0.1*inch))
        
        # Syllabus Section
        if capsule['syllabus']:
            syl_header = Paragraph("<b>Relevant Syllabus</b>", styles['SectionHeader'])
            story.append(syl_header)
            
            for item in capsule['syllabus']:
                # Clean up formatting
                item = item.replace('**', '')
                bullet = Paragraph(f"• {item}", styles['ListItem'])
                story.append(bullet)
        
        # Add separator between capsules (except for last one)
        if idx < len(capsules) - 1:
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("<hr/>", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
    
    # Build PDF
    doc.build(story)
    print(f"✅ PDF created successfully: {output_pdf}")
    print(f"📊 Total capsules processed: {len(capsules)}")

if __name__ == "__main__":
    input_file = "news_capsules.md"
    output_file = "UPSC_News_Capsules.pdf"
    
    try:
        create_pdf(input_file, output_file)
    except FileNotFoundError:
        print(f"❌ Error: '{input_file}' not found!")
        print("Please ensure the markdown file exists in the same directory.")
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        import traceback
        traceback.print_exc()