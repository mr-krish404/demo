"""
Recon Agent - Performs reconnaissance, crawling, and fingerprinting
"""
import os
import sys
import json
from typing import Dict, Any, List
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from shared.database import DatabaseManager, Job, JobStatus, Finding, FindingSeverity, FindingStatus, Evidence, EvidenceType
from shared.config import settings
from shared.storage import StorageManager

class ReconAgent:
    """Reconnaissance agent for web application scanning"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(settings.database_url)
        self.storage_manager = StorageManager()
        self.discovered_urls = set()
        self.discovered_params = {}
        self.technologies = []
    
    def execute(self, job_id: str):
        """Execute reconnaissance job"""
        session = next(self.db_manager.get_session())
        try:
            # Get job details
            job = session.query(Job).filter(Job.id == job_id).first()
            if not job:
                print(f"Job {job_id} not found")
                return
            
            # Get target from project
            from shared.database import Target
            targets = session.query(Target).filter(Target.project_id == job.project_id).all()
            
            if not targets:
                print("No targets found")
                return
            
            # Execute recon on each target
            for target in targets:
                print(f"Scanning target: {target.value}")
                self.scan_target(session, job, target.value)
            
            # Update job status
            job.status = JobStatus.COMPLETED
            job.result = {
                "urls_discovered": len(self.discovered_urls),
                "parameters_discovered": len(self.discovered_params),
                "technologies": self.technologies
            }
            session.commit()
            
            print(f"Recon completed for job {job_id}")
        except Exception as e:
            print(f"Error executing recon: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            session.commit()
        finally:
            session.close()
    
    def scan_target(self, session, job, target_url: str):
        """Scan a single target"""
        # Crawl with Playwright
        self.crawl_with_playwright(target_url)
        
        # Fingerprint technologies
        self.fingerprint_technologies(target_url)
        
        # Discover parameters
        self.discover_parameters(target_url)
        
        # Create findings for interesting discoveries
        self.create_findings(session, job)
    
    def crawl_with_playwright(self, base_url: str, max_pages: int = 50):
        """Crawl website using Playwright"""
        print(f"Crawling {base_url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            
            to_visit = [base_url]
            visited = set()
            
            while to_visit and len(visited) < max_pages:
                url = to_visit.pop(0)
                
                if url in visited:
                    continue
                
                try:
                    print(f"Visiting: {url}")
                    page.goto(url, timeout=10000, wait_until="networkidle")
                    visited.add(url)
                    self.discovered_urls.add(url)
                    
                    # Extract links
                    links = page.eval_on_selector_all(
                        'a[href]',
                        '(elements) => elements.map(e => e.href)'
                    )
                    
                    for link in links:
                        absolute_url = urljoin(base_url, link)
                        parsed = urlparse(absolute_url)
                        
                        # Only follow same-domain links
                        if parsed.netloc == urlparse(base_url).netloc:
                            if absolute_url not in visited:
                                to_visit.append(absolute_url)
                    
                    # Extract forms and parameters
                    forms = page.query_selector_all('form')
                    for form in forms:
                        inputs = form.query_selector_all('input, select, textarea')
                        for inp in inputs:
                            name = inp.get_attribute('name')
                            if name:
                                self.discovered_params[name] = {
                                    'type': inp.get_attribute('type') or 'text',
                                    'url': url
                                }
                
                except Exception as e:
                    print(f"Error crawling {url}: {e}")
                    continue
            
            browser.close()
        
        print(f"Crawled {len(visited)} pages, discovered {len(self.discovered_urls)} URLs")
    
    def fingerprint_technologies(self, url: str):
        """Detect technologies used by the target"""
        print(f"Fingerprinting {url}")
        
        try:
            response = requests.get(url, timeout=10)
            headers = response.headers
            content = response.text
            
            # Check server header
            if 'Server' in headers:
                self.technologies.append({
                    'type': 'server',
                    'name': headers['Server']
                })
            
            # Check for common frameworks
            if 'X-Powered-By' in headers:
                self.technologies.append({
                    'type': 'framework',
                    'name': headers['X-Powered-By']
                })
            
            # Check content for framework signatures
            if 'wp-content' in content or 'wp-includes' in content:
                self.technologies.append({'type': 'cms', 'name': 'WordPress'})
            
            if 'Drupal' in content:
                self.technologies.append({'type': 'cms', 'name': 'Drupal'})
            
            if 'django' in content.lower():
                self.technologies.append({'type': 'framework', 'name': 'Django'})
            
            if 'react' in content.lower() or '_next' in content:
                self.technologies.append({'type': 'frontend', 'name': 'React/Next.js'})
            
            print(f"Detected technologies: {self.technologies}")
        
        except Exception as e:
            print(f"Error fingerprinting: {e}")
    
    def discover_parameters(self, url: str):
        """Discover URL parameters"""
        parsed = urlparse(url)
        if parsed.query:
            from urllib.parse import parse_qs
            params = parse_qs(parsed.query)
            for param in params:
                if param not in self.discovered_params:
                    self.discovered_params[param] = {
                        'type': 'query',
                        'url': url
                    }
    
    def create_findings(self, session, job):
        """Create findings based on discoveries"""
        # Example: Create info finding for discovered technologies
        if self.technologies:
            finding = Finding(
                project_id=job.project_id,
                job_id=job.id,
                test_case_id=job.test_case_id,
                title="Technologies Detected",
                description=f"Detected the following technologies: {json.dumps(self.technologies, indent=2)}",
                severity=FindingSeverity.INFO,
                confidence=0.9,
                status=FindingStatus.VALIDATED
            )
            session.add(finding)
            session.commit()

def main():
    """Main entry point"""
    job_id = os.getenv("JOB_ID")
    if not job_id:
        print("No JOB_ID provided")
        return
    
    agent = ReconAgent()
    agent.execute(job_id)

if __name__ == "__main__":
    main()
