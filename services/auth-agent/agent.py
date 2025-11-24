"""
Auth Agent - Tests authentication mechanisms and vulnerabilities
"""
import os
import sys
import requests
from typing import Dict, Any, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from shared.database import DatabaseManager, Job, JobStatus, Finding, FindingSeverity, FindingStatus, Target
from shared.config import settings

class AuthAgent:
    """Tests authentication mechanisms for vulnerabilities"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(settings.database_url)
    
    def execute(self, job_id: str):
        """Execute authentication testing job"""
        session = next(self.db_manager.get_session())
        try:
            job = session.query(Job).filter(Job.id == job_id).first()
            if not job:
                print(f"Job {job_id} not found")
                return
            
            targets = session.query(Target).filter(Target.project_id == job.project_id).all()
            
            if not targets:
                print("No targets found")
                return
            
            findings_count = 0
            for target in targets:
                print(f"Testing authentication on {target.value}")
                
                # Test for common auth vulnerabilities
                findings_count += self.test_weak_passwords(session, job, target.value)
                findings_count += self.test_default_credentials(session, job, target.value)
                findings_count += self.test_brute_force_protection(session, job, target.value)
                findings_count += self.test_session_management(session, job, target.value)
            
            job.status = JobStatus.COMPLETED
            job.result = {"findings_created": findings_count}
            session.commit()
            
            print(f"Auth agent completed for job {job_id}")
        
        except Exception as e:
            print(f"Error executing auth agent: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            session.commit()
        finally:
            session.close()
    
    def test_weak_passwords(self, session, job, url: str) -> int:
        """Test for weak password policies"""
        print(f"Testing weak passwords on {url}")
        
        weak_passwords = ["password", "123456", "admin", "test", ""]
        
        for password in weak_passwords:
            try:
                # Attempt login with weak password
                response = requests.post(
                    f"{url}/login",
                    data={"username": "admin", "password": password},
                    timeout=5
                )
                
                if response.status_code == 200 and "success" in response.text.lower():
                    finding = Finding(
                        project_id=job.project_id,
                        job_id=job.id,
                        test_case_id=job.test_case_id,
                        title="Weak Password Accepted",
                        description=f"The application accepts weak passwords. Tested password: '{password}'",
                        severity=FindingSeverity.HIGH,
                        confidence=0.8,
                        status=FindingStatus.TENTATIVE,
                        affected_url=url,
                        affected_parameter="password",
                        remediation="Implement strong password policy requiring minimum length, complexity, and common password checks."
                    )
                    session.add(finding)
                    session.commit()
                    return 1
            
            except Exception:
                continue
        
        return 0
    
    def test_default_credentials(self, session, job, url: str) -> int:
        """Test for default credentials"""
        print(f"Testing default credentials on {url}")
        
        default_creds = [
            ("admin", "admin"),
            ("admin", "password"),
            ("root", "root"),
            ("administrator", "administrator"),
            ("test", "test")
        ]
        
        for username, password in default_creds:
            try:
                response = requests.post(
                    f"{url}/login",
                    data={"username": username, "password": password},
                    timeout=5
                )
                
                if response.status_code == 200 and "dashboard" in response.text.lower():
                    finding = Finding(
                        project_id=job.project_id,
                        job_id=job.id,
                        test_case_id=job.test_case_id,
                        title="Default Credentials Accepted",
                        description=f"The application accepts default credentials: {username}/{password}",
                        severity=FindingSeverity.CRITICAL,
                        confidence=0.95,
                        status=FindingStatus.TENTATIVE,
                        affected_url=url,
                        remediation="Remove or change all default credentials before deployment."
                    )
                    session.add(finding)
                    session.commit()
                    return 1
            
            except Exception:
                continue
        
        return 0
    
    def test_brute_force_protection(self, session, job, url: str) -> int:
        """Test for brute force protection"""
        print(f"Testing brute force protection on {url}")
        
        try:
            # Attempt multiple failed logins
            for i in range(10):
                response = requests.post(
                    f"{url}/login",
                    data={"username": "admin", "password": f"wrong{i}"},
                    timeout=5
                )
                
                # Check if account is locked or rate limited
                if "locked" in response.text.lower() or "too many" in response.text.lower():
                    print("Brute force protection detected")
                    return 0
            
            # If we got here, no brute force protection
            finding = Finding(
                project_id=job.project_id,
                job_id=job.id,
                test_case_id=job.test_case_id,
                title="Missing Brute Force Protection",
                description="The application does not implement brute force protection. Multiple failed login attempts were allowed without rate limiting or account lockout.",
                severity=FindingSeverity.MEDIUM,
                confidence=0.85,
                status=FindingStatus.TENTATIVE,
                affected_url=url,
                remediation="Implement rate limiting, account lockout after failed attempts, and CAPTCHA for login forms."
            )
            session.add(finding)
            session.commit()
            return 1
        
        except Exception as e:
            print(f"Error testing brute force protection: {e}")
            return 0
    
    def test_session_management(self, session, job, url: str) -> int:
        """Test session management vulnerabilities"""
        print(f"Testing session management on {url}")
        
        try:
            # Test for session fixation
            response1 = requests.get(url, timeout=5)
            session_id_before = response1.cookies.get("sessionid") or response1.cookies.get("PHPSESSID")
            
            if session_id_before:
                # Attempt login
                response2 = requests.post(
                    f"{url}/login",
                    data={"username": "test", "password": "test"},
                    cookies=response1.cookies,
                    timeout=5
                )
                
                session_id_after = response2.cookies.get("sessionid") or response2.cookies.get("PHPSESSID")
                
                # Check if session ID changed after login
                if session_id_before == session_id_after:
                    finding = Finding(
                        project_id=job.project_id,
                        job_id=job.id,
                        test_case_id=job.test_case_id,
                        title="Session Fixation Vulnerability",
                        description="The application does not regenerate session IDs after authentication, making it vulnerable to session fixation attacks.",
                        severity=FindingSeverity.HIGH,
                        confidence=0.75,
                        status=FindingStatus.TENTATIVE,
                        affected_url=url,
                        remediation="Regenerate session IDs after successful authentication."
                    )
                    session.add(finding)
                    session.commit()
                    return 1
        
        except Exception as e:
            print(f"Error testing session management: {e}")
        
        return 0

def main():
    """Main entry point"""
    job_id = os.getenv("JOB_ID")
    if not job_id:
        print("No JOB_ID provided")
        return
    
    agent = AuthAgent()
    agent.execute(job_id)

if __name__ == "__main__":
    main()
