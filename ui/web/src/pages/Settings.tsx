import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Save, Trash2, Plus } from 'lucide-react';

interface SettingsProps {
  projectId: string;
  project: any;
}

export default function Settings({ projectId, project }: SettingsProps) {
  const [targets, setTargets] = useState<string[]>([]);
  const [newTarget, setNewTarget] = useState('');
  const [concurrency, setConcurrency] = useState(4);
  const [rateLimit, setRateLimit] = useState(10);

  const handleAddTarget = () => {
    if (newTarget.trim()) {
      setTargets([...targets, newTarget.trim()]);
      setNewTarget('');
    }
  };

  const handleRemoveTarget = (index: number) => {
    setTargets(targets.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Project Settings</CardTitle>
          <CardDescription>Configure scan parameters and targets</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label htmlFor="project-name">Project Name</Label>
            <Input
              id="project-name"
              defaultValue={project?.name}
              className="mt-2"
            />
          </div>
          
          <div>
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              defaultValue={project?.description}
              className="mt-2"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Scan Targets</CardTitle>
          <CardDescription>Add URLs or IP ranges to scan</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex space-x-2">
            <Input
              placeholder="https://example.com or 192.168.1.0/24"
              value={newTarget}
              onChange={(e) => setNewTarget(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAddTarget()}
            />
            <Button onClick={handleAddTarget}>
              <Plus className="h-4 w-4 mr-2" />
              Add
            </Button>
          </div>
          
          <div className="space-y-2">
            {targets.map((target, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded">
                <span className="text-sm">{target}</span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleRemoveTarget(index)}
                >
                  <Trash2 className="h-4 w-4 text-red-500" />
                </Button>
              </div>
            ))}
            {targets.length === 0 && (
              <p className="text-sm text-slate-500 text-center py-4">No targets added yet</p>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Scan Configuration</CardTitle>
          <CardDescription>Adjust performance and rate limiting</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label htmlFor="concurrency">Concurrent Agents</Label>
            <Input
              id="concurrency"
              type="number"
              min="1"
              max="10"
              value={concurrency}
              onChange={(e) => setConcurrency(parseInt(e.target.value))}
              className="mt-2"
            />
            <p className="text-xs text-slate-500 mt-1">
              Number of agents running simultaneously (1-10)
            </p>
          </div>
          
          <div>
            <Label htmlFor="rate-limit">Rate Limit (req/sec)</Label>
            <Input
              id="rate-limit"
              type="number"
              min="1"
              max="100"
              value={rateLimit}
              onChange={(e) => setRateLimit(parseInt(e.target.value))}
              className="mt-2"
            />
            <p className="text-xs text-slate-500 mt-1">
              Maximum requests per second to target
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Test Selection</CardTitle>
          <CardDescription>Choose which test categories to run</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3">
            {[
              'Information Gathering',
              'Configuration Management',
              'Identity Management',
              'Authentication',
              'Session Management',
              'Input Validation',
              'Error Handling',
              'Cryptography',
            ].map((category) => (
              <label key={category} className="flex items-center space-x-2 p-2 border rounded hover:bg-slate-50 cursor-pointer">
                <input type="checkbox" defaultChecked className="rounded" />
                <span className="text-sm">{category}</span>
              </label>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end space-x-2">
        <Button variant="outline">Cancel</Button>
        <Button>
          <Save className="h-4 w-4 mr-2" />
          Save Settings
        </Button>
      </div>
    </div>
  );
}
