"""
Test Planning Engine - Generates intelligent test plans based on WSTG
"""
from typing import List, Dict, Any
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from shared.database import Project, Target, TestCase

class TestPlanner:
    """Generates test plans for penetration testing"""
    
    def __init__(self):
        self.wstg_test_cases = self._load_wstg_test_cases()
    
    def _load_wstg_test_cases(self) -> List[Dict[str, Any]]:
        """Load WSTG test case definitions"""
        return [
            {
                "wstg_id": "WSTG-INFO-01",
                "title": "Conduct Search Engine Discovery Reconnaissance",
                "category": "Information Gathering",
                "agent": "recon-agent",
                "priority": 1
            },
            {
                "wstg_id": "WSTG-INFO-02",
                "title": "Fingerprint Web Server",
                "category": "Information Gathering",
                "agent": "recon-agent",
                "priority": 1
            },
            {
                "wstg_id": "WSTG-CONF-01",
                "title": "Test Network Infrastructure Configuration",
                "category": "Configuration",
                "agent": "recon-agent",
                "priority": 2
            },
            {
                "wstg_id": "WSTG-IDNT-01",
                "title": "Test Role Definitions",
                "category": "Identity Management",
                "agent": "auth-agent",
                "priority": 3
            },
            {
                "wstg_id": "WSTG-ATHN-01",
                "title": "Test Credentials Transported over Encrypted Channel",
                "category": "Authentication",
                "agent": "auth-agent",
                "priority": 2
            },
            {
                "wstg_id": "WSTG-ATHN-02",
                "title": "Test Default Credentials",
                "category": "Authentication",
                "agent": "auth-agent",
                "priority": 2
            },
            {
                "wstg_id": "WSTG-ATHZ-01",
                "title": "Test Directory Traversal File Include",
                "category": "Authorization",
                "agent": "fuzz-agent",
                "priority": 3
            },
            {
                "wstg_id": "WSTG-SESS-01",
                "title": "Test Session Management Schema",
                "category": "Session Management",
                "agent": "session-agent",
                "priority": 2
            },
            {
                "wstg_id": "WSTG-INPV-01",
                "title": "Test Reflected Cross Site Scripting",
                "category": "Input Validation",
                "agent": "fuzz-agent",
                "priority": 3
            },
            {
                "wstg_id": "WSTG-INPV-02",
                "title": "Test Stored Cross Site Scripting",
                "category": "Input Validation",
                "agent": "fuzz-agent",
                "priority": 3
            },
            {
                "wstg_id": "WSTG-INPV-05",
                "title": "Test SQL Injection",
                "category": "Input Validation",
                "agent": "fuzz-agent",
                "priority": 4
            },
            {
                "wstg_id": "WSTG-INPV-11",
                "title": "Test Code Injection",
                "category": "Input Validation",
                "agent": "fuzz-agent",
                "priority": 4
            },
            {
                "wstg_id": "WSTG-INPV-12",
                "title": "Test Command Injection",
                "category": "Input Validation",
                "agent": "fuzz-agent",
                "priority": 4
            },
            {
                "wstg_id": "WSTG-ERRH-01",
                "title": "Test Error Handling",
                "category": "Error Handling",
                "agent": "recon-agent",
                "priority": 2
            },
            {
                "wstg_id": "WSTG-CRYP-01",
                "title": "Test Weak Transport Layer Security",
                "category": "Cryptography",
                "agent": "recon-agent",
                "priority": 2
            }
        ]
    
    def seed_test_cases(self, session):
        """Seed database with WSTG test cases"""
        for tc in self.wstg_test_cases:
            test_case = TestCase(
                wstg_id=tc["wstg_id"],
                title=tc["title"],
                description=f"WSTG test case: {tc['title']}",
                category=tc["category"],
                automatable=True,
                assigned_agent=tc["agent"],
                priority=tc["priority"]
            )
            session.add(test_case)
    
    def generate_plan(self, project: Project, targets: List[Target], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a test plan for a project
        Returns a structured test plan with prioritized test cases
        """
        # Get project settings
        settings = project.settings or {}
        
        # Determine which test cases to run
        selected_tests = []
        
        # Always include reconnaissance
        selected_tests.extend([tc for tc in self.wstg_test_cases if tc["category"] == "Information Gathering"])
        
        # Include authentication tests if credentials provided
        if config.get("has_credentials", False):
            selected_tests.extend([tc for tc in self.wstg_test_cases if tc["category"] in ["Authentication", "Session Management"]])
        
        # Include fuzzing tests
        selected_tests.extend([tc for tc in self.wstg_test_cases if tc["category"] == "Input Validation"])
        
        # Sort by priority
        selected_tests.sort(key=lambda x: x["priority"])
        
        return {
            "project_id": str(project.id),
            "target_count": len(targets),
            "test_cases": selected_tests,
            "estimated_duration_minutes": len(selected_tests) * 5,
            "phases": [
                {
                    "name": "Reconnaissance",
                    "tests": [tc["wstg_id"] for tc in selected_tests if tc["category"] == "Information Gathering"]
                },
                {
                    "name": "Authentication Testing",
                    "tests": [tc["wstg_id"] for tc in selected_tests if tc["category"] in ["Authentication", "Session Management"]]
                },
                {
                    "name": "Input Validation",
                    "tests": [tc["wstg_id"] for tc in selected_tests if tc["category"] == "Input Validation"]
                }
            ]
        }
