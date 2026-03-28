from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
from typing import Optional, Dict, Any
import json
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


PHI_PATHS = [
    "/fhir/Patient",
    "/fhir/Encounter",
    "/fhir/Observation",
    "/api/v1/consultations",
    "/api/v1/patients",
]


class AuditEventType:
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS = "access"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PHI_ACCESS = "phi_access"
    FAILED_LOGIN = "failed_login"


class AuditLoggerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, log_file: str = "/var/log/audit.jsonl"):
        super().__init__(app)
        self.log_file = log_file
    
    async def dispatch(self, request: Request, call_next) -> Response:
        audit_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        user_id = None
        if hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)
        
        method = request.method
        path = request.url.path
        
        is_phi_access = any(phi_path in path for phi_path in PHI_PATHS)
        
        event_type = AuditEventType.ACCESS
        if is_phi_access:
            event_type = AuditEventType.PHI_ACCESS
        
        if method == "POST" and "/auth/login" in path:
            event_type = AuditEventType.LOGIN
        elif method == "POST" and "/auth/logout" in path:
            event_type = AuditEventType.LOGOUT
        
        audit_entry = {
            "audit_id": audit_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "user_id": user_id,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "method": method,
            "path": path,
            "is_phi_access": is_phi_access,
            "query_params": dict(request.query_params),
        }
        
        try:
            response = await call_next(request)
            audit_entry["status_code"] = response.status_code
            audit_entry["response_size"] = response.headers.get("content-length", 0)
            
            self._log_audit(audit_entry)
            
            return response
            
        except Exception as e:
            audit_entry["status_code"] = 500
            audit_entry["error"] = str(e)
            self._log_audit(audit_entry)
            raise
    
    def _log_audit(self, audit_entry: Dict[str, Any]):
        log_entry = json.dumps(audit_entry)
        logger.info(f"AUDIT: {log_entry}")
        
        try:
            with open(self.log_file, "a") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")


class AuditLogger:
    @staticmethod
    def log_event(
        event_type: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        audit_entry = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "metadata": metadata or {},
        }
        
        logger.info(f"AUDIT: {json.dumps(audit_entry)}")
        
        try:
            with open("/var/log/audit.jsonl", "a") as f:
                f.write(json.dumps(audit_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    @staticmethod
    def log_phi_access(
        user_id: str,
        patient_id: str,
        resource_type: str,
        action: str,
    ):
        AuditLogger.log_event(
            event_type=AuditEventType.PHI_ACCESS,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=patient_id,
            action=action,
            metadata={"patient_id": patient_id, "hipaa_compliant": True},
        )
    
    @staticmethod
    def log_authentication(user_id: str, success: bool, ip_address: str):
        event_type = AuditEventType.LOGIN if success else AuditEventType.FAILED_LOGIN
        AuditLogger.log_event(
            event_type=event_type,
            user_id=user_id if success else None,
            metadata={"ip_address": ip_address, "success": success},
        )
