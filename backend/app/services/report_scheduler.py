"""
Report Scheduling Service

Provides automatic report generation scheduling:
- Cron-style scheduling
- Email delivery
- Report queue management
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class ScheduleFrequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ON_DEMAND = "on_demand"


@dataclass
class ScheduledReport:
    """A scheduled report configuration."""
    schedule_id: str
    name: str
    report_type: str  # daily_summary, shift_plan, etc.
    schedule_version_id: str
    frequency: ScheduleFrequency
    delivery_emails: List[str]
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    options: Dict = field(default_factory=dict)
    
    # Timing options
    run_hour: int = 6  # Default 6 AM
    run_day_of_week: int = 0  # Monday for weekly
    run_day_of_month: int = 1  # First of month for monthly


@dataclass
class ReportDelivery:
    """Record of a report delivery."""
    delivery_id: str
    schedule_id: str
    report_type: str
    generated_at: datetime
    delivered_to: List[str]
    status: str  # success, failed
    error_message: Optional[str] = None
    file_path: Optional[str] = None


class ReportScheduler:
    """
    Manages scheduled report generation and delivery.
    """
    
    def __init__(self, report_generator=None, email_sender=None):
        self._schedules: Dict[str, ScheduledReport] = {}
        self._deliveries: List[ReportDelivery] = []
        self._report_generator = report_generator
        self._email_sender = email_sender
        self._running = False
        self._task = None
    
    # =========================================================================
    # Schedule Management
    # =========================================================================
    
    def create_schedule(
        self,
        schedule_id: str,
        name: str,
        report_type: str,
        schedule_version_id: str,
        frequency: ScheduleFrequency,
        delivery_emails: List[str],
        run_hour: int = 6,
        run_day_of_week: int = 0,
        run_day_of_month: int = 1,
        options: Dict = None
    ) -> ScheduledReport:
        """Create a new report schedule."""
        schedule = ScheduledReport(
            schedule_id=schedule_id,
            name=name,
            report_type=report_type,
            schedule_version_id=schedule_version_id,
            frequency=frequency,
            delivery_emails=delivery_emails,
            run_hour=run_hour,
            run_day_of_week=run_day_of_week,
            run_day_of_month=run_day_of_month,
            options=options or {},
            next_run=self._calculate_next_run(frequency, run_hour, run_day_of_week, run_day_of_month)
        )
        
        self._schedules[schedule_id] = schedule
        logger.info(f"Created report schedule: {name} ({frequency.value})")
        
        return schedule
    
    def update_schedule(self, schedule_id: str, **updates) -> Optional[ScheduledReport]:
        """Update an existing schedule."""
        if schedule_id not in self._schedules:
            return None
        
        schedule = self._schedules[schedule_id]
        
        for key, value in updates.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)
        
        # Recalculate next run if timing changed
        if any(k in updates for k in ['frequency', 'run_hour', 'run_day_of_week', 'run_day_of_month']):
            schedule.next_run = self._calculate_next_run(
                schedule.frequency,
                schedule.run_hour,
                schedule.run_day_of_week,
                schedule.run_day_of_month
            )
        
        return schedule
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            return True
        return False
    
    def get_schedule(self, schedule_id: str) -> Optional[ScheduledReport]:
        """Get a schedule by ID."""
        return self._schedules.get(schedule_id)
    
    def list_schedules(self, schedule_version_id: str = None) -> List[Dict]:
        """List all schedules."""
        schedules = list(self._schedules.values())
        
        if schedule_version_id:
            schedules = [s for s in schedules if s.schedule_version_id == schedule_version_id]
        
        return [{
            'schedule_id': s.schedule_id,
            'name': s.name,
            'report_type': s.report_type,
            'frequency': s.frequency.value,
            'enabled': s.enabled,
            'delivery_emails': s.delivery_emails,
            'last_run': s.last_run.isoformat() if s.last_run else None,
            'next_run': s.next_run.isoformat() if s.next_run else None
        } for s in schedules]
    
    # =========================================================================
    # Scheduling Logic
    # =========================================================================
    
    def _calculate_next_run(
        self,
        frequency: ScheduleFrequency,
        run_hour: int,
        run_day_of_week: int,
        run_day_of_month: int
    ) -> datetime:
        """Calculate the next run time."""
        now = datetime.now()
        
        if frequency == ScheduleFrequency.DAILY:
            next_run = now.replace(hour=run_hour, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif frequency == ScheduleFrequency.WEEKLY:
            days_ahead = run_day_of_week - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run = now.replace(hour=run_hour, minute=0, second=0, microsecond=0)
            next_run += timedelta(days=days_ahead)
        
        elif frequency == ScheduleFrequency.MONTHLY:
            if now.day > run_day_of_month:
                # Next month
                if now.month == 12:
                    next_run = now.replace(year=now.year + 1, month=1, day=run_day_of_month,
                                          hour=run_hour, minute=0, second=0, microsecond=0)
                else:
                    next_run = now.replace(month=now.month + 1, day=run_day_of_month,
                                          hour=run_hour, minute=0, second=0, microsecond=0)
            else:
                next_run = now.replace(day=run_day_of_month, hour=run_hour,
                                      minute=0, second=0, microsecond=0)
                if next_run <= now:
                    if now.month == 12:
                        next_run = next_run.replace(year=now.year + 1, month=1)
                    else:
                        next_run = next_run.replace(month=now.month + 1)
        
        else:
            next_run = None
        
        return next_run
    
    # =========================================================================
    # Execution
    # =========================================================================
    
    async def run_schedule(self, schedule_id: str, db=None) -> ReportDelivery:
        """Execute a scheduled report immediately."""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        import uuid
        delivery_id = str(uuid.uuid4())
        
        try:
            # Generate report
            if self._report_generator and db:
                report = self._report_generator.generate_report(
                    schedule.report_type,
                    schedule.schedule_version_id,
                    options=schedule.options
                )
                
                # Export to PDF
                pdf_bytes = self._report_generator.export_to_pdf(report)
                file_path = f"/tmp/reports/{delivery_id}.pdf"
                # In production, would save to file storage
            else:
                file_path = None
            
            # Send emails
            delivery_status = "success"
            error = None
            
            if self._email_sender and schedule.delivery_emails:
                for email in schedule.delivery_emails:
                    try:
                        await self._send_report_email(
                            email,
                            schedule.name,
                            schedule.report_type,
                            file_path
                        )
                    except Exception as e:
                        error = str(e)
                        delivery_status = "partial"
            
            delivery = ReportDelivery(
                delivery_id=delivery_id,
                schedule_id=schedule_id,
                report_type=schedule.report_type,
                generated_at=datetime.now(),
                delivered_to=schedule.delivery_emails,
                status=delivery_status,
                error_message=error,
                file_path=file_path
            )
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            delivery = ReportDelivery(
                delivery_id=delivery_id,
                schedule_id=schedule_id,
                report_type=schedule.report_type,
                generated_at=datetime.now(),
                delivered_to=[],
                status="failed",
                error_message=str(e)
            )
        
        # Update schedule
        schedule.last_run = datetime.now()
        schedule.next_run = self._calculate_next_run(
            schedule.frequency,
            schedule.run_hour,
            schedule.run_day_of_week,
            schedule.run_day_of_month
        )
        
        self._deliveries.append(delivery)
        
        return delivery
    
    async def _send_report_email(
        self,
        to_email: str,
        report_name: str,
        report_type: str,
        attachment_path: str = None
    ):
        """Send report email (placeholder for email integration)."""
        logger.info(f"Sending {report_type} report '{report_name}' to {to_email}")
        
        # In production, would use SMTP or email service
        # Example with smtplib:
        # import smtplib
        # from email.mime.multipart import MIMEMultipart
        # from email.mime.application import MIMEApplication
        # msg = MIMEMultipart()
        # msg['To'] = to_email
        # msg['Subject'] = f"MineOpt Report: {report_name}"
        # if attachment_path:
        #     with open(attachment_path, 'rb') as f:
        #         attachment = MIMEApplication(f.read(), _subtype='pdf')
        #         attachment.add_header('Content-Disposition', 'attachment', filename='report.pdf')
        #         msg.attach(attachment)
        
        pass
    
    # =========================================================================
    # Background Scheduler
    # =========================================================================
    
    async def start_scheduler(self, check_interval: int = 60):
        """Start background scheduler loop."""
        self._running = True
        logger.info("Report scheduler started")
        
        while self._running:
            await self._check_due_schedules()
            await asyncio.sleep(check_interval)
    
    async def stop_scheduler(self):
        """Stop the scheduler."""
        self._running = False
        logger.info("Report scheduler stopped")
    
    async def _check_due_schedules(self):
        """Check for and run any due schedules."""
        now = datetime.now()
        
        for schedule in self._schedules.values():
            if not schedule.enabled:
                continue
            
            if schedule.next_run and schedule.next_run <= now:
                try:
                    await self.run_schedule(schedule.schedule_id)
                except Exception as e:
                    logger.error(f"Failed to run schedule {schedule.schedule_id}: {e}")
    
    # =========================================================================
    # Delivery History
    # =========================================================================
    
    def get_deliveries(
        self,
        schedule_id: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get delivery history."""
        deliveries = self._deliveries
        
        if schedule_id:
            deliveries = [d for d in deliveries if d.schedule_id == schedule_id]
        
        deliveries = sorted(deliveries, key=lambda d: d.generated_at, reverse=True)[:limit]
        
        return [{
            'delivery_id': d.delivery_id,
            'schedule_id': d.schedule_id,
            'report_type': d.report_type,
            'generated_at': d.generated_at.isoformat(),
            'delivered_to': d.delivered_to,
            'status': d.status,
            'error': d.error_message
        } for d in deliveries]


# Singleton
report_scheduler = ReportScheduler()
