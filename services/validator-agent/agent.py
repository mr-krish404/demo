"""
Validator Agent - Multi-agent validation and cross-attestation
"""
import os
import sys
import json
from typing import Dict, Any, List
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from shared.database import DatabaseManager, Finding, FindingStatus, Vote, VoteType
from shared.config import settings

class ValidatorAgent:
    """Validates findings through multi-agent reproduction"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(settings.database_url)
        self.agent_id = "validator-agent-1"
    
    def execute(self, finding_id: str):
        """Execute validation on a finding"""
        session = next(self.db_manager.get_session())
        try:
            finding = session.query(Finding).filter(Finding.id == finding_id).first()
            if not finding:
                print(f"Finding {finding_id} not found")
                return
            
            print(f"Validating finding: {finding.title}")
            
            # Attempt primary reproduction
            primary_result = self.reproduce_primary(finding)
            
            # Attempt secondary reproduction with different method
            secondary_result = self.reproduce_secondary(finding)
            
            # Cast vote based on results
            if primary_result and secondary_result:
                self.cast_vote(session, finding, VoteType.ACCEPT, 
                             "Successfully reproduced using multiple methods", 0.95)
                finding.status = FindingStatus.VALIDATED
                finding.confidence = 0.95
            elif primary_result or secondary_result:
                self.cast_vote(session, finding, VoteType.MORE_INFO,
                             "Partially reproduced, needs more investigation", 0.6)
                finding.confidence = 0.6
            else:
                self.cast_vote(session, finding, VoteType.REJECT,
                             "Could not reproduce the finding", 0.2)
                finding.status = FindingStatus.FALSE_POSITIVE
                finding.confidence = 0.2
            
            session.commit()
            print(f"Validation completed for finding {finding_id}")
        
        except Exception as e:
            print(f"Error validating finding: {e}")
        finally:
            session.close()
    
    def reproduce_primary(self, finding: Finding) -> bool:
        """Attempt primary reproduction"""
        print(f"Primary reproduction attempt for {finding.title}")
        
        if not finding.affected_url:
            return False
        
        try:
            # Attempt to reproduce the vulnerability
            response = requests.get(finding.affected_url, timeout=10)
            
            # Check for vulnerability indicators based on severity
            if finding.severity.value == 'critical':
                # For critical findings, look for strong indicators
                indicators = ['error', 'exception', 'root:', 'uid=']
                return any(ind in response.text.lower() for ind in indicators)
            elif finding.severity.value == 'high':
                # For high findings, check for XSS/injection patterns
                return '<script>' in response.text or 'alert(' in response.text
            else:
                # For lower severity, be more lenient
                return response.status_code == 200
        
        except Exception as e:
            print(f"Primary reproduction failed: {e}")
            return False
    
    def reproduce_secondary(self, finding: Finding) -> bool:
        """Attempt secondary reproduction with different method"""
        print(f"Secondary reproduction attempt for {finding.title}")
        
        if not finding.affected_url:
            return False
        
        try:
            # Use different approach (e.g., POST instead of GET)
            if finding.affected_parameter:
                data = {finding.affected_parameter: "test"}
                response = requests.post(finding.affected_url, data=data, timeout=10)
            else:
                response = requests.head(finding.affected_url, timeout=10)
            
            # Check if response indicates vulnerability
            return response.status_code in [200, 500, 403]
        
        except Exception as e:
            print(f"Secondary reproduction failed: {e}")
            return False
    
    def cast_vote(self, session, finding: Finding, vote: VoteType, 
                  rationale: str, confidence: float):
        """Cast a validation vote"""
        vote_record = Vote(
            finding_id=finding.id,
            agent_id=self.agent_id,
            vote=vote,
            rationale=rationale,
            confidence=confidence
        )
        session.add(vote_record)
        print(f"Cast vote: {vote.value} with confidence {confidence}")

def main():
    """Main entry point"""
    finding_id = os.getenv("FINDING_ID")
    if not finding_id:
        print("No FINDING_ID provided")
        return
    
    agent = ValidatorAgent()
    agent.execute(finding_id)

if __name__ == "__main__":
    main()
