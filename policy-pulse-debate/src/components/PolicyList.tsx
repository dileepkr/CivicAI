
import React, { useState, useEffect } from 'react';
import { Upload, FileText, Calendar, Users, Search, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiClient, Policy } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface PolicyListProps {
  onPolicySelect: (policy: Policy) => void;
  selectedPolicy: Policy | null;
}

const PolicyList: React.FC<PolicyListProps> = ({ onPolicySelect, selectedPolicy }) => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [searchText, setSearchText] = useState<string>('');
  const [hasSearched, setHasSearched] = useState<boolean>(false);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  // Load policies from backend on component mount
  useEffect(() => {
    loadPolicies();
  }, []);

  const loadPolicies = async () => {
    try {
      setLoading(true);
      setError(null);
      const fetchedPolicies = await apiClient.getPolicies();
      setPolicies(fetchedPolicies);
      setHasSearched(true);
      
      toast({
        title: "Policies loaded",
        description: `Found ${fetchedPolicies.length} policies`,
      });
    } catch (err) {
      console.error('Error loading policies:', err);
      setError('Failed to load policies. Please ensure the backend is running.');
      toast({
        title: "Error loading policies",
        description: "Failed to connect to the backend API",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      toast({
        title: "File uploaded",
        description: `${file.name} has been uploaded`,
      });
    }
  };

  const handleSearch = async () => {
    if (!searchText.trim() && !uploadedFile) {
      toast({
        title: "Search required",
        description: "Please enter search text or upload a file",
        variant: "destructive",
      });
      return;
    }
    
    setLoading(true);
    try {
      // For now, just filter existing policies
      // TODO: Implement actual search functionality when backend supports it
      const filteredPolicies = policies.filter(policy => 
        policy.title.toLowerCase().includes(searchText.toLowerCase()) ||
        policy.summary.toLowerCase().includes(searchText.toLowerCase())
      );
      
      setPolicies(filteredPolicies);
      setHasSearched(true);
      
      toast({
        title: "Search completed",
        description: `Found ${filteredPolicies.length} matching policies`,
      });
    } catch (err) {
      console.error('Error searching policies:', err);
      toast({
        title: "Search error",
        description: "Failed to search policies",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };



  const getRelevanceColor = (relevance: string) => {
    switch (relevance) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b bg-blue-50">
        <h2 className="text-xl font-bold text-gray-800 mb-2">SF Policies</h2>
        <p className="text-sm text-gray-600">Latest policies affecting San Francisco residents</p>
      </div>

      {/* Upload Section */}
      <div className="p-4 border-b bg-white">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Upload className="w-4 h-4" />
              Upload Agreement
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <label className="flex flex-col items-center justify-center w-full h-24 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors">
                <div className="flex flex-col items-center justify-center pt-2 pb-3">
                  <FileText className="w-6 h-6 mb-1 text-gray-500" />
                  <p className="text-xs text-gray-500">Click to upload PDF</p>
                </div>
                <input type="file" className="hidden" accept=".pdf" onChange={handleFileUpload} />
              </label>
              {uploadedFile ? (
                <div className="flex items-center gap-2 text-sm text-green-600">
                  <FileText className="w-4 h-4" />
                  <span className="truncate">{uploadedFile.name}</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <FileText className="w-3 h-3" />
                  <span className="italic">Example: rental_agreement_July2025_SF.pdf</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search Section */}
      <div className="p-4 border-b bg-white">
        <div className="flex gap-2">
          <Input
            placeholder="Enter area of interest (e.g., housing, transportation, environment)"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="flex-1"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSearch();
              }
            }}
          />
          <Button 
            onClick={handleSearch} 
            className="flex items-center gap-2"
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
            Search
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {error}
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Policies List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-full">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500 mb-4" />
            <p className="text-sm text-gray-600">Loading policies...</p>
          </div>
        ) : !hasSearched ? (
          // Show message before search
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <Search className="w-12 h-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-600 mb-2">Search for Policies</h3>
            <p className="text-sm text-gray-500 max-w-sm">
              Enter your area of interest or upload an agreement to find relevant upcoming policies
            </p>
          </div>
        ) : policies.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <FileText className="w-12 h-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-600 mb-2">No Policies Found</h3>
            <p className="text-sm text-gray-500 max-w-sm">
              No policies match your search criteria. Try different keywords or check the backend connection.
            </p>
          </div>
        ) : selectedPolicy ? (
          // Show only selected policy
          <Card 
            className="ring-2 ring-blue-500 bg-blue-50 cursor-pointer"
            onClick={() => onPolicySelect(selectedPolicy)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-sm text-gray-800 leading-tight">{selectedPolicy.title}</h3>
                <span className={`px-2 py-1 rounded-full text-xs border ${getRelevanceColor(selectedPolicy.relevance)}`}>
                  {selectedPolicy.relevance}
                </span>
              </div>
              <p className="text-xs text-gray-600 mb-2">{selectedPolicy.summary}</p>
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <Calendar className="w-3 h-3" />
                <span>{new Date(selectedPolicy.date).toLocaleDateString()}</span>
              </div>
            </CardContent>
          </Card>
        ) : (
          // Show all policies
          policies.map((policy) => (
            <Card 
              key={policy.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => onPolicySelect(policy)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-sm text-gray-800 leading-tight">{policy.title}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs border ${getRelevanceColor(policy.relevance)}`}>
                    {policy.relevance}
                  </span>
                </div>
                <p className="text-xs text-gray-600 mb-2">{policy.summary}</p>
                <div className="flex items-center gap-1 text-xs text-gray-500">
                  <Calendar className="w-3 h-3" />
                  <span>{new Date(policy.date).toLocaleDateString()}</span>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default PolicyList;
