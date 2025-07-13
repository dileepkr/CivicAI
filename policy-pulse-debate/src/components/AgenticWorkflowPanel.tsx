import React, { useState, useEffect } from 'react';
import { Play, Users, Search, Brain, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  apiClient, 
  AgenticPolicyAnalysisRequest,
  AgenticDebateRequest,
  CrewWorkflowRequest,
  AgenticWorkflowResponse,
  WorkflowDefinition,
  StakeholderInfo
} from '@/services/api';
import { useToast } from '@/hooks/use-toast';

const AgenticWorkflowPanel: React.FC = () => {
  const [availableWorkflows, setAvailableWorkflows] = useState<WorkflowDefinition[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [workflowResult, setWorkflowResult] = useState<AgenticWorkflowResponse | null>(null);
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const { toast } = useToast();

  // Form states
  const [policyName, setPolicyName] = useState<string>('');
  const [userLocation, setUserLocation] = useState<string>('San Francisco, CA');
  const [stakeholderRoles, setStakeholderRoles] = useState<string[]>(['renter', 'landlord']);
  const [interests, setInterests] = useState<string[]>(['rent control', 'housing rights']);
  const [stakeholders, setStakeholders] = useState<StakeholderInfo[]>([
    { name: 'Tenant Representative', type: 'renter', description: 'Advocates for tenant rights' },
    { name: 'Property Owner Representative', type: 'landlord', description: 'Represents landlord interests' }
  ]);

  useEffect(() => {
    loadWorkflows();
    checkSystemStatus();
  }, []);

  const loadWorkflows = async () => {
    try {
      const response = await apiClient.getAvailableWorkflows();
      setAvailableWorkflows(response.workflows);
    } catch (error) {
      console.error('Failed to load workflows:', error);
      toast({
        title: "Error",
        description: "Failed to load available workflows",
        variant: "destructive",
      });
    }
  };

  const checkSystemStatus = async () => {
    try {
      const status = await apiClient.getCrewSystemStatus();
      setSystemStatus(status);
    } catch (error) {
      console.error('Failed to check system status:', error);
    }
  };

  const runPolicyAnalysis = async () => {
    if (!policyName.trim()) {
      toast({
        title: "Policy name required",
        description: "Please enter a policy name to analyze",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const request: AgenticPolicyAnalysisRequest = {
        policy_name: policyName,
        user_location: userLocation,
        stakeholder_roles: stakeholderRoles,
        interests: interests,
        analysis_type: 'comprehensive'
      };

      const result = await apiClient.runPolicyAnalysis(request);
      setWorkflowResult(result);
      
      if (result.success) {
        toast({
          title: "Analysis Complete",
          description: `Policy analysis completed in ${result.execution_time.toFixed(1)}s`,
        });
      } else {
        toast({
          title: "Analysis Failed",
          description: result.error || "Unknown error occurred",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Policy analysis failed:', error);
      toast({
        title: "Analysis Failed",
        description: "An error occurred during policy analysis",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const runStakeholderDebate = async () => {
    if (!policyName.trim()) {
      toast({
        title: "Policy name required",
        description: "Please enter a policy name for the debate",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const request: AgenticDebateRequest = {
        policy_name: policyName,
        policy_text: `Policy text for ${policyName}...`,
        stakeholders: stakeholders,
        debate_rounds: 3,
        debate_style: 'structured'
      };

      const result = await apiClient.runStakeholderDebate(request);
      setWorkflowResult(result);
      
      if (result.success) {
        toast({
          title: "Debate Complete",
          description: `Stakeholder debate completed in ${result.execution_time.toFixed(1)}s`,
        });
      } else {
        toast({
          title: "Debate Failed",
          description: result.error || "Unknown error occurred",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Stakeholder debate failed:', error);
      toast({
        title: "Debate Failed",
        description: "An error occurred during stakeholder debate",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const runCustomWorkflow = async () => {
    if (!selectedWorkflow) {
      toast({
        title: "Workflow required",
        description: "Please select a workflow type",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const request: CrewWorkflowRequest = {
        workflow_type: selectedWorkflow,
        policy_context: {
          policy_name: policyName,
          policy_text: `Policy text for ${policyName}...`
        },
        user_context: {
          location: userLocation,
          stakeholder_roles: stakeholderRoles,
          interests: interests
        }
      };

      const result = await apiClient.runCustomWorkflow(request);
      setWorkflowResult(result);
      
      if (result.success) {
        toast({
          title: "Workflow Complete",
          description: `${selectedWorkflow} completed in ${result.execution_time.toFixed(1)}s`,
        });
      } else {
        toast({
          title: "Workflow Failed",
          description: result.error || "Unknown error occurred",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Custom workflow failed:', error);
      toast({
        title: "Workflow Failed",
        description: "An error occurred during workflow execution",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Loader2 className="h-4 w-4 animate-spin" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Agentic System Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          {systemStatus && (
            <div className="flex items-center gap-2">
              <Badge variant={systemStatus.status === 'available' ? 'default' : 'destructive'}>
                {systemStatus.status}
              </Badge>
              <span className="text-sm text-gray-600">{systemStatus.message}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Workflow Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Policy Name</label>
            <Input
              value={policyName}
              onChange={(e) => setPolicyName(e.target.value)}
              placeholder="Enter policy name..."
            />
          </div>
          
          <div>
            <label className="text-sm font-medium">Location</label>
            <Input
              value={userLocation}
              onChange={(e) => setUserLocation(e.target.value)}
              placeholder="San Francisco, CA"
            />
          </div>

          <div>
            <label className="text-sm font-medium">Stakeholder Roles</label>
            <Textarea
              value={stakeholderRoles.join(', ')}
              onChange={(e) => setStakeholderRoles(e.target.value.split(', ').filter(Boolean))}
              placeholder="renter, landlord, business_owner..."
            />
          </div>

          <div>
            <label className="text-sm font-medium">Interests</label>
            <Textarea
              value={interests.join(', ')}
              onChange={(e) => setInterests(e.target.value.split(', ').filter(Boolean))}
              placeholder="rent control, housing rights, minimum wage..."
            />
          </div>
        </CardContent>
      </Card>

      {/* Workflow Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Agentic Workflows</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              onClick={runPolicyAnalysis}
              disabled={loading}
              className="flex items-center gap-2"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              Policy Analysis
            </Button>

            <Button
              onClick={runStakeholderDebate}
              disabled={loading}
              variant="outline"
              className="flex items-center gap-2"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Users className="h-4 w-4" />}
              Stakeholder Debate
            </Button>

            <div className="flex gap-2">
              <Select value={selectedWorkflow} onValueChange={setSelectedWorkflow}>
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="Custom Workflow" />
                </SelectTrigger>
                <SelectContent>
                  {availableWorkflows.map((workflow) => (
                    <SelectItem key={workflow.type} value={workflow.type}>
                      {workflow.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                onClick={runCustomWorkflow}
                disabled={loading || !selectedWorkflow}
                variant="outline"
                className="flex items-center gap-2"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                Run
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {workflowResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {getStatusIcon(workflowResult.status)}
              Workflow Results
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-sm font-medium">Workflow ID</div>
                <div className="text-sm text-gray-600">{workflowResult.workflow_id}</div>
              </div>
              <div>
                <div className="text-sm font-medium">Type</div>
                <div className="text-sm text-gray-600">{workflowResult.workflow_type}</div>
              </div>
              <div>
                <div className="text-sm font-medium">Status</div>
                <Badge variant={workflowResult.success ? 'default' : 'destructive'}>
                  {workflowResult.status}
                </Badge>
              </div>
              <div>
                <div className="text-sm font-medium">Execution Time</div>
                <div className="text-sm text-gray-600">{workflowResult.execution_time.toFixed(1)}s</div>
              </div>
            </div>

            {workflowResult.agents_involved.length > 0 && (
              <div>
                <div className="text-sm font-medium mb-2">Agents Involved</div>
                <div className="flex flex-wrap gap-2">
                  {workflowResult.agents_involved.map((agent, index) => (
                    <Badge key={index} variant="outline">{agent}</Badge>
                  ))}
                </div>
              </div>
            )}

            {workflowResult.error && (
              <Alert variant="destructive">
                <XCircle className="h-4 w-4" />
                <AlertDescription>{workflowResult.error}</AlertDescription>
              </Alert>
            )}

            {workflowResult.success && workflowResult.results && (
              <div>
                <div className="text-sm font-medium mb-2">Results Summary</div>
                <div className="bg-gray-50 p-4 rounded-md">
                  <pre className="text-xs overflow-auto max-h-96">
                    {JSON.stringify(workflowResult.results, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AgenticWorkflowPanel; 