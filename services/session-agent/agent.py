"""
Session Agent - Manages browser sessions, login workflows, and token extraction
"""
import os
import sys
import json
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, Page

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from shared.database import DatabaseManager, Job, JobStatus, Credential
from shared.config import settings
from shared.security import decrypt_credential

class SessionAgent:
    """Manages browser sessions and authentication workflows"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(settings.database_url)
        self.sessions = {}
    
    def execute(self, job_id: str):
        """Execute session management job"""
        session = next(self.db_manager.get_session())
        try:
            job = session.query(Job).filter(Job.id == job_id).first()
            if not job:
                print(f"Job {job_id} not found")
                return
            
            # Get credentials for the project
            credentials = session.query(Credential).filter(
                Credential.project_id == job.project_id
            ).all()
            
            if not credentials:
                print("No credentials found for project")
                job.status = JobStatus.COMPLETED
                job.result = {"message": "No credentials to test"}
                session.commit()
                return
            
            # Test each credential
            results = []
            for cred in credentials:
                result = self.test_credential(cred)
                results.append(result)
            
            job.status = JobStatus.COMPLETED
            job.result = {
                "credentials_tested": len(credentials),
                "successful_logins": sum(1 for r in results if r.get("success")),
                "results": results
            }
            session.commit()
            
            print(f"Session agent completed for job {job_id}")
        
        except Exception as e:
            print(f"Error executing session agent: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            session.commit()
        finally:
            session.close()
    
    def test_credential(self, credential: Credential) -> Dict[str, Any]:
        """Test a credential by attempting login"""
        try:
            # Decrypt credential
            cred_data = decrypt_credential(credential.encrypted_payload)
            
            if credential.type == "form":
                return self.test_form_login(cred_data)
            elif credential.type == "basic":
                return self.test_basic_auth(cred_data)
            elif credential.type == "oauth":
                return self.test_oauth(cred_data)
            else:
                return {"success": False, "error": "Unsupported credential type"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_form_login(self, cred_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test form-based login"""
        print(f"Testing form login at {cred_data.get('url')}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                # Navigate to login page
                page.goto(cred_data.get("url"), timeout=10000)
                
                # Fill in credentials
                username_selector = cred_data.get("username_selector", "input[name='username']")
                password_selector = cred_data.get("password_selector", "input[name='password']")
                submit_selector = cred_data.get("submit_selector", "button[type='submit']")
                
                page.fill(username_selector, cred_data.get("username", ""))
                page.fill(password_selector, cred_data.get("password", ""))
                page.click(submit_selector)
                
                # Wait for navigation
                page.wait_for_load_state("networkidle", timeout=5000)
                
                # Extract session tokens
                cookies = context.cookies()
                csrf_token = self.extract_csrf_token(page)
                
                # Check if login was successful
                success = self.check_login_success(page, cred_data)
                
                return {
                    "success": success,
                    "cookies": [{"name": c["name"], "value": c["value"]} for c in cookies],
                    "csrf_token": csrf_token,
                    "url": page.url
                }
            
            except Exception as e:
                return {"success": False, "error": str(e)}
            finally:
                browser.close()
    
    def test_basic_auth(self, cred_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test HTTP Basic Authentication"""
        print(f"Testing basic auth at {cred_data.get('url')}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                http_credentials={
                    "username": cred_data.get("username", ""),
                    "password": cred_data.get("password", "")
                }
            )
            page = context.new_page()
            
            try:
                response = page.goto(cred_data.get("url"), timeout=10000)
                success = response.status == 200
                
                return {
                    "success": success,
                    "status_code": response.status,
                    "url": page.url
                }
            
            except Exception as e:
                return {"success": False, "error": str(e)}
            finally:
                browser.close()
    
    def test_oauth(self, cred_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test OAuth authentication"""
        print(f"Testing OAuth at {cred_data.get('url')}")
        
        # OAuth testing would require more complex flow
        # This is a placeholder implementation
        return {
            "success": False,
            "error": "OAuth testing not fully implemented",
            "note": "Requires OAuth flow implementation"
        }
    
    def extract_csrf_token(self, page: Page) -> Optional[str]:
        """Extract CSRF token from page"""
        try:
            # Try common CSRF token locations
            selectors = [
                "input[name='csrf_token']",
                "input[name='_csrf']",
                "input[name='csrfmiddlewaretoken']",
                "meta[name='csrf-token']"
            ]
            
            for selector in selectors:
                element = page.query_selector(selector)
                if element:
                    value = element.get_attribute("value") or element.get_attribute("content")
                    if value:
                        return value
            
            return None
        
        except Exception:
            return None
    
    def check_login_success(self, page: Page, cred_data: Dict[str, Any]) -> bool:
        """Check if login was successful"""
        # Check for success indicators
        success_indicators = cred_data.get("success_indicators", [
            "dashboard", "logout", "profile", "welcome"
        ])
        
        page_content = page.content().lower()
        for indicator in success_indicators:
            if indicator.lower() in page_content:
                return True
        
        # Check for failure indicators
        failure_indicators = ["invalid", "incorrect", "failed", "error"]
        for indicator in failure_indicators:
            if indicator in page_content:
                return False
        
        # If no clear indicators, assume success if we're on a different page
        return page.url != cred_data.get("url")

def main():
    """Main entry point"""
    job_id = os.getenv("JOB_ID")
    if not job_id:
        print("No JOB_ID provided")
        return
    
    agent = SessionAgent()
    agent.execute(job_id)

if __name__ == "__main__":
    main()
