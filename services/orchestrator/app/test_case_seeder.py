"""
Seed WSTG test cases into database
"""
import sys
import os
from datetime import datetime
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from shared.database import DatabaseManager, TestCase
from shared.config import settings

WSTG_TEST_CASES = [
    # Information Gathering
    {"wstg_id": "WSTG-INFO-01", "title": "Conduct Search Engine Discovery", "category": "Information Gathering", "agent": "recon-agent", "priority": 1},
    {"wstg_id": "WSTG-INFO-02", "title": "Fingerprint Web Server", "category": "Information Gathering", "agent": "recon-agent", "priority": 1},
    {"wstg_id": "WSTG-INFO-03", "title": "Review Webserver Metafiles", "category": "Information Gathering", "agent": "recon-agent", "priority": 2},
    {"wstg_id": "WSTG-INFO-04", "title": "Enumerate Applications on Webserver", "category": "Information Gathering", "agent": "recon-agent", "priority": 2},
    {"wstg_id": "WSTG-INFO-05", "title": "Review Webpage Content for Information Leakage", "category": "Information Gathering", "agent": "recon-agent", "priority": 3},
    {"wstg_id": "WSTG-INFO-06", "title": "Identify Application Entry Points", "category": "Information Gathering", "agent": "recon-agent", "priority": 1},
    {"wstg_id": "WSTG-INFO-07", "title": "Map Execution Paths Through Application", "category": "Information Gathering", "agent": "recon-agent", "priority": 2},
    {"wstg_id": "WSTG-INFO-08", "title": "Fingerprint Web Application Framework", "category": "Information Gathering", "agent": "recon-agent", "priority": 1},
    {"wstg_id": "WSTG-INFO-09", "title": "Fingerprint Web Application", "category": "Information Gathering", "agent": "recon-agent", "priority": 1},
    {"wstg_id": "WSTG-INFO-10", "title": "Map Application Architecture", "category": "Information Gathering", "agent": "recon-agent", "priority": 2},
    
    # Configuration Management
    {"wstg_id": "WSTG-CONF-01", "title": "Test Network Infrastructure Configuration", "category": "Configuration", "agent": "recon-agent", "priority": 2},
    {"wstg_id": "WSTG-CONF-02", "title": "Test Application Platform Configuration", "category": "Configuration", "agent": "recon-agent", "priority": 2},
    {"wstg_id": "WSTG-CONF-03", "title": "Test File Extensions Handling", "category": "Configuration", "agent": "fuzz-agent", "priority": 3},
    {"wstg_id": "WSTG-CONF-04", "title": "Review Old Backup and Unreferenced Files", "category": "Configuration", "agent": "recon-agent", "priority": 3},
    
    # Identity Management
    {"wstg_id": "WSTG-IDNT-01", "title": "Test Role Definitions", "category": "Identity", "agent": "auth-agent", "priority": 2},
    {"wstg_id": "WSTG-IDNT-02", "title": "Test User Registration Process", "category": "Identity", "agent": "auth-agent", "priority": 2},
    {"wstg_id": "WSTG-IDNT-03", "title": "Test Account Provisioning Process", "category": "Identity", "agent": "auth-agent", "priority": 3},
    {"wstg_id": "WSTG-IDNT-04", "title": "Testing for Account Enumeration", "category": "Identity", "agent": "auth-agent", "priority": 2},
    {"wstg_id": "WSTG-IDNT-05", "title": "Testing for Weak Username Policy", "category": "Identity", "agent": "auth-agent", "priority": 3},
    
    # Authentication
    {"wstg_id": "WSTG-ATHN-01", "title": "Testing for Credentials Transported over Encrypted Channel", "category": "Authentication", "agent": "auth-agent", "priority": 1},
    {"wstg_id": "WSTG-ATHN-02", "title": "Testing for Default Credentials", "category": "Authentication", "agent": "auth-agent", "priority": 1},
    {"wstg_id": "WSTG-ATHN-03", "title": "Testing for Weak Lock Out Mechanism", "category": "Authentication", "agent": "auth-agent", "priority": 1},
    {"wstg_id": "WSTG-ATHN-04", "title": "Testing for Bypassing Authentication Schema", "category": "Authentication", "agent": "auth-agent", "priority": 1},
    {"wstg_id": "WSTG-ATHN-05", "title": "Testing for Vulnerable Remember Password", "category": "Authentication", "agent": "auth-agent", "priority": 2},
    {"wstg_id": "WSTG-ATHN-06", "title": "Testing for Browser Cache Weaknesses", "category": "Authentication", "agent": "session-agent", "priority": 3},
    {"wstg_id": "WSTG-ATHN-07", "title": "Testing for Weak Password Policy", "category": "Authentication", "agent": "auth-agent", "priority": 1},
    {"wstg_id": "WSTG-ATHN-08", "title": "Testing for Weak Security Question Answer", "category": "Authentication", "agent": "auth-agent", "priority": 2},
    
    # Session Management
    {"wstg_id": "WSTG-SESS-01", "title": "Testing for Session Management Schema", "category": "Session", "agent": "session-agent", "priority": 1},
    {"wstg_id": "WSTG-SESS-02", "title": "Testing for Cookies Attributes", "category": "Session", "agent": "session-agent", "priority": 1},
    {"wstg_id": "WSTG-SESS-03", "title": "Testing for Session Fixation", "category": "Session", "agent": "session-agent", "priority": 1},
    {"wstg_id": "WSTG-SESS-04", "title": "Testing for Exposed Session Variables", "category": "Session", "agent": "session-agent", "priority": 2},
    {"wstg_id": "WSTG-SESS-05", "title": "Testing for CSRF", "category": "Session", "agent": "session-agent", "priority": 1},
    {"wstg_id": "WSTG-SESS-06", "title": "Testing for Logout Functionality", "category": "Session", "agent": "session-agent", "priority": 2},
    {"wstg_id": "WSTG-SESS-07", "title": "Testing Session Timeout", "category": "Session", "agent": "session-agent", "priority": 2},
    
    # Input Validation
    {"wstg_id": "WSTG-INPV-01", "title": "Testing for Reflected Cross Site Scripting", "category": "Input Validation", "agent": "fuzz-agent", "priority": 1},
    {"wstg_id": "WSTG-INPV-02", "title": "Testing for Stored Cross Site Scripting", "category": "Input Validation", "agent": "fuzz-agent", "priority": 1},
    {"wstg_id": "WSTG-INPV-03", "title": "Testing for HTTP Verb Tampering", "category": "Input Validation", "agent": "fuzz-agent", "priority": 2},
    {"wstg_id": "WSTG-INPV-04", "title": "Testing for HTTP Parameter Pollution", "category": "Input Validation", "agent": "fuzz-agent", "priority": 2},
    {"wstg_id": "WSTG-INPV-05", "title": "Testing for SQL Injection", "category": "Input Validation", "agent": "fuzz-agent", "priority": 1},
    {"wstg_id": "WSTG-INPV-06", "title": "Testing for LDAP Injection", "category": "Input Validation", "agent": "fuzz-agent", "priority": 2},
    {"wstg_id": "WSTG-INPV-07", "title": "Testing for XML Injection", "category": "Input Validation", "agent": "fuzz-agent", "priority": 2},
    {"wstg_id": "WSTG-INPV-08", "title": "Testing for SSI Injection", "category": "Input Validation", "agent": "fuzz-agent", "priority": 3},
    {"wstg_id": "WSTG-INPV-09", "title": "Testing for XPath Injection", "category": "Input Validation", "agent": "fuzz-agent", "priority": 3},
    {"wstg_id": "WSTG-INPV-10", "title": "Testing for IMAP SMTP Injection", "category": "Input Validation", "agent": "fuzz-agent", "priority": 3},
    {"wstg_id": "WSTG-INPV-11", "title": "Testing for Code Injection", "category": "Input Validation", "agent": "fuzz-agent", "priority": 1},
    {"wstg_id": "WSTG-INPV-12", "title": "Testing for Command Injection", "category": "Input Validation", "agent": "fuzz-agent", "priority": 1},
    {"wstg_id": "WSTG-INPV-13", "title": "Testing for Format String Injection", "category": "Input Validation", "agent": "fuzz-agent", "priority": 3},
]

def seed_test_cases():
    """Seed WSTG test cases into database"""
    db_manager = DatabaseManager(settings.database_url)
    session = next(db_manager.get_session())
    
    try:
        # Check if test cases already exist
        existing_count = session.query(TestCase).count()
        if existing_count > 0:
            print(f"Test cases already seeded ({existing_count} cases)")
            return
        
        # Insert all test cases
        for tc_data in WSTG_TEST_CASES:
            test_case = TestCase(
                id=uuid.uuid4(),
                wstg_id=tc_data["wstg_id"],
                title=tc_data["title"],
                description=f"Automated test for {tc_data['title']}",
                category=tc_data["category"],
                automatable=True,
                assigned_agent=tc_data["agent"],
                priority=tc_data["priority"],
                metadata={},
                created_at=datetime.utcnow()
            )
            session.add(test_case)
        
        session.commit()
        print(f"Successfully seeded {len(WSTG_TEST_CASES)} WSTG test cases")
    
    except Exception as e:
        print(f"Error seeding test cases: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_test_cases()
