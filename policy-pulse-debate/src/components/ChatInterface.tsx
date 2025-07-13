import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, User, Bot, FileText, MessageCircle, Mail, Search, Users, ChevronDown, ChevronUp, Building, Globe, Home, Shield, Briefcase, Heart, Calendar, Star } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { 
  apiClient, 
  Policy, 
  DiscoveredPolicy,
  PolicySearchRequest,
  PolicyDiscoveryRequest,
  DebateMessage,
  EmailGenerationRequest,
  AgenticDebateRequest,
  AgenticWorkflowResponse,
  createDebateWebSocket,
  DebateWebSocketClient
} from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface ChatMessage {
  id: string;
  type: 'user' | 'bot' | 'system';
  content: string;
  timestamp: Date;
  data?: {
    type?: string;
    policy?: DiscoveredPolicy;
    policies?: DiscoveredPolicy[];
    actions?: ChatAction[];
    emailContent?: string;
    recipients?: string[];
    debateResult?: AgenticWorkflowResponse;
    debateMessages?: DebateMessage[];
    selectedPolicy?: DiscoveredPolicy;
    messageId?: string;
    debateMessage?: DebateMessage;
    round?: number;
    roundType?: string;
  };
  actions?: ChatAction[];
}

interface ChatAction {
  id: string;
  label: string;
  type: 'policy_select' | 'start_debate' | 'generate_email' | 'search_more' | 'analyze_policy' | 'explain_policy';
  data?: DiscoveredPolicy | { policy: DiscoveredPolicy; debateMessages?: DebateMessage[] };
}

// Enhanced markdown processor for LLM responses
const processMarkdown = (text: string): JSX.Element => {
  if (!text) return <></>;
  
  // Process line by line to handle different markdown patterns
  const lines = text.split('\n');
  
  return (
    <>
      {lines.map((line, lineIndex) => {
        // Handle headers
        if (line.startsWith('### ')) {
          return <h3 key={lineIndex} className="text-lg font-semibold mt-3 mb-2">{line.slice(4)}</h3>;
        }
        if (line.startsWith('## ')) {
          return <h2 key={lineIndex} className="text-xl font-semibold mt-4 mb-2">{line.slice(3)}</h2>;
        }
        if (line.startsWith('# ')) {
          return <h1 key={lineIndex} className="text-2xl font-bold mt-4 mb-3">{line.slice(2)}</h1>;
        }
        
        // Handle bullet points
        if (line.match(/^[\s]*[-*+]\s+/)) {
          const content = line.replace(/^[\s]*[-*+]\s+/, '');
          return (
            <div key={lineIndex} className="flex items-start gap-2 my-1">
              <span className="text-gray-500 mt-1">•</span>
              <span>{processInlineMarkdown(content)}</span>
            </div>
          );
        }
        
        // Handle numbered lists
        if (line.match(/^[\s]*\d+\.\s+/)) {
          const match = line.match(/^[\s]*(\d+)\.\s+(.*)$/);
          if (match) {
            return (
              <div key={lineIndex} className="flex items-start gap-2 my-1">
                <span className="text-gray-500 mt-1 font-medium">{match[1]}.</span>
                <span>{processInlineMarkdown(match[2])}</span>
              </div>
            );
          }
        }
        
        // Handle empty lines
        if (line.trim() === '') {
          return <br key={lineIndex} />;
        }
        
        // Handle regular paragraphs with inline formatting
        return (
          <div key={lineIndex} className="mb-2">
            {processInlineMarkdown(line)}
          </div>
        );
      })}
    </>
  );
};

