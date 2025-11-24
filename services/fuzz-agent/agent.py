"""
Fuzz Agent - Performs intelligent fuzzing with mutation engine
"""
import os
import sys
import json
import random
import urllib.parse
from typing import Dict, Any, List, Tuple
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from shared.database import DatabaseManager, Job, JobStatus, Finding, FindingSeverity, FindingStatus
from shared.config import settings

class MutationEngine:
    """Generates and evolves payloads for fuzzing"""
    
    def __init__(self):
        self.seed_payloads = {
            'xss': [
                '<script>alert(1)</script>',
                '"><script>alert(1)</script>',
                '<img src=x onerror=alert(1)>',
                'javascript:alert(1)',
                '<svg onload=alert(1)>'
            ],
            'sqli': [
                "' OR '1'='1",
                "1' OR '1'='1' --",
                "' UNION SELECT NULL--",
                "1; DROP TABLE users--",
                "admin'--"
            ],
            'command_injection': [
                '; ls -la',
                '| whoami',
                '`id`',
                '$(whoami)',
                '; cat /etc/passwd'
            ],
            'path_traversal': [
                '../../../etc/passwd',
                '..\\..\\..\\windows\\system32\\config\\sam',
                '....//....//....//etc/passwd',
                '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd'
            ]
        }
    
    def mutate(self, payload: str, mutation_type: str = 'random') -> str:
        """Apply mutation to a payload"""
        mutations = [
            self._case_mutation,
            self._encoding_mutation,
            self._whitespace_mutation,
            self._concatenation_mutation
        ]
        
        mutator = random.choice(mutations)
        return mutator(payload)
    
    def _case_mutation(self, payload: str) -> str:
        """Randomly change case"""
        return ''.join(c.upper() if random.random() > 0.5 else c.lower() for c in payload)
    
    def _encoding_mutation(self, payload: str) -> str:
        """Apply URL encoding"""
        if random.random() > 0.5:
            return urllib.parse.quote(payload)
        return payload
    
    def _whitespace_mutation(self, payload: str) -> str:
        """Add whitespace variations"""
        whitespace_chars = [' ', '\t', '\n', '\r']
        result = payload
        for _ in range(random.randint(1, 3)):
            pos = random.randint(0, len(result))
            result = result[:pos] + random.choice(whitespace_chars) + result[pos:]
        return result
    
    def _concatenation_mutation(self, payload: str) -> str:
        """Add concatenation operators"""
        if 'script' in payload.lower():
            return payload.replace('script', 'scr'+'ipt')
        return payload
    
    def generate_payloads(self, attack_type: str, count: int = 10) -> List[str]:
        """Generate mutated payloads"""
        base_payloads = self.seed_payloads.get(attack_type, [])
        generated = []
        
        for _ in range(count):
            base = random.choice(base_payloads)
            mutated = self.mutate(base)
            generated.append(mutated)
        
        return generated

class FuzzAgent:
    """Fuzzing agent for vulnerability discovery"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(settings.database_url)
        self.mutation_engine = MutationEngine()
        self.findings = []
    
    def execute(self, job_id: str):
        """Execute fuzzing job"""
        session = next(self.db_manager.get_session())
        try:
            job = session.query(Job).filter(Job.id == job_id).first()
            if not job:
                print(f"Job {job_id} not found")
                return
            
            from shared.database import Target
            targets = session.query(Target).filter(Target.project_id == job.project_id).all()
            
            if not targets:
                print("No targets found")
                return
            
            # Fuzz each target
            for target in targets:
                print(f"Fuzzing target: {target.value}")
                self.fuzz_target(session, job, target.value)
            
            # Update job status
            job.status = JobStatus.COMPLETED
            job.result = {
                "findings_count": len(self.findings),
                "payloads_tested": 100
            }
            session.commit()
            
            print(f"Fuzzing completed for job {job_id}")
        except Exception as e:
            print(f"Error executing fuzzing: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            session.commit()
        finally:
            session.close()
    
    def fuzz_target(self, session, job, target_url: str):
        """Fuzz a single target"""
        # Test for XSS
        self.test_xss(session, job, target_url)
        
        # Test for SQLi
        self.test_sqli(session, job, target_url)
        
        # Test for Command Injection
        self.test_command_injection(session, job, target_url)
    
    def test_xss(self, session, job, url: str):
        """Test for Cross-Site Scripting"""
        print(f"Testing XSS on {url}")
        
        payloads = self.mutation_engine.generate_payloads('xss', 20)
        
        for payload in payloads:
            try:
                # Test in URL parameter
                test_url = f"{url}?test={urllib.parse.quote(payload)}"
                response = requests.get(test_url, timeout=5)
                
                # Check if payload is reflected
                if payload in response.text or payload.replace('<', '&lt;') in response.text:
                    self.create_finding(
                        session, job,
                        "Potential Cross-Site Scripting (XSS)",
                        f"Reflected XSS detected at {url}. Payload: {payload}",
                        FindingSeverity.HIGH,
                        url,
                        "test"
                    )
                    break
            except Exception as e:
                continue
    
    def test_sqli(self, session, job, url: str):
        """Test for SQL Injection"""
        print(f"Testing SQL Injection on {url}")
        
        payloads = self.mutation_engine.generate_payloads('sqli', 20)
        
        for payload in payloads:
            try:
                test_url = f"{url}?id={urllib.parse.quote(payload)}"
                response = requests.get(test_url, timeout=5)
                
                # Check for SQL error signatures
                sql_errors = [
                    'sql syntax',
                    'mysql_fetch',
                    'postgresql',
                    'ora-',
                    'sqlite',
                    'syntax error'
                ]
                
                response_lower = response.text.lower()
                for error in sql_errors:
                    if error in response_lower:
                        self.create_finding(
                            session, job,
                            "Potential SQL Injection",
                            f"SQL Injection detected at {url}. Payload: {payload}. Error: {error}",
                            FindingSeverity.CRITICAL,
                            url,
                            "id"
                        )
                        return
            except Exception as e:
                continue
    
    def test_command_injection(self, session, job, url: str):
        """Test for Command Injection"""
        print(f"Testing Command Injection on {url}")
        
        payloads = self.mutation_engine.generate_payloads('command_injection', 15)
        
        for payload in payloads:
            try:
                test_url = f"{url}?cmd={urllib.parse.quote(payload)}"
                response = requests.get(test_url, timeout=5)
                
                # Check for command execution indicators
                indicators = ['root:', 'uid=', 'gid=', 'groups=', '/bin/', '/usr/']
                
                for indicator in indicators:
                    if indicator in response.text:
                        self.create_finding(
                            session, job,
                            "Potential Command Injection",
                            f"Command Injection detected at {url}. Payload: {payload}",
                            FindingSeverity.CRITICAL,
                            url,
                            "cmd"
                        )
                        return
            except Exception as e:
                continue
    
    def create_finding(self, session, job, title: str, description: str, 
                      severity: FindingSeverity, url: str, param: str):
        """Create a finding"""
        finding = Finding(
            project_id=job.project_id,
            job_id=job.id,
            test_case_id=job.test_case_id,
            title=title,
            description=description,
            severity=severity,
            confidence=0.7,
            status=FindingStatus.TENTATIVE,
            affected_url=url,
            affected_parameter=param
        )
        session.add(finding)
        session.commit()
        self.findings.append(finding)
        print(f"Created finding: {title}")

def main():
    """Main entry point"""
    job_id = os.getenv("JOB_ID")
    if not job_id:
        print("No JOB_ID provided")
        return
    
    agent = FuzzAgent()
    agent.execute(job_id)

if __name__ == "__main__":
    main()
