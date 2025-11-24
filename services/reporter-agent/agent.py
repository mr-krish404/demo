"""
Reporter Agent - Generates comprehensive penetration testing reports
"""
import os
import sys
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from jinja2 import Template

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from shared.database import DatabaseManager, Project, Finding, Evidence
from shared.config import settings
from shared.storage import StorageManager

class ReporterAgent:
    """Generates penetration testing reports"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(settings.database_url)
        self.storage_manager = StorageManager()
    
    def execute(self, project_id: str, format: str = 'pdf'):
        """Generate report for a project"""
        session = next(self.db_manager.get_session())
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if not project:
                print(f"Project {project_id} not found")
                return
            
            findings = session.query(Finding).filter(Finding.project_id == project_id).all()
            
            print(f"Generating {format} report for project: {project.name}")
            
            if format == 'pdf':
                report_path = self.generate_pdf_report(project, findings)
            elif format == 'html':
                report_path = self.generate_html_report(project, findings)
            else:
                print(f"Unsupported format: {format}")
                return
            
            # Upload report to storage
            with open(report_path, 'rb') as f:
                storage_key = f"reports/{project_id}/report_{datetime.utcnow().isoformat()}.{format}"
                self.storage_manager.upload_file(storage_key, f, os.path.getsize(report_path))
            
            print(f"Report generated and uploaded: {storage_key}")
        
        except Exception as e:
            print(f"Error generating report: {e}")
        finally:
            session.close()
    
    def generate_pdf_report(self, project: Project, findings: List[Finding]) -> str:
        """Generate PDF report"""
        filename = f"/tmp/report_{project.id}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"<b>Penetration Testing Report</b><br/>{project.name}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Executive Summary
        story.append(Paragraph("<b>Executive Summary</b>", styles['Heading1']))
        summary_text = f"""
        This report presents the findings from the automated penetration testing assessment 
        of {project.name}. The assessment was conducted using Apex Pentest X platform.
        <br/><br/>
        Total Findings: {len(findings)}<br/>
        Critical: {sum(1 for f in findings if f.severity.value == 'critical')}<br/>
        High: {sum(1 for f in findings if f.severity.value == 'high')}<br/>
        Medium: {sum(1 for f in findings if f.severity.value == 'medium')}<br/>
        Low: {sum(1 for f in findings if f.severity.value == 'low')}<br/>
        Info: {sum(1 for f in findings if f.severity.value == 'info')}
        """
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Findings
        story.append(PageBreak())
        story.append(Paragraph("<b>Detailed Findings</b>", styles['Heading1']))
        
        for i, finding in enumerate(findings, 1):
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>Finding {i}: {finding.title}</b>", styles['Heading2']))
            story.append(Paragraph(f"<b>Severity:</b> {finding.severity.value.upper()}", styles['Normal']))
            story.append(Paragraph(f"<b>Confidence:</b> {finding.confidence * 100:.1f}%", styles['Normal']))
            story.append(Paragraph(f"<b>Status:</b> {finding.status.value}", styles['Normal']))
            
            if finding.affected_url:
                story.append(Paragraph(f"<b>Affected URL:</b> {finding.affected_url}", styles['Normal']))
            
            story.append(Paragraph(f"<b>Description:</b>", styles['Normal']))
            story.append(Paragraph(finding.description, styles['Normal']))
            
            if finding.remediation:
                story.append(Paragraph(f"<b>Remediation:</b>", styles['Normal']))
                story.append(Paragraph(finding.remediation, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        return filename
    
    def generate_html_report(self, project: Project, findings: List[Finding]) -> str:
        """Generate HTML report"""
        filename = f"/tmp/report_{project.id}.html"
        
        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Penetration Testing Report - {{ project.name }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                .finding { border: 1px solid #ddd; padding: 20px; margin: 20px 0; }
                .critical { border-left: 5px solid #d32f2f; }
                .high { border-left: 5px solid #f57c00; }
                .medium { border-left: 5px solid #fbc02d; }
                .low { border-left: 5px solid #388e3c; }
                .info { border-left: 5px solid #1976d2; }
                .severity { font-weight: bold; text-transform: uppercase; }
            </style>
        </head>
        <body>
            <h1>Penetration Testing Report</h1>
            <h2>{{ project.name }}</h2>
            
            <h3>Executive Summary</h3>
            <p>Total Findings: {{ findings|length }}</p>
            <ul>
                <li>Critical: {{ findings|selectattr('severity.value', 'equalto', 'critical')|list|length }}</li>
                <li>High: {{ findings|selectattr('severity.value', 'equalto', 'high')|list|length }}</li>
                <li>Medium: {{ findings|selectattr('severity.value', 'equalto', 'medium')|list|length }}</li>
                <li>Low: {{ findings|selectattr('severity.value', 'equalto', 'low')|list|length }}</li>
                <li>Info: {{ findings|selectattr('severity.value', 'equalto', 'info')|list|length }}</li>
            </ul>
            
            <h3>Detailed Findings</h3>
            {% for finding in findings %}
            <div class="finding {{ finding.severity.value }}">
                <h4>{{ loop.index }}. {{ finding.title }}</h4>
                <p><span class="severity">Severity: {{ finding.severity.value }}</span></p>
                <p><strong>Confidence:</strong> {{ (finding.confidence * 100)|round(1) }}%</p>
                <p><strong>Status:</strong> {{ finding.status.value }}</p>
                {% if finding.affected_url %}
                <p><strong>Affected URL:</strong> {{ finding.affected_url }}</p>
                {% endif %}
                <p><strong>Description:</strong></p>
                <p>{{ finding.description }}</p>
                {% if finding.remediation %}
                <p><strong>Remediation:</strong></p>
                <p>{{ finding.remediation }}</p>
                {% endif %}
            </div>
            {% endfor %}
        </body>
        </html>
        """
        
        template = Template(template_str)
        html_content = template.render(project=project, findings=findings)
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename

def main():
    """Main entry point"""
    project_id = os.getenv("PROJECT_ID")
    format = os.getenv("FORMAT", "pdf")
    
    if not project_id:
        print("No PROJECT_ID provided")
        return
    
    agent = ReporterAgent()
    agent.execute(project_id, format)

if __name__ == "__main__":
    main()
