import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { FileImage, FileText, Video, Download, Eye } from 'lucide-react';
import { apiClient } from '../api/client';

interface EvidenceProps {
  projectId: string;
  findings: any[];
}

export default function Evidence({ projectId, findings }: EvidenceProps) {
  const [selectedFinding, setSelectedFinding] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedFinding) {
      loadEvidence(selectedFinding);
    }
  }, [selectedFinding]);

  const loadEvidence = async (findingId: string) => {
    setLoading(true);
    try {
      const data = await apiClient.getEvidence(findingId);
      setEvidence(data);
    } catch (err) {
      console.error('Failed to load evidence:', err);
    } finally {
      setLoading(false);
    }
  };

  const getEvidenceIcon = (type: string) => {
    switch (type) {
      case 'screenshot':
        return <FileImage className="h-5 w-5" />;
      case 'video':
        return <Video className="h-5 w-5" />;
      default:
        return <FileText className="h-5 w-5" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="grid grid-cols-3 gap-6">
      {/* Findings List */}
      <div className="col-span-1 space-y-2">
        <h3 className="font-medium mb-4">Findings with Evidence</h3>
        {findings.filter(f => f.evidence_count > 0).map((finding) => (
          <Card
            key={finding.id}
            className={`cursor-pointer transition-colors ${
              selectedFinding === finding.id ? 'border-blue-500 bg-blue-50' : 'hover:bg-slate-50'
            }`}
            onClick={() => setSelectedFinding(finding.id)}
          >
            <CardContent className="py-3">
              <p className="text-sm font-medium line-clamp-2">{finding.title}</p>
              <div className="flex items-center justify-between mt-2">
                <Badge variant="outline" className="text-xs">
                  {finding.evidence_count || 0} files
                </Badge>
                <Badge className={`text-xs ${
                  finding.severity === 'critical' ? 'bg-red-500' :
                  finding.severity === 'high' ? 'bg-orange-500' :
                  finding.severity === 'medium' ? 'bg-yellow-500' :
                  'bg-green-500'
                }`}>
                  {finding.severity}
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
        {findings.filter(f => f.evidence_count > 0).length === 0 && (
          <p className="text-sm text-slate-500 text-center py-8">No evidence available yet</p>
        )}
      </div>

      {/* Evidence Details */}
      <div className="col-span-2">
        {!selectedFinding ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Eye className="h-12 w-12 mx-auto text-slate-400" />
              <p className="mt-4 text-slate-600">Select a finding to view evidence</p>
            </CardContent>
          </Card>
        ) : loading ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p>Loading evidence...</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {evidence.map((item) => (
              <Card key={item.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getEvidenceIcon(item.type)}
                      <CardTitle className="text-base">{item.filename}</CardTitle>
                    </div>
                    <Button size="sm" variant="outline">
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-600">Type:</span>
                      <Badge variant="outline">{item.type}</Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-600">Size:</span>
                      <span>{formatFileSize(item.size_bytes || 0)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-600">Created:</span>
                      <span>{new Date(item.created_at).toLocaleString()}</span>
                    </div>
                    
                    {/* Preview for screenshots */}
                    {item.type === 'screenshot' && item.storage_key && (
                      <div className="mt-4 border rounded p-2">
                        <img
                          src={`/api/evidence/${item.id}/download`}
                          alt="Evidence screenshot"
                          className="w-full h-auto rounded"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                          }}
                        />
                      </div>
                    )}
                    
                    {/* Preview for text/JSON */}
                    {(item.type === 'raw_request' || item.type === 'raw_response' || item.type === 'log') && (
                      <div className="mt-4 bg-slate-900 text-slate-100 p-4 rounded text-xs font-mono overflow-x-auto max-h-64">
                        <pre>{item.content || 'Content not available'}</pre>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
            {evidence.length === 0 && (
              <Card>
                <CardContent className="py-12 text-center">
                  <p className="text-slate-600">No evidence files found</p>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
