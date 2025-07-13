import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Users, MessageSquare, Play, Pause, SkipForward, RotateCcw, Loader2, AlertCircle } from 'lucide-react';
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
        onGenerateEmail();
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

    wsClient.sendUserMessage(userInput);
    setUserInput('');
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
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b bg-green-50">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold text-gray-800">Policy Debate</h2>
          <div className="flex items-center gap-2">
            <Select
              value={systemType}
              onValueChange={(value: 'debug' | 'weave' | 'human') => setSystemType(value)}
              disabled={loading || isConnected}
            >
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="debug">Debug</SelectItem>
                <SelectItem value="weave">Weave</SelectItem>
                <SelectItem value="human">Human</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <p className="text-sm text-gray-600 mb-2">
          {selectedPolicy.title}
        </p>
        
        {/* Status and Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge variant={isConnected ? "default" : "secondary"}>
              {isConnected ? "Connected" : "Disconnected"}
            </Badge>
            <span className="text-sm text-gray-600">{getStatusText()}</span>
          </div>
          
          <div className="flex items-center gap-1">
            {isConnected && debateStatus === 'paused' && (
              <Button onClick={resumeDebate} size="sm" variant="outline">
                <Play className="w-4 h-4 mr-1" />
                Resume
              </Button>
            )}
            {isConnected && debateStatus === 'running' && (
              <Button onClick={pauseDebate} size="sm" variant="outline">
                <Pause className="w-4 h-4 mr-1" />
                Pause
              </Button>
            )}
            <Button onClick={restartDebate} size="sm" variant="outline">
              <RotateCcw className="w-4 h-4 mr-1" />
              Restart
            </Button>
          </div>
        </div>
      </div>

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
                : "Type your message to join the debate..."
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
      </div>
    </div>
  );
};

export default DebatePanel;
