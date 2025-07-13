import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Users, MessageSquare, Play, Pause, SkipForward, RotateCcw, Loader2, AlertCircle, StopCircle, CheckCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { apiClient, createDebateWebSocket, DebateWebSocketClient, DebateMessage, formatTimestamp, getSenderColor } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface DebatePanelProps {
  selectedPolicy: any;
  onGenerateEmail: () => void;
  onMessagesChange: (messages: DebateMessage[]) => void;
}

const DebatePanel: React.FC<DebatePanelProps> = ({ selectedPolicy, onGenerateEmail, onMessagesChange }) => {
  const [messages, setMessages] = useState<DebateMessage[]>([]);
  const [userInput, setUserInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [debateStatus, setDebateStatus] = useState<string>('idle');
  const [systemType, setSystemType] = useState<'debug' | 'weave' | 'human'>('debug');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [wsClient, setWsClient] = useState<DebateWebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  // Add state for early ending functionality
  const [showEndConfirmation, setShowEndConfirmation] = useState(false);
  const [endReason, setEndReason] = useState('');
  const [canEndDebate, setCanEndDebate] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
    onMessagesChange(messages);
  }, [messages, onMessagesChange]);

  // Start debate when policy is selected
  useEffect(() => {
    if (selectedPolicy && !sessionId) {
      startDebate();
    }
  }, [selectedPolicy]);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsClient) {
        wsClient.disconnect();
      }
    };
  }, [wsClient]);

  const startDebate = async () => {
    if (!selectedPolicy) return;

    setLoading(true);
    setError(null);
    setMessages([]);

    try {
      // Start debate session
      const session = await apiClient.startDebate({
        policy_name: selectedPolicy.id,
        system_type: systemType
      });

      setSessionId(session.session_id);
      setDebateStatus(session.status);

      // Connect WebSocket
      const client = createDebateWebSocket(session.session_id);
      setWsClient(client);

      // Set up WebSocket event handlers
      client.onMessage('connection_established', (message) => {
        setIsConnected(true);
        setCanEndDebate(true);
        toast({
          title: "Connected to debate",
          description: "Real-time debate connection established",
        });
      });

      client.onMessage('debate_message', (message) => {
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
        setMessages(prev => [...prev, debateMessage]);
      });

      client.onMessage('debate_step', (message) => {
        const stepMessage: DebateMessage = {
          id: `step_${Date.now()}`,
          sender: 'moderator',
          content: message.message,
          timestamp: new Date().toISOString(),
          message_type: 'status'
        };
        setMessages(prev => [...prev, stepMessage]);
      });

      client.onMessage('round_start', (message) => {
        const roundMessage: DebateMessage = {
          id: `round_${message.round}`,
          sender: 'moderator',
          content: `🎯 **Round ${message.round}: ${message.round_type.toUpperCase()}**\n\n${message.message}`,
          timestamp: new Date().toISOString(),
          message_type: 'status',
          round: message.round,
          round_type: message.round_type
        };
        setMessages(prev => [...prev, roundMessage]);
      });

      client.onMessage('round_complete', (message) => {
        const completeMessage: DebateMessage = {
          id: `complete_${message.round}`,
          sender: 'moderator',
          content: `✅ ${message.message}`,
          timestamp: new Date().toISOString(),
          message_type: 'status'
        };
        setMessages(prev => [...prev, completeMessage]);
      });

      client.onMessage('debate_complete', (message) => {
        const endMessage: DebateMessage = {
          id: `end_${Date.now()}`,
          sender: 'moderator',
          content: `🎉 **Debate Complete!**\n\n${message.message}\n\nYou can now generate your personalized email to city council.`,
          timestamp: new Date().toISOString(),
          message_type: 'status'
        };
        setMessages(prev => [...prev, endMessage]);
        setDebateStatus('completed');
        setCanEndDebate(false);
        onGenerateEmail();
      });

      client.onMessage('debate_terminated_complete', (message) => {
        const terminatedMessage: DebateMessage = {
          id: `terminated_${Date.now()}`,
          sender: 'moderator',
          content: `🛑 **Debate Ended Early**\n\n${message.message}\n\nYou can still generate your personalized email based on the discussion so far.`,
          timestamp: new Date().toISOString(),
          message_type: 'status'
        };
        setMessages(prev => [...prev, terminatedMessage]);
        setDebateStatus('terminated_early');
        setCanEndDebate(false);
        onGenerateEmail();
      });

      client.onMessage('end_debate_confirmation', (message) => {
        setShowEndConfirmation(true);
        toast({
          title: "Confirm debate ending",
          description: "Are you sure you want to end the debate early?",
        });
      });

      client.onMessage('debate_terminating', (message) => {
        setShowEndConfirmation(false);
        setCanEndDebate(false);
        const terminatingMessage: DebateMessage = {
          id: `terminating_${Date.now()}`,
          sender: 'moderator',
          content: `🛑 ${message.message}`,
          timestamp: new Date().toISOString(),
          message_type: 'status'
        };
        setMessages(prev => [...prev, terminatingMessage]);
        toast({
          title: "Debate ending",
          description: message.message,
        });
      });

      client.onMessage('end_debate_cancelled', (message) => {
        setShowEndConfirmation(false);
        toast({
          title: "Debate continues",
          description: message.message,
        });
      });

      client.onMessage('user_input_received', (message) => {
        const userMessage: DebateMessage = {
          id: `user_input_${Date.now()}`,
          sender: 'user',
          content: userInput,
          timestamp: new Date().toISOString(),
          message_type: 'user_input'
        };
        setMessages(prev => [...prev, userMessage]);
        
        const responseMessage: DebateMessage = {
          id: `response_${Date.now()}`,
          sender: 'moderator',
          content: `👤 ${message.message}`,
          timestamp: new Date().toISOString(),
          message_type: 'status'
        };
        setMessages(prev => [...prev, responseMessage]);
      });

      client.onMessage('error', (message) => {
        setError(message.message);
        toast({
          title: "Debate error",
          description: message.message,
          variant: "destructive",
        });
      });

      client.onMessage('debate_paused', (message) => {
        setDebateStatus('paused');
        toast({
          title: "Debate paused",
          description: message.message,
        });
      });

      client.onMessage('debate_resumed', (message) => {
        setDebateStatus('running');
        toast({
          title: "Debate resumed",
          description: message.message,
        });
      });

      // Connect to WebSocket
      await client.connect();

    } catch (err) {
      console.error('Error starting debate:', err);
      setError('Failed to start debate. Please ensure the backend is running.');
      toast({
        title: "Error starting debate",
        description: "Failed to connect to the debate backend",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUserMessage = () => {
    if (!userInput.trim() || !wsClient || !isConnected) return;

    // Send as user_input for pivot functionality
    wsClient.sendMessage({
      type: 'user_input',
      message: userInput,
      timestamp: new Date().toISOString()
    });
    
    setUserInput('');
  };

  const handleEndDebate = () => {
    if (!wsClient || !isConnected) return;
    
    wsClient.sendMessage({
      type: 'end_debate',
      confirmation: false,
      timestamp: new Date().toISOString()
    });
  };

  const handleEndDebateConfirm = () => {
    if (!wsClient || !isConnected) return;
    
    wsClient.sendMessage({
      type: 'end_debate_confirm',
      reason: endReason || 'User requested early termination',
      timestamp: new Date().toISOString()
    });
    
    setShowEndConfirmation(false);
    setEndReason('');
  };

  const handleEndDebateCancel = () => {
    if (!wsClient || !isConnected) return;
    
    wsClient.sendMessage({
      type: 'end_debate_cancel',
      timestamp: new Date().toISOString()
    });
    
    setShowEndConfirmation(false);
    setEndReason('');
  };

  const pauseDebate = () => {
    if (wsClient && isConnected) {
      wsClient.pauseDebate();
    }
  };

  const resumeDebate = () => {
    if (wsClient && isConnected) {
      wsClient.resumeDebate();
    }
  };

  const restartDebate = () => {
    if (wsClient) {
      wsClient.disconnect();
    }
    setSessionId(null);
    setMessages([]);
    setDebateStatus('idle');
    setIsConnected(false);
    setCanEndDebate(false);
    setShowEndConfirmation(false);
    startDebate();
  };

  const getStatusText = () => {
    if (loading) return 'Starting debate...';
    if (error) return `Error: ${error}`;
    if (!isConnected) return 'Connecting...';
    
    switch (debateStatus) {
      case 'idle': return 'Ready to start';
      case 'initialized': return 'Debate initialized';
      case 'running': return 'Debate in progress';
      case 'paused': return 'Debate paused';
      case 'completed': return 'Debate completed';
      case 'terminated_early': return 'Debate ended early';
      default: return debateStatus;
    }
  };

  const getAgentName = (sender: string) => {
    switch (sender) {
      case 'user': return 'You';
      case 'moderator': return 'Moderator';
      default: return sender;
    }
  };

  const getAvatarInitials = (sender: string) => {
    switch (sender) {
      case 'user': return 'U';
      case 'moderator': return 'M';
      default: return sender.charAt(0).toUpperCase();
    }
  };

  if (!selectedPolicy) {
    return (
      <div className="h-full flex flex-col">
        <div className="p-4 border-b bg-green-50">
          <h2 className="text-xl font-bold text-gray-800 mb-1">Policy Debate</h2>
          <p className="text-sm text-gray-600">Select a policy to start the debate</p>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <MessageSquare className="w-12 h-12 mx-auto mb-4" />
            <p>No policy selected</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Policy Debate
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant={isConnected ? "default" : "secondary"}>
              {getStatusText()}
            </Badge>
            {canEndDebate && (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleEndDebate}
                disabled={!isConnected}
              >
                <StopCircle className="w-4 h-4 mr-1" />
                End Debate
              </Button>
            )}
          </div>
        </div>
        
        {selectedPolicy && (
          <div className="text-sm text-gray-600">
            Discussing: <span className="font-medium">{selectedPolicy.title}</span>
          </div>
        )}
      </CardHeader>

      {/* Early End Confirmation Dialog */}
      {showEndConfirmation && (
        <div className="p-4 border-b bg-yellow-50">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <div className="space-y-3">
                <p className="font-medium">Are you sure you want to end the debate early?</p>
                <p className="text-sm">This will generate a summary of the discussion so far.</p>
                <div className="space-y-2">
                  <Input
                    placeholder="Optional: Reason for ending early"
                    value={endReason}
                    onChange={(e) => setEndReason(e.target.value)}
                    className="w-full"
                  />
                  <div className="flex gap-2">
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={handleEndDebateConfirm}
                    >
                      <CheckCircle className="w-4 h-4 mr-1" />
                      Yes, End Debate
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleEndDebateCancel}
                    >
                      <X className="w-4 h-4 mr-1" />
                      Cancel
                    </Button>
                  </div>
                </div>
              </div>
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <span className="ml-2 text-gray-600">Starting debate...</span>
          </div>
        )}
        
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex items-start gap-3 ${
              message.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {message.sender !== 'user' && (
              <Avatar className="w-8 h-8 mt-1">
                <AvatarFallback className={getSenderColor(message.sender)}>
                  {getAvatarInitials(message.sender)}
                </AvatarFallback>
              </Avatar>
            )}
            
            <div className={`max-w-xs sm:max-w-md ${message.sender === 'user' ? 'order-first' : ''}`}>
              <div className="flex items-baseline gap-2 mb-1">
                <span className="text-sm font-medium text-gray-900">
                  {getAgentName(message.sender)}
                </span>
                <span className="text-xs text-gray-500">
                  {formatTimestamp(message.timestamp)}
                </span>
                {message.round && (
                  <Badge variant="outline" className="text-xs px-1">
                    R{message.round}
                  </Badge>
                )}
                {message.message_type === 'user_input' && (
                  <Badge variant="outline" className="text-xs px-1 bg-blue-50">
                    Input
                  </Badge>
                )}
              </div>
              
              <div className={`rounded-lg p-3 ${
                message.sender === 'user' 
                  ? 'bg-blue-500 text-white' 
                  : message.message_type === 'status'
                  ? 'bg-gray-100 text-gray-800'
                  : 'bg-gray-50 text-gray-900'
              }`}>
                <div className="text-sm whitespace-pre-wrap">
                  {message.content}
                </div>
              </div>
            </div>
            
            {message.sender === 'user' && (
              <Avatar className="w-8 h-8 mt-1">
                <AvatarFallback className="bg-blue-100 text-blue-800">
                  {getAvatarInitials(message.sender)}
                </AvatarFallback>
              </Avatar>
            )}
          </div>
        ))}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t bg-white">
        <div className="flex items-center gap-2">
          <Input
            placeholder={
              !isConnected 
                ? "Connecting to debate..." 
                : "Type your message to influence the debate direction..."
            }
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleUserMessage();
              }
            }}
            disabled={!isConnected}
            className="flex-1"
          />
          <Button 
            onClick={handleUserMessage} 
            disabled={!userInput.trim() || !isConnected}
            size="sm"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
        
        {!isConnected && (
          <p className="text-xs text-gray-500 mt-2">
            Connect to the debate to participate in the discussion
          </p>
        )}
        {isConnected && (
          <p className="text-xs text-gray-500 mt-2">
            💬 Your input can change the debate direction and focus
          </p>
        )}
      </div>
    </div>
  );
};

export default DebatePanel;
