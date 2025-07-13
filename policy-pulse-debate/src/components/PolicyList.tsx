
import React, { useState, useEffect } from 'react';
import { Search, Loader2, AlertCircle, Sparkles, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { 
  apiClient, 
  Policy, 
  DiscoveredPolicy,
  PolicySearchRequest
} from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface PolicyListProps {
  onPolicySelect: (policy: Policy | DiscoveredPolicy) => void;
  selectedPolicy: Policy | DiscoveredPolicy | null;
}

const PolicyList: React.FC<PolicyListProps> = ({ onPolicySelect, selectedPolicy }) => {
  const [searchPrompt, setSearchPrompt] = useState<string>('');
  const [discoveredPolicies, setDiscoveredPolicies] = useState<DiscoveredPolicy[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState<boolean>(false);
  const [policyAnalysis, setPolicyAnalysis] = useState<any>(null);
  const { toast } = useToast();

  const handlePromptSearch = async () => {
    if (!searchPrompt.trim()) {
      toast({
        title: "Search prompt required",
        description: "Please enter a policy question or topic to search for",
        variant: "destructive",
      });
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      // Use the new natural language search endpoint
      const request: PolicySearchRequest = {
        prompt: searchPrompt,
        max_results: 20
      };
      
      const response = await apiClient.searchPolicies(request);
      
      if (response.success) {
        setDiscoveredPolicies(response.priority_policies);
        setPolicyAnalysis(response.policy_analysis);
        setHasSearched(true);
        
        toast({
          title: "Policy search completed",
          description: `Found ${response.total_found} relevant policies in ${response.search_time.toFixed(1)}s`,
        });
      } else {
        setError(response.error || 'Policy search failed');
        toast({
          title: "Search failed",
          description: response.error || "An error occurred during search",
          variant: "destructive",
        });
      }
    } catch (err) {
      console.error('Error searching policies:', err);
      setError('Failed to search policies');
      toast({
        title: "Search failed",
        description: "An error occurred while searching for policies",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handlePromptSearch();
    }
  };

  const getRelevanceColor = (relevance: string) => {
    switch (relevance) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getGovernmentLevelColor = (level: string) => {
    switch (level) {
      case 'federal': return 'bg-blue-100 text-blue-800';
      case 'state': return 'bg-purple-100 text-purple-800';
      case 'local': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading && !hasSearched) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading policy discovery...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            AI Policy Discovery
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                What policy topic would you like to explore?
              </label>
              <div className="relative">
                <Textarea
                  placeholder="Ask about any policy topic... 

Examples:
• 'What are the rent control policies in San Francisco?'
• 'Show me housing policies for renters in California'
• 'What labor rights policies affect small business owners?'
• 'Tell me about environmental regulations in my area'"
                  value={searchPrompt}
                  onChange={(e) => setSearchPrompt(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="min-h-[120px] pr-12 resize-none"
                  disabled={loading}
                />
                <Button 
                  onClick={handlePromptSearch}
                  disabled={loading || !searchPrompt.trim()}
                  className="absolute bottom-2 right-2 h-8 w-8 p-0"
                  size="sm"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Sparkles className="h-4 w-4" />
              <span>
                Our AI will analyze your query and find relevant policies across federal, state, and local levels
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {policyAnalysis && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              AI Policy Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-700 mb-4">
              {policyAnalysis.answer}
            </p>
            {policyAnalysis.citations && (
              <div className="space-y-2">
                <h4 className="font-medium">Sources:</h4>
                <ul className="text-sm space-y-1">
                  {policyAnalysis.citations.map((citation: any, index: number) => (
                    <li key={index}>
                      <a href={citation.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                        {citation.title}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {hasSearched && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Discovered Policies ({discoveredPolicies.length})</h3>
              {discoveredPolicies.length > 0 && (
                <Badge variant="outline">
                  <Sparkles className="h-3 w-3 mr-1" />
                  AI-Powered Results
                </Badge>
              )}
            </div>
            
            {discoveredPolicies.map((policy) => (
              <Card 
                key={policy.id}
                className={`cursor-pointer transition-all ${
                  selectedPolicy?.id === policy.id ? 'ring-2 ring-blue-500' : 'hover:shadow-md'
                }`}
                onClick={() => onPolicySelect(policy)}
              >
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-lg">{policy.title}</CardTitle>
                    <div className="flex gap-2">
                      <Badge className={getGovernmentLevelColor(policy.government_level)}>
                        {policy.government_level}
                      </Badge>
                      <Badge variant="outline">{policy.domain}</Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-4">{policy.summary}</p>
                  
                  <div className="flex flex-wrap gap-2 mb-3">
                    <span className="text-xs text-gray-500">
                      {formatDate(policy.last_updated)}
                    </span>
                    <span className="text-xs text-gray-500">{policy.source_agency}</span>
                    <span className="text-xs text-gray-500">
                      Confidence: {(policy.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  
                  {policy.stakeholder_impacts && policy.stakeholder_impacts.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium">Stakeholder Impacts:</h4>
                      <div className="flex flex-wrap gap-2">
                        {policy.stakeholder_impacts.map((impact, index) => (
                          <Badge key={index} className={getSeverityColor(impact.severity)}>
                            {impact.group} - {impact.severity}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {!hasSearched && !loading && (
        <div className="text-center py-12">
          <Sparkles className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Ready to discover policies
          </h3>
          <p className="text-gray-600">
            Enter your policy question above and let our AI find relevant policies across all government levels.
          </p>
        </div>
      )}
    </div>
  );
};

export default PolicyList;
