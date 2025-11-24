"""
Audit logging for user actions
"""
from datetime import datetime
from typing import Optional, Dict, Any
import uuid
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .database import Base, DatabaseManager

class AuditLog(Base):
    """Audit log entry for user actions"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(255))
    details = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(String(512))
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    success = Column(Boolean, nullable=False, default=True)

class AuditLogger:
    """Helper class for audit logging"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def log(
        self,
        user_id: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True
    ):
        """Log a user action"""
        session = next(self.db_manager.get_session())
        try:
            log_entry = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success
            )
            session.add(log_entry)
            session.commit()
        except Exception as e:
            print(f"Failed to write audit log: {e}")
            session.rollback()
        finally:
            session.close()
    
    def log_login(self, user_id: str, ip_address: str, success: bool = True):
        """Log a login attempt"""
        self.log(
            user_id=user_id,
            action="login",
            ip_address=ip_address,
            success=success
        )
    
    def log_project_created(self, user_id: str, project_id: str, project_name: str):
        """Log project creation"""
        self.log(
            user_id=user_id,
            action="project_created",
            resource_type="project",
            resource_id=project_id,
            details={"name": project_name}
        )
    
    def log_scan_started(self, user_id: str, project_id: str):
        """Log scan start"""
        self.log(
            user_id=user_id,
            action="scan_started",
            resource_type="project",
            resource_id=project_id
        )
    
    def log_finding_validated(self, user_id: str, finding_id: str, status: str):
        """Log finding validation"""
        self.log(
            user_id=user_id,
            action="finding_validated",
            resource_type="finding",
            resource_id=finding_id,
            details={"status": status}
        )
    
    def log_report_generated(self, user_id: str, project_id: str, format: str):
        """Log report generation"""
        self.log(
            user_id=user_id,
            action="report_generated",
            resource_type="project",
            resource_id=project_id,
            details={"format": format}
        )