// Process inline markdown within a line
const processInlineMarkdown = (text: string): JSX.Element => {
  if (!text) return <></>;
  
  // Split by inline markdown patterns while preserving them
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/);
  
  return (
    <>
      {parts.map((part, index) => {
        if (!part) return null;
        
        // Bold text **text**
        if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
          return <strong key={index} className="font-semibold">{part.slice(2, -2)}</strong>;
        }
        
        // Italic text *text* (but not **text**)
        if (part.startsWith('*') && part.endsWith('*') && part.length > 2 && !part.startsWith('**')) {
          return <em key={index} className="italic">{part.slice(1, -1)}</em>;
        }
        
        // Inline code `code`
        if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
          return (
            <code key={index} className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono border">
              {part.slice(1, -1)}
            </code>
          );
        }
        
        // Regular text
        return <span key={index}>{part}</span>;
      })}
    </>
  );
};

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState<DiscoveredPolicy | null>(null);
  const [debateMessages, setDebateMessages] = useState<DebateMessage[]>([]);
  const [isDebateActive, setIsDebateActive] = useState(false);
  const [expandedPolicies, setExpandedPolicies] = useState<Set<string>>(new Set());
  // Add WebSocket state management
  const [wsClient, setWsClient] = useState<DebateWebSocketClient | null>(null);
  const [currentDebateSession, setCurrentDebateSession] = useState<string | null>(null);
  const [isDebateConnected, setIsDebateConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Minimalistic welcome message with markdown formatting
    addBotMessage(
      "Hello! I'm your **SF Policy Assistant**. I can help you:\n\n• Discover relevant policies\n• Analyze their impact  \n• Facilitate discussions\n\nWhat policy area interests you today?"
    );
  }, []);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsClient) {
        wsClient.disconnect();
      }
    };
  }, [wsClient]);

  const addBotMessage = (content: string, data?: ChatMessage['data'], actions?: ChatAction[]) => {
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'bot',
      content,
      timestamp: new Date(),
      data,
      actions
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const addUserMessage = (content: string) => {
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const addSystemMessage = (content: string, data?: ChatMessage['data']) => {
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'system',
      content,
      timestamp: new Date(),
      data
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const updateBotMessage = (messageId: string, newContent: string) => {
    setMessages(prev => prev.map(msg => 
      msg.data?.messageId === messageId 
        ? { ...msg, content: newContent }
        : msg
    ));
  };

  const removeBotMessage = (messageId: string) => {
    setMessages(prev => prev.filter(msg => msg.data?.messageId !== messageId));
  };

  const handleAgenticPolicyDiscovery = async (query: string) => {
    try {
      setIsLoading(true);
      
      // Add a status message that will be updated during streaming
      const statusMessageId = Date.now().toString();
      addBotMessage("🔍 Starting policy search...", { type: 'status', messageId: statusMessageId });
      
      // Use streaming endpoint for real-time updates
      const response = await fetch('http://localhost:8000/policies/search/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: query,
          max_results: 8
        })
      });

      if (!response.ok) {
        throw new Error('Stream request failed');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response stream available');
      }

      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'status') {
                // Update the status message with progress
                const progressBar = '▓'.repeat(data.step) + '░'.repeat(data.total_steps - data.step);
                updateBotMessage(statusMessageId, `${data.message}\n\n[${progressBar}] ${data.step}/${data.total_steps}`);
              } else if (data.type === 'result') {
                // Remove status message and add results
                removeBotMessage(statusMessageId);
                
                if (data.success && data.priority_policies?.length > 0) {
                  addBotMessage(
                    `Found ${data.total_found} relevant policies. Here are the most important ones:`,
                    { policies: data.priority_policies }
                  );

                  // Display top policies as clean cards
                  data.priority_policies.slice(0, 4).forEach((policy: any) => {
                    const policyActions: ChatAction[] = [
                      {
                        id: `explain_${policy.id}`,
                        label: 'Explain Policy',
                        type: 'explain_policy',
                        data: policy
                      },
                      {
                        id: `select_${policy.id}`,
                        label: 'Select Policy',
                        type: 'policy_select',
                        data: policy
                      },
                      {
                        id: `analyze_${policy.id}`,
                        label: 'Analyze Impact',
                        type: 'analyze_policy',
                        data: policy
                      }
                    ];

                    addSystemMessage('', { 
                      type: 'policy_card',
                      policy,
                      actions: policyActions
                    });
                  });
                } else {
                  addBotMessage("I couldn't find policies matching your search. Try different keywords like 'housing', 'transportation', or 'business'.");
                }
              } else if (data.type === 'error') {
                removeBotMessage(statusMessageId);
                addBotMessage(`Sorry, I encountered an error: ${data.message}`);
              }
            } catch (parseError) {
              console.error('Error parsing stream data:', parseError);
            }
          }
        }
      }
      
    } catch (error) {
      addBotMessage("Sorry, I encountered an error while searching for policies. Please try again.");
      console.error('Policy discovery error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePolicySelect = (policy: DiscoveredPolicy) => {
    setSelectedPolicy(policy);
    
    const actions: ChatAction[] = [
      {
        id: 'explain_selected',
        label: 'Explain Policy',
        type: 'explain_policy',
        data: policy
      },
      {
        id: 'start_debate',
        label: 'Start Debate',
        type: 'start_debate',
        data: policy
      },
      {
        id: 'generate_email',
        label: 'Generate Email',
        type: 'generate_email',
        data: policy
      }
    ];

    addBotMessage(
      `Selected: "${policy.title}"\n\nWhat would you like to do next?`,
      { selectedPolicy: policy },
      actions
    );
  };

  const handleStartDebate = async (policy: DiscoveredPolicy) => {
    try {
      setIsLoading(true);
      setIsDebateActive(true);
      
      addBotMessage("🎭 Starting real-time stakeholder debate...");
      
      // Use the real-time debate system instead of batch API
      const session = await apiClient.startDebate({
        policy_name: policy.id || `policy_${Date.now()}`,
        system_type: 'human' // Use human system for conversational debate
      });

      setCurrentDebateSession(session.session_id);
      
      // Connect to WebSocket for real-time streaming
      const client = createDebateWebSocket(session.session_id);
      setWsClient(client);

      // Set up WebSocket event handlers
      client.onMessage('connection_established', (message: any) => {
        setIsDebateConnected(true);
        addBotMessage("🔗 Connected to real-time debate stream");
        toast({
          title: "Connected to debate",
          description: "Real-time debate connection established",
        });
      });

      client.onMessage('debate_message', (message: any) => {
        const debateMessage: DebateMessage = {
          id: message.id,
          sender: message.sender,
          content: message.content,
          timestamp: message.timestamp,
          message_type: message.type,
          metadata: message.metadata || {},
          round: message.round,
          round_type: message.round_type
        };
        
        // Add to debate messages state
        setDebateMessages(prev => [...prev, debateMessage]);
        
        // Add to chat interface as a bot message
        addBotMessage(`**${message.sender}**: ${message.content}`, {
          type: 'debate_message',
          debateMessage
        });
      });

      client.onMessage('debate_step', (message: any) => {
        addBotMessage(`🎯 ${message.message}`, { type: 'debate_step' });
      });

      client.onMessage('debate_start', (message: any) => {
        addBotMessage(`🚀 ${message.message}`, { type: 'debate_status' });
      });

      client.onMessage('round_start', (message: any) => {
        addBotMessage(`📋 **Round ${message.round}: ${message.round_type?.toUpperCase()}**`, { 
          type: 'round_start',
          round: message.round,
          roundType: message.round_type
        });
      });

      client.onMessage('round_complete', (message: any) => {
        addBotMessage(`✅ Round ${message.round} completed`, { type: 'round_complete' });
      });

      client.onMessage('debate_complete', (message: any) => {
        addBotMessage(`🎉 **Debate Complete!**\n\n${message.message}`, { type: 'debate_complete' });
        
        const actions: ChatAction[] = [
          {
            id: 'generate_email_after_debate',
            label: 'Generate Email',
            type: 'generate_email',
            data: { policy, debateMessages }
          }
        ];

        addBotMessage(
          "You can now generate your personalized email to city council based on the debate.",
          { debateResult: { success: true, debate_messages: debateMessages }, debateMessages },
          actions
        );
        
        setIsDebateActive(false);
        setIsDebateConnected(false);
      });

      client.onMessage('error', (message: any) => {
        addBotMessage(`❌ Error: ${message.message}`, { type: 'error' });
        toast({
          title: "Debate error",
          description: message.message,
          variant: "destructive",
        });
        setIsDebateActive(false);
        setIsDebateConnected(false);
      });

      // Connect to WebSocket
      await client.connect();
      
    } catch (error) {
      addBotMessage("Sorry, I encountered an error starting the real-time debate. Please try again.");
      console.error('Real-time debate error:', error);
      setIsDebateActive(false);
      setIsDebateConnected(false);
      toast({
        title: "Error starting debate",
        description: "Failed to connect to the real-time debate system",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateEmail = async (policy: DiscoveredPolicy, debateContext?: { debateMessages?: DebateMessage[] }) => {
    try {
      setIsLoading(true);
      
      addBotMessage("Generating advocacy email...");
      
      const emailRequest: EmailGenerationRequest = {
        policy_id: policy.url, // Send the URL so backend can fetch full content
        policy_title: policy.title,
        policy_content: policy.summary || policy.content_preview || '', // Fallback content
        user_perspective: 'concerned_citizen',
        debate_context: debateContext?.debateMessages || debateMessages
      };

      const response = await apiClient.generateEmail(emailRequest);
      
      if (response.success) {
        addBotMessage(
          "Your advocacy email is ready:",
          { emailContent: response.email_content, recipients: response.recipients }
        );
      }
    } catch (error) {
      addBotMessage("Sorry, I encountered an error generating the email. Please try again.");
      console.error('Email generation error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExplainPolicy = (policy: DiscoveredPolicy) => {
    const explanation = `## ${policy.title}

**What this policy is about:**
${policy.summary}

**Government Level:** ${policy.government_level}
**Policy Domain:** ${policy.domain}
**Source Agency:** ${policy.source_agency}
**Status:** ${policy.status}

${policy.content_preview ? `### Key Details\n${policy.content_preview}` : ''}

${policy.stakeholder_impacts && policy.stakeholder_impacts.length > 0 ? 
  `### Who this affects\n${policy.stakeholder_impacts.map(impact => 
    `• **${impact.group}**: ${impact.description}`
  ).join('\n')}` : ''}

*This policy explanation helps you understand what the policy does before deciding to start a debate or draft an advocacy email.*`;

    addBotMessage(explanation);
  };

  const handleActionClick = (action: ChatAction) => {
    switch (action.type) {
      case 'explain_policy':
        if (action.data && 'id' in action.data) {
          handleExplainPolicy(action.data);
        }
        break;
      case 'policy_select':
        if (action.data && 'id' in action.data) {
          handlePolicySelect(action.data);
        }
        break;
      case 'start_debate':
        if (action.data && 'id' in action.data) {
          handleStartDebate(action.data);
        }
        break;
      case 'generate_email':
        if (action.data) {
          if ('policy' in action.data) {
            handleGenerateEmail(action.data.policy, action.data);
          } else if ('id' in action.data) {
            handleGenerateEmail(action.data);
          }
        }
        break;
      case 'search_more':
        addBotMessage("What specific policy area would you like to explore?");
        break;
      case 'analyze_policy':
        if (action.data && 'title' in action.data) {
          addBotMessage(`Analyzing "${action.data.title}"...`);
        }
        break;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userInput = inputValue.trim();
    setInputValue('');
    addUserMessage(userInput);

    // If we're in an active debate, send message to the debate
    if (isDebateActive && isDebateConnected && wsClient) {
      wsClient.sendUserMessage(userInput);
      addBotMessage(`**You**: ${userInput}`, { type: 'user_debate_message' });
      return;
    }

    // Use agentic policy discovery for all queries
    await handleAgenticPolicyDiscovery(userInput);
  };

  const togglePolicyExpansion = (policyId: string) => {
    setExpandedPolicies(prev => {
      const newSet = new Set(prev);
      if (newSet.has(policyId)) {
        newSet.delete(policyId);
      } else {
        newSet.add(policyId);
      }
      return newSet;
    });
  };

  const getGovernmentColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'federal': return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'state': return 'bg-green-50 text-green-700 border-green-200';
      case 'local': return 'bg-purple-50 text-purple-700 border-purple-200';
      default: return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const getDomainIcon = (domain: string) => {
    switch (domain?.toLowerCase()) {
      case 'housing': return <Home className="w-3 h-3" />;
      case 'transportation': return <Users className="w-3 h-3" />;
      case 'business': return <Briefcase className="w-3 h-3" />;
      case 'healthcare': return <Heart className="w-3 h-3" />;
      case 'environment': return <Globe className="w-3 h-3" />;
      default: return <FileText className="w-3 h-3" />;
    }
  };

  const renderMessage = (message: ChatMessage) => {
    if (message.data?.type === 'policy_card') {
      const policy = message.data.policy;
      const isExpanded = expandedPolicies.has(policy.id);
      
      return (
        <div className="mb-4">
          <Card className="border-l-4 border-l-blue-500 hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-base font-medium text-gray-900 mb-2">
                    {policy.title}
                  </CardTitle>
                  <div className="flex flex-wrap gap-1 mb-2">
                    <Badge 
                      variant="secondary" 
                      className={`text-xs ${getGovernmentColor(policy.government_level)}`}
                    >
                      {policy.government_level}
                    </Badge>
                    <Badge variant="outline" className="text-xs flex items-center gap-1">
                      {getDomainIcon(policy.domain)}
                      {policy.domain}
                    </Badge>
                    {policy.confidence_score && (
                      <Badge variant="default" className="text-xs bg-green-50 text-green-700">
                        {Math.round(policy.confidence_score * 100)}%
                      </Badge>
                    )}
                  </div>
                </div>
                <Collapsible>
                  <CollapsibleTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => togglePolicyExpansion(policy.id)}
                    >
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </Button>
                  </CollapsibleTrigger>
                </Collapsible>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-sm text-gray-700 mb-3">{processInlineMarkdown(policy.summary)}</div>
              
              <Collapsible open={isExpanded}>
                <CollapsibleContent className="space-y-3">
                  {policy.content_preview && (
                    <div className="p-3 bg-gray-50 rounded text-sm">
                      <h4 className="font-medium mb-1">Content Preview</h4>
                      <div className="text-gray-700">{processInlineMarkdown(policy.content_preview)}</div>
                    </div>
                  )}
                  
                  {policy.stakeholder_impacts && policy.stakeholder_impacts.length > 0 && (
                    <div className="p-3 bg-blue-50 rounded">
                      <h4 className="font-medium text-sm mb-2 text-blue-800">Stakeholder Impacts</h4>
                      <div className="space-y-2">
                        {policy.stakeholder_impacts.map((impact, idx) => (
                          <div key={idx} className="flex gap-2 text-sm">
                            <Badge 
                              variant="outline" 
                              className={`text-xs ${
                                impact.severity === 'high' ? 'bg-red-50 text-red-700' :
                                impact.severity === 'medium' ? 'bg-yellow-50 text-yellow-700' :
                                'bg-green-50 text-green-700'
                              }`}
                            >
                              {impact.group}
                            </Badge>
                            <span className="text-gray-700">{processInlineMarkdown(impact.description)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CollapsibleContent>
              </Collapsible>
              
              <div className="flex gap-2 mt-3 pt-3 border-t">
                {message.data.actions?.map((action: ChatAction) => (
                  <Button
                    key={action.id}
                    variant="outline"
                    size="sm"
                    onClick={() => handleActionClick(action)}
                    className="text-xs"
                  >
                    {action.label}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    // Handle debate messages with special styling
    if (message.data?.type === 'debate_message') {
      const debateMessage = message.data.debateMessage;
      const getAgentColor = (sender: string) => {
        const colors = {
          'moderator': 'bg-purple-50 border-purple-200 text-purple-900',
          'tenants': 'bg-blue-50 border-blue-200 text-blue-900',
          'landlords': 'bg-green-50 border-green-200 text-green-900',
          'city_officials': 'bg-yellow-50 border-yellow-200 text-yellow-900',
          'business_owners': 'bg-red-50 border-red-200 text-red-900',
          'housing_advocates': 'bg-indigo-50 border-indigo-200 text-indigo-900',
          'user': 'bg-gray-50 border-gray-200 text-gray-900'
        };
        return colors[sender] || 'bg-gray-50 border-gray-200 text-gray-900';
      };

      return (
        <div className="mb-4">
          <div className={`rounded-lg p-3 border-2 ${getAgentColor(debateMessage?.sender || 'unknown')}`}>
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="outline" className="text-xs">
                {debateMessage?.sender || 'Unknown'}
              </Badge>
              {debateMessage?.round && (
                <Badge variant="secondary" className="text-xs">
                  Round {debateMessage.round}
                </Badge>
              )}
            </div>
            <div className="text-sm">
              {processMarkdown(debateMessage?.content || message.content)}
            </div>
            <div className="text-xs opacity-60 mt-2">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        </div>
      );
    }

    // Handle status messages (debate steps, round starts, etc.)
    if (message.data?.type === 'debate_step' || message.data?.type === 'debate_status' || 
        message.data?.type === 'round_start' || message.data?.type === 'round_complete') {
      return (
        <div className="mb-4">
          <div className="bg-gray-100 rounded-lg p-3 border-l-4 border-l-blue-500">
            <div className="flex items-center gap-2 mb-1">
              <MessageCircle className="w-4 h-4 text-blue-500" />
              <span className="text-sm font-medium text-blue-700">System</span>
            </div>
            <div className="text-sm text-gray-700">
              {processMarkdown(message.content)}
            </div>
            <div className="text-xs opacity-60 mt-2">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        </div>
      );
    }

    // Handle user debate messages
    if (message.data?.type === 'user_debate_message') {
      return (
        <div className="flex gap-3 mb-4 justify-end">
          <div className="flex gap-2 max-w-[85%] flex-row-reverse">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center">
              <User size={16} />
            </div>
            <div className="rounded-lg p-3 bg-blue-500 text-white">
              <div className="flex items-center gap-2 mb-1">
                <Badge variant="outline" className="text-xs bg-blue-600 text-white border-blue-400">
                  You (Debate)
                </Badge>
              </div>
              <div className="text-sm">
                {processMarkdown(message.content)}
              </div>
              <div className="text-xs opacity-80 mt-2">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className={`flex gap-3 mb-4 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
        <div className={`flex gap-2 max-w-[85%] ${message.type === 'user' ? 'flex-row-reverse' : ''}`}>
          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            message.type === 'user' 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-500 text-white'
          }`}>
            {message.type === 'user' ? <User size={16} /> : <Bot size={16} />}
          </div>
          
          <div className={`rounded-lg p-3 ${
            message.type === 'user' 
              ? 'bg-blue-500 text-white' 
              : 'bg-white border text-gray-900'
          }`}>
            <div className="text-sm">
              {processMarkdown(message.content)}
            </div>
            
            {message.data?.emailContent && (
              <div className="mt-3 p-3 bg-gray-50 rounded text-sm">
                <h4 className="font-medium mb-2 flex items-center gap-1">
                  <Mail className="w-4 h-4" />
                  Advocacy Email
                </h4>
                <div className="text-gray-700 bg-white p-2 rounded border">
                  {processMarkdown(message.data.emailContent)}
                </div>
                {message.data.recipients && (
                  <div className="mt-2 text-xs text-gray-500">
                    <span className="font-medium">Recipients: </span>
                    {message.data.recipients.join(', ')}
                  </div>
                )}
              </div>
            )}
            
            {message.data?.debateResult && (
              <div className="mt-3 p-3 bg-blue-50 rounded text-sm">
                <h4 className="font-medium mb-2 flex items-center gap-1">
                  <MessageCircle className="w-4 h-4" />
                  Debate Summary
                </h4>
                <div className="text-blue-800 mb-2 bg-white p-2 rounded">
                  {processMarkdown(message.data.debateResult.summary)}
                </div>
                {message.data.debateMessages && (
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {message.data.debateMessages.slice(0, 3).map((msg: DebateMessage, idx: number) => (
                      <div key={idx} className="text-xs p-2 bg-white rounded">
                        <div className="font-medium text-blue-700">{msg.stakeholder || msg.sender}:</div>
                        <div className="text-gray-700">{processMarkdown(msg.message || msg.content)}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {message.actions && message.actions.length > 0 && (
              <div className="flex gap-2 mt-3 pt-2 border-t">
                {message.actions.map((action) => (
                  <Button
                    key={action.id}
                    variant="secondary"
                    size="sm"
                    onClick={() => handleActionClick(action)}
                    className="text-xs"
                  >
                    {action.label}
                  </Button>
                ))}
              </div>
            )}
            
            <div className="text-xs opacity-60 mt-2">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-semibold text-gray-900">SF Policy Assistant</h1>
            </div>
            {/* Show debate status */}
            {isDebateActive && (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                  <div className={`w-2 h-2 rounded-full ${isDebateConnected ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
                  <span className="text-sm text-gray-600">
                    {isDebateConnected ? 'Live Debate' : 'Connecting...'}
                  </span>
                </div>
                {isDebateConnected && (
                  <Badge variant="outline" className="text-xs">
                    🎭 Multi-Agent Chat
                  </Badge>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        <div className="max-w-4xl mx-auto p-4 space-y-4">
          {messages.map((message) => renderMessage(message))}
          {isLoading && (
            <div className="flex items-center justify-center p-4">
              <div className="flex items-center gap-2 text-gray-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>
                  {isDebateActive ? 'Agents are discussing...' : 'Thinking...'}
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t shadow-sm">
        <div className="max-w-4xl mx-auto p-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={
                isDebateActive && isDebateConnected 
                  ? "Join the debate discussion..." 
                  : "Ask about SF policies..."
              }
              disabled={isLoading}
              className="flex-1"
            />
            <Button type="submit" disabled={isLoading || !inputValue.trim()}>
              <Send className="w-4 h-4" />
            </Button>
          </form>
          {isDebateActive && isDebateConnected && (
            <p className="text-xs text-gray-500 mt-2">
              💬 You can now participate in the live multi-agent debate
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatInterface; 