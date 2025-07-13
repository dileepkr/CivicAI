
import React, { useState } from 'react';
import { Upload, FileText, Calendar, Users, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

interface Policy {
  id: string;
  title: string;
  date: string;
  summary: string;
  relevance: 'high' | 'medium' | 'low';
}

interface PolicyListProps {
  onPolicySelect: (policy: Policy) => void;
  selectedPolicy: Policy | null;
}

const PolicyList: React.FC<PolicyListProps> = ({ onPolicySelect, selectedPolicy }) => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [searchText, setSearchText] = useState<string>('');
  const [hasSearched, setHasSearched] = useState<boolean>(false);

  const policies: Policy[] = [
    {
      id: '1',
      title: 'Tenant Protection Act 2024',
      date: '2024-01-15',
      summary: 'Enhanced protections against unfair evictions and rent gouging',
      relevance: 'high'
    },
    {
      id: '2',
      title: 'Rental Registration Ordinance',
      date: '2024-02-01',
      summary: 'Mandatory registration of all rental units with the city',
      relevance: 'high'
    },
    {
      id: '3',
      title: 'Housing Stability Policy',
      date: '2024-01-28',
      summary: 'New guidelines for lease renewals and tenant rights',
      relevance: 'medium'
    },
    {
      id: '4',
      title: 'Rent Control Expansion',
      date: '2024-02-10',
      summary: 'Extended rent control to buildings constructed after 1979',
      relevance: 'high'
    }
  ];

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
    }
  };

  const handleSearch = () => {
    // TODO: Implement search functionality for relevant, upcoming policies
    console.log('Searching for policies:', searchText);
    console.log('Uploaded file:', uploadedFile?.name);
    setHasSearched(true);
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
          />
          <Button onClick={handleSearch} className="flex items-center gap-2">
            <Search className="w-4 h-4" />
            Search
          </Button>
        </div>
      </div>

      {/* Policies List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {!hasSearched ? (
          // Show message before search
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <Search className="w-12 h-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-600 mb-2">Search for Policies</h3>
            <p className="text-sm text-gray-500 max-w-sm">
              Enter your area of interest or upload an agreement to find relevant upcoming policies
            </p>
          </div>
        ) : selectedPolicy ? (
          // Show only selected policy
          <Card 
            className="ring-2 ring-blue-500 bg-blue-50"
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
          // Show all policies when none selected after search
          policies.map((policy) => (
            <Card 
              key={policy.id}
              className="cursor-pointer transition-all hover:shadow-md hover:bg-gray-50"
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
