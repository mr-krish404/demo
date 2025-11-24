import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Shield, ArrowLeft, Play, AlertCircle, CheckCircle, Clock } from 'lucide-react';

interface Project {
  id: string;
  name: string;
  description: string;
  status: string;
}

interface Finding {
  id: string;
  title: string;
  severity: string;
  confidence: number;
  status: string;
  affected_url: string;
}

interface Job {
  id: string;
  agent_id: string;
  status: string;
  created_at: string;
}

export default function ProjectDetail() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProjectData();
  }, [projectId]);

  const loadProjectData = async () => {
    try {
      const [projectData, findingsData, jobsData] = await Promise.all([
        apiClient.getProject(projectId!),
        apiClient.getFindings(projectId!),
        apiClient.getJobs(projectId!),
      ]);
      setProject(projectData);
      setFindings(findingsData);
      setJobs(jobsData);
    } catch (err) {
      console.error('Failed to load project data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartScan = async () => {
    try {
      await apiClient.startScan(projectId!);
      loadProjectData();
    } catch (err) {
      console.error('Failed to start scan:', err);
    }
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-500',
      high: 'bg-orange-500',
      medium: 'bg-yellow-500',
      low: 'bg-green-500',
      info: 'bg-blue-500',
    };
    return colors[severity] || 'bg-gray-500';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Button variant="ghost" onClick={() => navigate('/dashboard')}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
              <Shield className="h-8 w-8 text-blue-600 ml-4" />
              <span className="ml-2 text-xl font-bold text-slate-900">
                {project?.name}
              </span>
            </div>
            <div className="flex items-center">
              <Button onClick={handleStartScan}>
                <Play className="h-4 w-4 mr-2" />
                Start Scan
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="findings">Findings</TabsTrigger>
            <TabsTrigger value="jobs">Jobs</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Project Information</CardTitle>
                <CardDescription>{project?.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-600">Status</p>
                    <p className="text-lg font-medium capitalize">{project?.status}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">Total Findings</p>
                    <p className="text-lg font-medium">{findings.length}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Findings Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-5 gap-4">
                  {['critical', 'high', 'medium', 'low', 'info'].map((severity) => (
                    <div key={severity} className="text-center">
                      <div className={`h-12 w-12 rounded-full ${getSeverityColor(severity)} mx-auto flex items-center justify-center text-white font-bold`}>
                        {findings.filter(f => f.severity === severity).length}
                      </div>
                      <p className="mt-2 text-sm capitalize text-slate-600">{severity}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="findings" className="space-y-4">
            {findings.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <AlertCircle className="h-12 w-12 mx-auto text-slate-400" />
                  <p className="mt-4 text-slate-600">No findings yet</p>
                </CardContent>
              </Card>
            ) : (
              findings.map((finding) => (
                <Card key={finding.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg">{finding.title}</CardTitle>
                        <CardDescription className="mt-1">
                          {finding.affected_url}
                        </CardDescription>
                      </div>
                      <Badge className={getSeverityColor(finding.severity)}>
                        {finding.severity.toUpperCase()}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center space-x-4 text-sm text-slate-600">
                      <span>Confidence: {(finding.confidence * 100).toFixed(0)}%</span>
                      <span>Status: {finding.status}</span>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </TabsContent>

          <TabsContent value="jobs" className="space-y-4">
            {jobs.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <Clock className="h-12 w-12 mx-auto text-slate-400" />
                  <p className="mt-4 text-slate-600">No jobs yet</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-2">
                {jobs.map((job) => (
                  <Card key={job.id}>
                    <CardContent className="py-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          {job.status === 'completed' ? (
                            <CheckCircle className="h-5 w-5 text-green-500" />
                          ) : job.status === 'running' ? (
                            <Clock className="h-5 w-5 text-blue-500 animate-spin" />
                          ) : (
                            <AlertCircle className="h-5 w-5 text-slate-400" />
                          )}
                          <div>
                            <p className="font-medium">{job.agent_id}</p>
                            <p className="text-sm text-slate-600">
                              {new Date(job.created_at).toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <Badge variant="outline" className="capitalize">
                          {job.status}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
