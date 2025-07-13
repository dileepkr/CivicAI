
import React from 'react';
import ChatInterface from '@/components/ChatInterface';
import { Building, Users, MessageCircle, Mail, Globe } from 'lucide-react';

const Index = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Minimalistic Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                <Building className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">
                  SF Policy Discussion Platform
                </h1>
                <p className="text-sm text-gray-600">
                  AI-Powered Policy Discovery & Civic Engagement
                </p>
              </div>
            </div>
            
            {/* Simple feature indicators */}
            <div className="hidden md:flex items-center gap-4 text-xs text-gray-500">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span>AI-Powered</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span>Real-time Debates</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span>Advocacy Tools</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Chat Interface */}
      <div className="h-[calc(100vh-140px)] max-w-7xl mx-auto px-4 sm:px-6 py-4">
        <div className="h-full bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <ChatInterface />
        </div>
      </div>

      {/* Simple Footer */}
      <footer className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                <Globe className="w-3 h-3" />
                <span>San Francisco Focused</span>
              </div>
              <div className="flex items-center gap-1">
                <Users className="w-3 h-3" />
                <span>Multi-Stakeholder</span>
              </div>
            </div>
            <div>
              Powered by AI • Built for Civic Engagement
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;
