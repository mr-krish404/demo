"""
Learning Agent - Pattern clustering and optimization using ChromaDB
"""
import os
import sys
from typing import Dict, Any, List
import chromadb
from chromadb.config import Settings

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from shared.database import DatabaseManager, Finding, Job
from shared.config import settings

class LearningAgent:
    """Learns from historical findings to optimize future scans"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(settings.database_url)
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.HttpClient(
            host=settings.chromadb_url.replace("http://", "").split(":")[0],
            port=int(settings.chromadb_url.split(":")[-1]) if ":" in settings.chromadb_url else 8000
        )
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_or_create_collection(
                name="apex_findings",
                metadata={"description": "Historical vulnerability findings"}
            )
        except Exception as e:
            print(f"Warning: Could not connect to ChromaDB: {e}")
            self.collection = None
    
    def execute(self, project_id: str):
        """Execute learning on project findings"""
        session = next(self.db_manager.get_session())
        try:
            # Get all findings for the project
            findings = session.query(Finding).filter(Finding.project_id == project_id).all()
            
            if not findings:
                print("No findings to learn from")
                return
            
            print(f"Learning from {len(findings)} findings")
            
            # Store findings in vector database
            self.store_findings(findings)
            
            # Analyze patterns
            patterns = self.analyze_patterns(findings)
            
            # Generate recommendations
            recommendations = self.generate_recommendations(patterns)
            
            print(f"Learning completed. Found {len(patterns)} patterns")
            print(f"Generated {len(recommendations)} recommendations")
        
        except Exception as e:
            print(f"Error executing learning agent: {e}")
        finally:
            session.close()
    
    def store_findings(self, findings: List[Finding]):
        """Store findings in ChromaDB for similarity search"""
        if not self.collection:
            print("ChromaDB not available, skipping storage")
            return
        
        try:
            documents = []
            metadatas = []
            ids = []
            
            for finding in findings:
                # Create document text
                doc_text = f"{finding.title}. {finding.description}"
                documents.append(doc_text)
                
                # Create metadata
                metadata = {
                    "severity": finding.severity.value,
                    "confidence": finding.confidence,
                    "status": finding.status.value,
                    "affected_url": finding.affected_url or "",
                    "affected_parameter": finding.affected_parameter or ""
                }
                metadatas.append(metadata)
                
                ids.append(str(finding.id))
            
            # Add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"Stored {len(findings)} findings in ChromaDB")
        
        except Exception as e:
            print(f"Error storing findings: {e}")
    
    def analyze_patterns(self, findings: List[Finding]) -> List[Dict[str, Any]]:
        """Analyze patterns in findings"""
        patterns = []
        
        # Group by severity
        severity_counts = {}
        for finding in findings:
            severity = finding.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        patterns.append({
            "type": "severity_distribution",
            "data": severity_counts
        })
        
        # Group by affected parameter
        param_counts = {}
        for finding in findings:
            if finding.affected_parameter:
                param = finding.affected_parameter
                param_counts[param] = param_counts.get(param, 0) + 1
        
        if param_counts:
            patterns.append({
                "type": "vulnerable_parameters",
                "data": param_counts
            })
        
        # Group by vulnerability type
        vuln_types = {}
        for finding in findings:
            # Extract vulnerability type from title
            title_lower = finding.title.lower()
            if "xss" in title_lower or "cross-site" in title_lower:
                vuln_type = "XSS"
            elif "sql" in title_lower:
                vuln_type = "SQL Injection"
            elif "command" in title_lower:
                vuln_type = "Command Injection"
            elif "auth" in title_lower:
                vuln_type = "Authentication"
            else:
                vuln_type = "Other"
            
            vuln_types[vuln_type] = vuln_types.get(vuln_type, 0) + 1
        
        patterns.append({
            "type": "vulnerability_types",
            "data": vuln_types
        })
        
        return patterns
    
    def generate_recommendations(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on patterns"""
        recommendations = []
        
        for pattern in patterns:
            if pattern["type"] == "severity_distribution":
                critical_count = pattern["data"].get("critical", 0)
                high_count = pattern["data"].get("high", 0)
                
                if critical_count > 0:
                    recommendations.append(
                        f"Found {critical_count} critical vulnerabilities. Prioritize immediate remediation."
                    )
                
                if high_count > 3:
                    recommendations.append(
                        f"Found {high_count} high-severity vulnerabilities. Consider security code review."
                    )
            
            elif pattern["type"] == "vulnerable_parameters":
                # Find most vulnerable parameters
                sorted_params = sorted(
                    pattern["data"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                if sorted_params:
                    top_param = sorted_params[0]
                    recommendations.append(
                        f"Parameter '{top_param[0]}' is frequently vulnerable ({top_param[1]} findings). "
                        f"Implement strict input validation."
                    )
            
            elif pattern["type"] == "vulnerability_types":
                # Find most common vulnerability type
                sorted_types = sorted(
                    pattern["data"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                if sorted_types:
                    top_type = sorted_types[0]
                    recommendations.append(
                        f"{top_type[0]} is the most common vulnerability type ({top_type[1]} findings). "
                        f"Focus security training on this area."
                    )
        
        return recommendations
    
    def find_similar_findings(self, finding_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Find similar historical findings"""
        if not self.collection:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[finding_text],
                n_results=n_results
            )
            
            similar_findings = []
            if results and results["ids"]:
                for i, finding_id in enumerate(results["ids"][0]):
                    similar_findings.append({
                        "id": finding_id,
                        "distance": results["distances"][0][i] if "distances" in results else None,
                        "metadata": results["metadatas"][0][i] if "metadatas" in results else {}
                    })
            
            return similar_findings
        
        except Exception as e:
            print(f"Error finding similar findings: {e}")
            return []

def main():
    """Main entry point"""
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        print("No PROJECT_ID provided")
        return
    
    agent = LearningAgent()
    agent.execute(project_id)

if __name__ == "__main__":
    main()
