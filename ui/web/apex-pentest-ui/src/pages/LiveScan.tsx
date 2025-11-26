import { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Activity, CheckCircle, Clock, XCircle } from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';

interface LiveScanProps {
  projectId: string;
  jobs: any[];
}

export default function LiveScan({ projectId, jobs }: LiveScanProps) {
  const { messages, isConnected } = useWebSocket(projectId);
  const [liveJobs, setLiveJobs] = useState(jobs);
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    setLiveJobs(jobs);
  }, [jobs]);

  useEffect(() => {
    // Process WebSocket messages
    messages.forEach((msg) => {
      if (msg.type === 'job_started' || msg.type === 'job_completed') {
        setEvents((prev) => [msg, ...prev].slice(0, 50)); // Keep last 50 events
        
        if (msg.type === 'job_started') {
          setLiveJobs((prev) => [...prev, msg.data]);
        } else if (msg.type === 'job_completed') {
          setLiveJobs((prev) =>
            prev.map((job) =>
              job.id === msg.data.id ? { ...job, status: 'completed' } : job
            )
          );
        }
      }
    });
  }, [messages]);

  const getAgentColor = (agentId: string) => {
    const colors: Record<string, string> = {
      'recon-agent': 'bg-blue-500',
      'fuzz-agent': 'bg-purple-500',
      'exploit-agent': 'bg-red-500',
      'validator-agent': 'bg-green-500',
      'session-agent': 'bg-yellow-500',
      'auth-agent': 'bg-orange-500',
      'learning-agent': 'bg-pink-500',
      'reporter-agent': 'bg-indigo-500',
    };
    return colors[agentId] || 'bg-gray-500';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'running':
        return <Activity className="h-5 w-5 text-blue-500 animate-pulse" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  // Group jobs by agent
  const agentGroups = liveJobs.reduce((acc, job) => {
    const agent = job.agent_id || 'unknown';
    if (!acc[agent]) acc[agent] = [];
    acc[agent].push(job);
    return acc;
  }, {} as Record<string, any[]>);

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className={`h-3 w-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
              <span className="text-sm font-medium">
                {isConnected ? 'Live Updates Active' : 'Disconnected'}
              </span>
            </div>
            <Badge variant="outline">
              {liveJobs.filter(j => j.status === 'running').length} Running
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Agent Swimlanes */}
      <Card>
        <CardHeader>
          <CardTitle>Agent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(agentGroups).map(([agentId, agentJobs]) => (
              <div key={agentId} className="border-l-4 pl-4" style={{ borderColor: getAgentColor(agentId).replace('bg-', '#') }}>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium capitalize">{agentId.replace('-', ' ')}</h3>
                  <Badge className={getAgentColor(agentId)}>
                    {agentJobs.length} jobs
                  </Badge>
                </div>
                <div className="space-y-2">
                  {agentJobs.slice(0, 5).map((job) => (
                    <div key={job.id} className="flex items-center justify-between bg-slate-50 p-2 rounded">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(job.status)}
                        <span className="text-sm text-slate-600">
                          {new Date(job.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                      <Badge variant="outline" className="capitalize text-xs">
                        {job.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Event Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Events</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {events.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No events yet</p>
            ) : (
              events.map((event, idx) => (
                <div key={idx} className="flex items-start space-x-3 text-sm border-b pb-2">
                  <Badge variant="outline" className="text-xs">
                    {event.type.replace('_', ' ')}
                  </Badge>
                  <div className="flex-1">
                    <p className="text-slate-700">
                      {event.type === 'job_started' && `Started ${event.data.agent_id}`}
                      {event.type === 'job_completed' && `Completed ${event.data.agent_id}`}
                      {event.type === 'finding_created' && `New finding: ${event.data.title}`}
                    </p>
                    <p className="text-xs text-slate-500">
                      {new Date(event.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
