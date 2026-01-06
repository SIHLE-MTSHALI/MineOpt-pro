"""
Report Email Service - Scheduled Report Email Delivery

Provides functionality for:
- Sending scheduled reports via email
- Building report pack PDF bundles
- Managing email templates and recipients
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import os
import json


class EmailStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SCHEDULED = "scheduled"


@dataclass
class EmailRecipient:
    email: str
    name: Optional[str] = None
    role: Optional[str] = None  # e.g., "manager", "operator", "executive"


@dataclass
class ReportSchedule:
    schedule_id: str
    name: str
    report_type: str  # daily_production, weekly_summary, quality_analysis
    cron_expression: str  # e.g., "0 6 * * 1" for weekly Monday 6am
    recipients: List[EmailRecipient]
    enabled: bool = True
    include_attachments: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_sent: Optional[datetime] = None


@dataclass
class EmailDelivery:
    delivery_id: str
    schedule_id: str
    recipients: List[str]
    subject: str
    status: EmailStatus
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    attachment_count: int = 0


class ReportEmailService:
    """Service for sending scheduled reports via email."""
    
    def __init__(self):
        # SMTP configuration from environment
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.example.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_password = os.environ.get("SMTP_PASSWORD", "")
        self.from_email = os.environ.get("REPORT_FROM_EMAIL", "reports@mineopt.local")
        self.from_name = os.environ.get("REPORT_FROM_NAME", "MineOpt Pro Reports")
        
        # In-memory storage for demo
        self._schedules: Dict[str, ReportSchedule] = {}
        self._deliveries: List[EmailDelivery] = []
        
        # Email templates
        self._templates = {
            "daily_production": {
                "subject": "Daily Production Report - {date}",
                "body": """
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <h2 style="color: #1e40af;">Daily Production Report</h2>
                    <p>Date: {date}</p>
                    <h3>Summary</h3>
                    <table style="border-collapse: collapse; width: 100%;">
                        <tr style="background: #f0f0f0;">
                            <th style="padding: 8px; border: 1px solid #ddd;">Metric</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Planned</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Actual</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Variance</th>
                        </tr>
                        {metric_rows}
                    </table>
                    <p style="margin-top: 20px; font-size: 12px; color: #666;">
                        This is an automated report from MineOpt Pro. 
                        Please do not reply to this email.
                    </p>
                </body>
                </html>
                """
            },
            "weekly_summary": {
                "subject": "Weekly Production Summary - Week {week_number}",
                "body": """
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <h2 style="color: #1e40af;">Weekly Production Summary</h2>
                    <p>Week {week_number} ({start_date} - {end_date})</p>
                    {content}
                    <p style="margin-top: 20px; font-size: 12px; color: #666;">
                        This is an automated report from MineOpt Pro.
                    </p>
                </body>
                </html>
                """
            },
            "quality_analysis": {
                "subject": "Quality Analysis Report - {date}",
                "body": """
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <h2 style="color: #1e40af;">Quality Analysis Report</h2>
                    <p>Generated: {date}</p>
                    {content}
                    <h3>Quality Compliance</h3>
                    {compliance_table}
                    <p style="margin-top: 20px; font-size: 12px; color: #666;">
                        This is an automated report from MineOpt Pro.
                    </p>
                </body>
                </html>
                """
            }
        }
    
    def create_schedule(self, schedule: ReportSchedule) -> ReportSchedule:
        """Create a new report schedule."""
        self._schedules[schedule.schedule_id] = schedule
        return schedule
    
    def get_schedule(self, schedule_id: str) -> Optional[ReportSchedule]:
        """Get a report schedule by ID."""
        return self._schedules.get(schedule_id)
    
    def list_schedules(self) -> List[ReportSchedule]:
        """List all report schedules."""
        return list(self._schedules.values())
    
    def update_schedule(self, schedule_id: str, updates: Dict) -> Optional[ReportSchedule]:
        """Update a report schedule."""
        if schedule_id in self._schedules:
            schedule = self._schedules[schedule_id]
            for key, value in updates.items():
                if hasattr(schedule, key):
                    setattr(schedule, key, value)
            return schedule
        return None
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a report schedule."""
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            return True
        return False
    
    def send_report(
        self,
        schedule_id: str,
        report_data: Dict[str, Any],
        attachments: Optional[List[Dict]] = None
    ) -> EmailDelivery:
        """Send a report based on a schedule configuration."""
        import uuid
        
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return EmailDelivery(
                delivery_id=str(uuid.uuid4()),
                schedule_id=schedule_id,
                recipients=[],
                subject="",
                status=EmailStatus.FAILED,
                error_message="Schedule not found"
            )
        
        # Get template
        template = self._templates.get(schedule.report_type, self._templates["daily_production"])
        
        # Format subject and body
        subject = template["subject"].format(**report_data)
        body = template["body"].format(**report_data)
        
        # Prepare recipients
        recipient_emails = [r.email for r in schedule.recipients]
        
        # Create delivery record
        delivery = EmailDelivery(
            delivery_id=str(uuid.uuid4()),
            schedule_id=schedule_id,
            recipients=recipient_emails,
            subject=subject,
            status=EmailStatus.PENDING,
            attachment_count=len(attachments) if attachments else 0
        )
        
        try:
            # Send email (mock for demo)
            self._send_email(recipient_emails, subject, body, attachments)
            delivery.status = EmailStatus.SENT
            delivery.sent_at = datetime.utcnow()
            schedule.last_sent = delivery.sent_at
        except Exception as e:
            delivery.status = EmailStatus.FAILED
            delivery.error_message = str(e)
        
        self._deliveries.append(delivery)
        return delivery
    
    def _send_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        attachments: Optional[List[Dict]] = None
    ):
        """Send an email via SMTP."""
        # In production, this would connect to actual SMTP server
        # For demo, we just log the attempt
        
        if not self.smtp_user:
            # Demo mode - just simulate success
            print(f"[DEMO] Email sent to {recipients}: {subject}")
            return
        
        msg = MIMEMultipart()
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        
        # Add HTML body
        msg.attach(MIMEText(body, "html"))
        
        # Add attachments
        if attachments:
            for attachment in attachments:
                part = MIMEApplication(attachment["content"], Name=attachment["filename"])
                part["Content-Disposition"] = f'attachment; filename="{attachment["filename"]}"'
                msg.attach(part)
        
        # Send via SMTP
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, recipients, msg.as_string())
    
    def get_delivery_history(
        self,
        schedule_id: Optional[str] = None,
        limit: int = 50
    ) -> List[EmailDelivery]:
        """Get email delivery history."""
        deliveries = self._deliveries
        if schedule_id:
            deliveries = [d for d in deliveries if d.schedule_id == schedule_id]
        return sorted(deliveries, key=lambda d: d.sent_at or datetime.min, reverse=True)[:limit]


