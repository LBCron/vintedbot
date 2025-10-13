import csv
import json
from io import StringIO, BytesIO
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from backend.models.schemas import Item


class ExportService:
    def export_csv(self, items: List[Item]) -> str:
        output = StringIO()
        if not items:
            return ""
        
        fieldnames = ['id', 'title', 'brand', 'size', 'category', 'condition', 'price', 'status', 'created_at']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in items:
            writer.writerow({
                'id': item.id,
                'title': item.title,
                'brand': item.brand or '',
                'size': item.size or '',
                'category': item.category or '',
                'condition': item.condition.value if item.condition else '',
                'price': item.price,
                'status': item.status.value,
                'created_at': item.created_at.isoformat() if item.created_at else ''
            })
        
        return output.getvalue()
    
    def export_vinted_csv(self, items: List[Item]) -> str:
        output = StringIO()
        if not items:
            return ""
        
        fieldnames = ['titre', 'description', 'prix', 'categorie', 'taille', 'etat', 'marque']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in items:
            condition_map = {
                'new_with_tags': 'Neuf avec étiquette',
                'new_without_tags': 'Neuf sans étiquette',
                'very_good': 'Très bon état',
                'good': 'Bon état',
                'satisfactory': 'Satisfaisant'
            }
            
            writer.writerow({
                'titre': item.title,
                'description': item.description,
                'prix': item.price,
                'categorie': item.category or '',
                'taille': item.size or '',
                'etat': condition_map.get(item.condition.value, '') if item.condition else '',
                'marque': item.brand or ''
            })
        
        return output.getvalue()
    
    def export_json(self, items: List[Item]) -> str:
        items_dict = [item.model_dump(mode='json') for item in items]
        return json.dumps(items_dict, indent=2, default=str)
    
    def export_pdf(self, items: List[Item]) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
        )
        
        title = Paragraph("Inventaire des Articles", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.3 * inch))
        
        if not items:
            no_items = Paragraph("Aucun article dans l'inventaire", styles['Normal'])
            elements.append(no_items)
        else:
            data = [['Titre', 'Marque', 'Taille', 'Prix', 'État']]
            
            for item in items:
                data.append([
                    item.title[:40],
                    item.brand or 'N/A',
                    item.size or 'N/A',
                    f"{item.price}€",
                    item.status.value
                ])
            
            table = Table(data, colWidths=[3*inch, 1.5*inch, 0.8*inch, 0.8*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            
            elements.append(table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


export_service = ExportService()
