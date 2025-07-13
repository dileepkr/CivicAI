
import React, { useState } from 'react';
import PolicyList from '@/components/PolicyList';
import DebatePanel from '@/components/DebatePanel';
import EmailGenerator from '@/components/EmailGenerator';

interface Policy {
  id: string;
  title: string;
  date: string;
  summary: string;
  relevance: 'high' | 'medium' | 'low';
}

const Index = () => {
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null);
  const [showEmailGenerator, setShowEmailGenerator] = useState(false);
  const [debateMessages, setDebateMessages] = useState<any[]>([]);

  const handlePolicySelect = (policy: Policy) => {
    setSelectedPolicy(policy);
    setShowEmailGenerator(false);
    setDebateMessages([]); // Clear messages when policy changes
  };

  const handleGenerateEmail = () => {
    setShowEmailGenerator(true);
  };

  const handleMessagesChange = (messages: any[]) => {
    setDebateMessages(messages);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            SF Policy Discussion Platform
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Engage with AI agents to understand and advocate for policies in San Francisco. Enter your area of interest or upload agreements to search for relevant upcoming policies.
          </p>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-88px)]">
        {/* Left Panel - Policy List */}
        <div className="w-1/3 bg-white border-r shadow-sm">
          <PolicyList 
            onPolicySelect={handlePolicySelect}
            selectedPolicy={selectedPolicy}
          />
        </div>

        {/* Center Panel - Debate */}
        <div className="w-1/3 bg-white border-r shadow-sm">
          <DebatePanel 
            selectedPolicy={selectedPolicy}
            onGenerateEmail={handleGenerateEmail}
            onMessagesChange={handleMessagesChange}
          />
        </div>

        {/* Right Panel - Email Generator */}
        <div className="w-1/3 bg-white shadow-sm">
          <EmailGenerator 
            selectedPolicy={selectedPolicy}
            debateMessages={debateMessages}
          />
        </div>
      </div>
    </div>
  );
};

export default Index;