class ReportPackGenerator:
    """Generate bundled PDF report packs."""
    
    def __init__(self):
        self._report_templates = {
            "production_summary": self._generate_production_summary,
            "quality_report": self._generate_quality_report,
            "equipment_utilization": self._generate_equipment_report,
            "schedule_comparison": self._generate_schedule_comparison
        }
    
    def generate_report_pack(
        self,
        pack_name: str,
        report_types: List[str],
        data: Dict[str, Any],
        date_range: Optional[Dict] = None
    ) -> Dict:
        """
        Generate a bundled PDF report pack containing multiple reports.
        
        Returns metadata about the generated pack.
        """
        import uuid
        
        pack_id = str(uuid.uuid4())
        reports_generated = []
        
        for report_type in report_types:
            if report_type in self._report_templates:
                # Generate individual report
                report = self._report_templates[report_type](data, date_range)
                reports_generated.append({
                    "type": report_type,
                    "title": report["title"],
                    "pages": report["pages"]
                })
        
        # In production, this would use a PDF library like reportlab or weasyprint
        # to actually generate the PDF bundle
        
        return {
            "pack_id": pack_id,
            "pack_name": pack_name,
            "generated_at": datetime.utcnow().isoformat(),
            "reports": reports_generated,
            "total_pages": sum(r["pages"] for r in reports_generated),
            "file_path": f"/reports/{pack_id}/{pack_name.replace(' ', '_')}.pdf",
            "status": "generated"
        }
    
    def _generate_production_summary(self, data: Dict, date_range: Optional[Dict]) -> Dict:
        """Generate production summary report section."""
        return {
            "title": "Production Summary",
            "pages": 3,
            "sections": [
                "Executive Summary",
                "Daily Production Totals",
                "Equipment Performance",
                "Variance Analysis"
            ]
        }
    
    def _generate_quality_report(self, data: Dict, date_range: Optional[Dict]) -> Dict:
        """Generate quality analysis report section."""
        return {
            "title": "Quality Analysis Report",
            "pages": 4,
            "sections": [
                "Quality Overview",
                "CV Analysis",
                "Ash Content Trends",
                "Compliance Status",
                "Recommendations"
            ]
        }
    
    def _generate_equipment_report(self, data: Dict, date_range: Optional[Dict]) -> Dict:
        """Generate equipment utilization report section."""
        return {
            "title": "Equipment Utilization Report",
            "pages": 2,
            "sections": [
                "Fleet Summary",
                "Utilization by Equipment",
                "Maintenance Windows"
            ]
        }
    
    def _generate_schedule_comparison(self, data: Dict, date_range: Optional[Dict]) -> Dict:
        """Generate schedule comparison report section."""
        return {
            "title": "Schedule Comparison",
            "pages": 2,
            "sections": [
                "Planned vs Actual",
                "Scenario Analysis",
                "Key Metrics"
            ]
        }
    
    def get_available_report_types(self) -> List[Dict]:
        """Get list of available report types for pack generation."""
        return [
            {"id": "production_summary", "name": "Production Summary", "description": "Daily/weekly production overview"},
            {"id": "quality_report", "name": "Quality Analysis", "description": "Quality metrics and compliance"},
            {"id": "equipment_utilization", "name": "Equipment Utilization", "description": "Fleet performance and utilization"},
            {"id": "schedule_comparison", "name": "Schedule Comparison", "description": "Plan vs actual analysis"}
        ]


# Global instances
report_email_service = ReportEmailService()
report_pack_generator = ReportPackGenerator()
