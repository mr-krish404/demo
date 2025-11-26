import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, Circle, Clock } from 'lucide-react';

interface TestPlanProps {
  projectId: string;
  jobs: any[];
}

export default function TestPlan({ projectId, jobs }: TestPlanProps) {
  // WSTG test categories
  const testCategories = [
    {
      id: 'INFO',
      name: 'Information Gathering',
      tests: [
        { id: 'WSTG-INFO-01', name: 'Conduct Search Engine Discovery', agent: 'recon-agent' },
        { id: 'WSTG-INFO-02', name: 'Fingerprint Web Server', agent: 'recon-agent' },
        { id: 'WSTG-INFO-03', name: 'Review Webserver Metafiles', agent: 'recon-agent' },
        { id: 'WSTG-INFO-04', name: 'Enumerate Applications', agent: 'recon-agent' },
      ],
    },
    {
      id: 'CONF',
      name: 'Configuration Management',
      tests: [
        { id: 'WSTG-CONF-01', name: 'Test Network Infrastructure', agent: 'recon-agent' },
        { id: 'WSTG-CONF-02', name: 'Test Application Platform', agent: 'recon-agent' },
      ],
    },
    {
      id: 'IDNT',
      name: 'Identity Management',
      tests: [
        { id: 'WSTG-IDNT-01', name: 'Test Role Definitions', agent: 'auth-agent' },
        { id: 'WSTG-IDNT-02', name: 'Test User Registration', agent: 'auth-agent' },
        { id: 'WSTG-IDNT-03', name: 'Test Account Provisioning', agent: 'auth-agent' },
      ],
    },
    {
      id: 'ATHN',
      name: 'Authentication',
      tests: [
        { id: 'WSTG-ATHN-01', name: 'Test Credentials Transport', agent: 'auth-agent' },
        { id: 'WSTG-ATHN-02', name: 'Test Default Credentials', agent: 'auth-agent' },
        { id: 'WSTG-ATHN-03', name: 'Test Weak Lock Out', agent: 'auth-agent' },
        { id: 'WSTG-ATHN-04', name: 'Test Bypass Authentication', agent: 'auth-agent' },
      ],
    },
    {
      id: 'SESS',
      name: 'Session Management',
      tests: [
        { id: 'WSTG-SESS-01', name: 'Test Session Management Schema', agent: 'session-agent' },
        { id: 'WSTG-SESS-02', name: 'Test Cookie Attributes', agent: 'session-agent' },
        { id: 'WSTG-SESS-03', name: 'Test Session Fixation', agent: 'session-agent' },
      ],
    },
    {
      id: 'INPV',
      name: 'Input Validation',
      tests: [
        { id: 'WSTG-INPV-01', name: 'Test Reflected XSS', agent: 'fuzz-agent' },
        { id: 'WSTG-INPV-02', name: 'Test Stored XSS', agent: 'fuzz-agent' },
        { id: 'WSTG-INPV-05', name: 'Test SQL Injection', agent: 'fuzz-agent' },
        { id: 'WSTG-INPV-12', name: 'Test Command Injection', agent: 'fuzz-agent' },
      ],
    },
  ];

  const getTestStatus = (testId: string) => {
    const job = jobs.find(j => j.test_case_id === testId);
    if (!job) return 'pending';
    return job.status;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'running':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <Circle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getCategoryProgress = (category: any) => {
    const completed = category.tests.filter((t: any) => getTestStatus(t.id) === 'completed').length;
    return Math.round((completed / category.tests.length) * 100);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>WSTG Test Plan</CardTitle>
          <CardDescription>
            Automated testing based on OWASP Web Security Testing Guide
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">
                {jobs.filter(j => j.status === 'completed').length}
              </p>
              <p className="text-sm text-slate-600">Completed</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-yellow-600">
                {jobs.filter(j => j.status === 'running').length}
              </p>
              <p className="text-sm text-slate-600">Running</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-slate-600">
                {jobs.filter(j => j.status === 'queued').length}
              </p>
              <p className="text-sm text-slate-600">Queued</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {testCategories.map((category) => (
        <Card key={category.id}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">{category.name}</CardTitle>
              <Badge variant="outline">
                {getCategoryProgress(category)}% Complete
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {category.tests.map((test) => {
                const status = getTestStatus(test.id);
                return (
                  <div
                    key={test.id}
                    className="flex items-center justify-between p-3 bg-slate-50 rounded hover:bg-slate-100 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(status)}
                      <div>
                        <p className="text-sm font-medium">{test.name}</p>
                        <p className="text-xs text-slate-500">{test.id}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline" className="text-xs">
                        {test.agent}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={`text-xs capitalize ${
                          status === 'completed' ? 'bg-green-50 text-green-700' :
                          status === 'running' ? 'bg-blue-50 text-blue-700' :
                          'bg-slate-50 text-slate-700'
                        }`}
                      >
                        {status}
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
