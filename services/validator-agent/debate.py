"""
Multi-agent debate system for finding validation
"""
import sys
import os
from typing import List, Dict, Any
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from shared.agent_protocol import AgentMessage, VoteMessage
from shared.database import DatabaseManager, Finding, Vote, VoteType
from shared.config import settings

class DebateCoordinator:
    """Coordinates multi-agent debate for finding validation"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(settings.database_url)
        self.messages: List[AgentMessage] = []
    
    def initiate_debate(self, finding_id: str, agents: List[str]) -> Dict[str, Any]:
        """
        Initiate a debate among multiple agents about a finding
        
        Args:
            finding_id: The finding to validate
            agents: List of agent IDs to participate in debate
        
        Returns:
            Debate results with consensus
        """
        session = next(self.db_manager.get_session())
        try:
            finding = session.query(Finding).filter(Finding.id == finding_id).first()
            if not finding:
                return {"error": "Finding not found"}
            
            # Collect votes from all agents
            votes = []
            for agent_id in agents:
                vote = self._request_vote(agent_id, finding)
                votes.append(vote)
                
                # Store vote in database
                db_vote = Vote(
                    finding_id=finding_id,
                    agent_id=agent_id,
                    vote=VoteType(vote["vote"]),
                    rationale=vote["rationale"],
                    confidence=vote["confidence"]
                )
                session.add(db_vote)
            
            session.commit()
            
            # Calculate consensus
            consensus = self._calculate_consensus(votes)
            
            # Update finding status based on consensus
            if consensus["decision"] == "accept":
                finding.status = "validated"
                finding.confidence = consensus["confidence"]
            elif consensus["decision"] == "reject":
                finding.status = "false_positive"
            
            session.commit()
            
            return {
                "finding_id": finding_id,
                "votes": votes,
                "consensus": consensus,
                "final_status": finding.status
            }
        
        finally:
            session.close()
    
    def _request_vote(self, agent_id: str, finding: Finding) -> Dict[str, Any]:
        """
        Request a vote from an agent using the agent protocol
        
        Args:
            agent_id: The agent to request vote from
            finding: The finding to vote on
        
        Returns:
            Vote data
        """
        # Create request message
        request_msg = AgentMessage(
            from_agent="debate-coordinator",
            to_agent=agent_id,
            type="request",
            payload={
                "action": "vote_on_finding",
                "finding_id": str(finding.id),
                "finding_title": finding.title,
                "finding_description": finding.description,
                "severity": finding.severity.value,
                "affected_url": finding.affected_url
            }
        )
        
        self.messages.append(request_msg)
        
        # Simulate agent response (in production, this would be async message passing)
        # For now, use simple heuristics based on agent type
        vote_result = self._simulate_agent_vote(agent_id, finding)
        
        # Create response message
        response_msg = AgentMessage(
            from_agent=agent_id,
            to_agent="debate-coordinator",
            type="vote",
            payload=vote_result
        )
        
        self.messages.append(response_msg)
        
        return vote_result
    
    def _simulate_agent_vote(self, agent_id: str, finding: Finding) -> Dict[str, Any]:
        """
        Simulate an agent's vote based on finding characteristics
        In production, this would call the actual agent
        """
        # Different agents have different validation strategies
        if "validator" in agent_id:
            # Validator agent is strict
            vote = "accept" if finding.confidence > 0.7 else "more_info"
            confidence = finding.confidence
            rationale = f"Confidence threshold {'met' if vote == 'accept' else 'not met'}"
        
        elif "exploit" in agent_id:
            # Exploit agent checks if exploitation was successful
            vote = "accept" if finding.confidence > 0.8 else "reject"
            confidence = 0.9 if vote == "accept" else 0.3
            rationale = "Exploitation attempt " + ("succeeded" if vote == "accept" else "failed")
        
        elif "recon" in agent_id:
            # Recon agent validates based on information gathering
            vote = "accept" if finding.severity in ["critical", "high"] else "more_info"
            confidence = 0.7
            rationale = "Severity level indicates " + ("high risk" if vote == "accept" else "needs more analysis")
        
        else:
            # Default voting logic
            vote = "accept" if finding.confidence > 0.6 else "more_info"
            confidence = finding.confidence
            rationale = "Standard validation check"
        
        return {
            "vote": vote,
            "rationale": rationale,
            "confidence": confidence,
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _calculate_consensus(self, votes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate consensus from multiple agent votes
        
        Args:
            votes: List of vote dictionaries
        
        Returns:
            Consensus decision and confidence
        """
        if not votes:
            return {"decision": "more_info", "confidence": 0.0}
        
        # Count votes
        accept_count = sum(1 for v in votes if v["vote"] == "accept")
        reject_count = sum(1 for v in votes if v["vote"] == "reject")
        more_info_count = sum(1 for v in votes if v["vote"] == "more_info")
        
        total_votes = len(votes)
        
        # Calculate weighted confidence
        total_confidence = sum(v["confidence"] for v in votes if v["vote"] == "accept")
        avg_confidence = total_confidence / max(accept_count, 1)
        
        # Determine consensus
        if accept_count > total_votes / 2:
            decision = "accept"
            confidence = avg_confidence
        elif reject_count > total_votes / 2:
            decision = "reject"
            confidence = 1.0 - avg_confidence
        else:
            decision = "more_info"
            confidence = 0.5
        
        return {
            "decision": decision,
            "confidence": confidence,
            "vote_breakdown": {
                "accept": accept_count,
                "reject": reject_count,
                "more_info": more_info_count
            },
            "total_agents": total_votes
        }
