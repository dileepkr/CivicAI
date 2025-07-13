
import React, { useState, useRef, useEffect, useReducer } from 'react';
import { Send, Users, MessageSquare, Play, Pause, SkipForward, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';

interface Message {
  id: string;
  sender: 'renter' | 'landlord' | 'moderator' | 'user';
  content: string;
  timestamp: Date;
  clauseIndex?: number;
}

interface Clause {
  id: number;
  title: string;
  content: string;
  keyPoints: string[];
}

// Debate state machine types
enum DebateAction {
  WAITING = 'WAITING',
  RENTER_MESSAGE = 'RENTER_MESSAGE', 
  LANDLORD_MESSAGE = 'LANDLORD_MESSAGE',
  NEXT_ROUND = 'NEXT_ROUND',
  NEXT_CLAUSE = 'NEXT_CLAUSE',
  END_DEBATE = 'END_DEBATE'
}

interface DebateState {
  clauseIndex: number;
  round: number;
  step: number; // Which step in the current round (0=renter, 1=landlord, 2=next)
  nextAction: DebateAction;
  isActive: boolean;
  isPaused: boolean;
}

interface DebatePanelProps {
  selectedPolicy: any;
  onGenerateEmail: () => void;
  onMessagesChange: (messages: Message[]) => void;
}

// Debate state reducer
const debateReducer = (state: DebateState, action: any): DebateState => {
  console.log('Debate state transition:', { current: state, action });
  
  switch (action.type) {
    case 'START_DEBATE':
      return {
        clauseIndex: 0,
        round: 0,
        step: 0,
        nextAction: DebateAction.RENTER_MESSAGE,
        isActive: true,
        isPaused: false
      };
      
    case 'PAUSE':
      return { ...state, isPaused: true };
      
    case 'RESUME':
      return { ...state, isPaused: false };
      
    case 'NEXT_STEP':
      const { clauseIndex, round, step } = state;
      
      if (step === 0) { // After renter message
        return { ...state, step: 1, nextAction: DebateAction.LANDLORD_MESSAGE };
      } else if (step === 1) { // After landlord message
        if (round < 2) { // More rounds to go
          return { ...state, step: 0, round: round + 1, nextAction: DebateAction.RENTER_MESSAGE };
        } else { // End of rounds for this clause
          if (clauseIndex < 2) { // More clauses to go
            return { ...state, step: 0, round: 0, clauseIndex: clauseIndex + 1, nextAction: DebateAction.RENTER_MESSAGE };
          } else { // End of debate
            return { ...state, nextAction: DebateAction.END_DEBATE, isActive: false };
          }
        }
      }
      return state;
      
    case 'SKIP_CLAUSE':
      if (state.clauseIndex < 2) {
        return { ...state, clauseIndex: state.clauseIndex + 1, round: 0, step: 0, nextAction: DebateAction.RENTER_MESSAGE };
      } else {
        return { ...state, nextAction: DebateAction.END_DEBATE, isActive: false };
      }
      
    case 'SET_CLAUSE':
      return { ...state, clauseIndex: action.clauseIndex, round: 0, step: 0, nextAction: DebateAction.RENTER_MESSAGE };
      
    default:
      return state;
  }
};

const DebatePanel: React.FC<DebatePanelProps> = ({ selectedPolicy, onGenerateEmail, onMessagesChange }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [userInput, setUserInput] = useState('');
  const [userTyping, setUserTyping] = useState(false);
  const [shouldPauseAfterClause, setShouldPauseAfterClause] = useState(false);
  const [waitingForUserInput, setWaitingForUserInput] = useState(false);
  
  // Use reducer for debate state management
  const [debateState, dispatch] = useReducer(debateReducer, {
    clauseIndex: 0,
    round: 0,
    step: 0,
    nextAction: DebateAction.WAITING,
    isActive: false,
    isPaused: false
  });
  
  const activeTimeouts = useRef<NodeJS.Timeout[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const currentExecutionId = useRef<string>('');
  const isUserInteracting = useRef<boolean>(false);

  // Mock clauses for the selected policy
  const clauses: Clause[] = [
    {
      id: 1,
      title: "Rent Control Provisions",
      content: "Annual rent increases shall not exceed 3% or the Consumer Price Index, whichever is lower.",
      keyPoints: ["3% annual cap", "CPI adjustment", "Tenant protection"]
    },
    {
      id: 2,
      title: "Just Cause Eviction Requirements",
      content: "Landlords must provide just cause for eviction and 90-day notice for no-fault evictions.",
      keyPoints: ["Just cause requirement", "90-day notice", "No-fault protections"]
    },
    {
      id: 3,
      title: "Tenant Rights and Remedies",
      content: "Tenants have the right to organize, request repairs, and challenge unlawful rent increases.",
      keyPoints: ["Organization rights", "Repair requests", "Legal remedies"]
    }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
    onMessagesChange(messages);
  }, [messages, onMessagesChange]);

  useEffect(() => {
    if (selectedPolicy && !debateState.isActive) {
      startDebate();
    }
  }, [selectedPolicy]);

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      clearAllTimeouts();
    };
  }, []);

  const clearAllTimeouts = () => {
    activeTimeouts.current.forEach(timeout => clearTimeout(timeout));
    activeTimeouts.current = [];
  };

  const addTimeout = (callback: () => void, delay: number, executionId?: string) => {
    const timeout = setTimeout(() => {
      // Only execute if this is still the current execution and user is not interacting
      if ((!executionId || executionId === currentExecutionId.current) && !isUserInteracting.current) {
        callback();
      }
    }, delay);
    activeTimeouts.current.push(timeout);
    return timeout;
  };

  // Generate unique execution ID for each debate sequence
  const generateExecutionId = () => {
    currentExecutionId.current = `exec_${Date.now()}_${Math.random()}`;
    return currentExecutionId.current;
  };

  const startDebate = () => {
    clearAllTimeouts();
    
    // Reset all interaction states
    isUserInteracting.current = false;
    setWaitingForUserInput(false);
    setUserTyping(false);
    setShouldPauseAfterClause(false);
    
    const executionId = generateExecutionId();
    
    setMessages([]);
    dispatch({ type: 'START_DEBATE' });
    
    const initialMessage: Message = {
      id: '1',
      sender: 'moderator',
      content: `Welcome to the policy debate for "${selectedPolicy.title}". We'll discuss this clause by clause. You can pause at any time to join the conversation. Let's start with the first clause.`,
      timestamp: new Date()
    };

    setMessages([initialMessage]);
    
    // Start the first clause debate after a short delay
    addTimeout(() => {
      startClauseDebate(0, executionId);
    }, 2000, executionId);
  };

  const startClauseDebate = (clauseIndex: number, executionId: string) => {
    console.log(`Starting clause debate for index ${clauseIndex}`);
    
    if (clauseIndex >= clauses.length) {
      // End of debate
      const endMessage: Message = {
        id: `end-${Date.now()}`,
        sender: 'moderator',
        content: "We've discussed all clauses of this policy. Thank you for this comprehensive debate. You can now generate an email to the SF City Council based on our discussion.",
        timestamp: new Date(),
        clauseIndex
      };
      setMessages(prev => [...prev, endMessage]);
      return;
    }

    const clause = clauses[clauseIndex];
    const moderatorIntro: Message = {
      id: `mod-intro-${clauseIndex}`,
      sender: 'moderator',
      content: `Now let's discuss ${clause.title}: "${clause.content}"`,
      timestamp: new Date(),
      clauseIndex
    };

    setMessages(prev => [...prev, moderatorIntro]);

    // Start the debate exchanges for this clause
    addTimeout(() => {
      // Ensure we start with the first renter message for this clause
      console.log('Starting debate exchanges for clause', clauseIndex, 'with current state:', debateState);
      executeNextDebateStep(executionId);
    }, 1500, executionId);
  };

  // New robust debate execution engine
  const executeNextDebateStep = (executionId: string) => {
    if (debateState.isPaused || !debateState.isActive) {
      console.log('Debate execution halted - paused or inactive', debateState);
      return;
    }
    
    // Additional check: don't continue if user is actively typing
    if (isUserInteracting.current) {
      console.log('Debate execution halted - user is interacting');
      return;
    }

    const { clauseIndex, round, step, nextAction } = debateState;
    const clause = clauses[clauseIndex];
    
    console.log(`Executing debate step: ${nextAction}, clause: ${clauseIndex}, round: ${round}, step: ${step}`);
    
    // Handle case where nextAction might be WAITING - force to start with renter message
    if (nextAction === DebateAction.WAITING && debateState.isActive) {
      console.log('Forcing transition to RENTER_MESSAGE from WAITING state');
      dispatch({ type: 'START_DEBATE' }); // This will set nextAction to RENTER_MESSAGE
      // Re-schedule execution to allow state update
      addTimeout(() => executeNextDebateStep(executionId), 100, executionId);
      return;
    }
    
    const exchanges = [
      {
        renter: `This clause is essential for tenant protection. ${clause.keyPoints[0]} ensures affordability remains within reach for working families.`,
        landlord: `While I understand the intent, ${clause.keyPoints[0]} could limit our ability to maintain properties and adapt to market conditions.`
      },
      {
        renter: `${clause.keyPoints[1]} provides necessary stability and prevents sudden displacement of long-term residents.`,
        landlord: `However, ${clause.keyPoints[1]} may discourage investment in housing improvements and new construction.`
      },
      {
        renter: `${clause.keyPoints[2]} empowers tenants to advocate for their rights and ensures fair treatment in the rental market.`,
        landlord: `We need to balance ${clause.keyPoints[2]} with practical considerations for property management and operational costs.`
      }
    ];

    switch (nextAction) {
      case DebateAction.RENTER_MESSAGE:
        if (round < exchanges.length) {
          const renterMessage: Message = {
            id: `renter-${clauseIndex}-${round}-${step}`,
            sender: 'renter',
            content: exchanges[round].renter,
            timestamp: new Date(),
            clauseIndex
          };
          setMessages(prev => [...prev, renterMessage]);
          
          dispatch({ type: 'NEXT_STEP' });
          addTimeout(() => executeNextDebateStep(executionId), 3000, executionId);
        }
        break;
        
      case DebateAction.LANDLORD_MESSAGE:
        if (round < exchanges.length) {
          const landlordMessage: Message = {
            id: `landlord-${clauseIndex}-${round}-${step}`,
            sender: 'landlord',
            content: exchanges[round].landlord,
            timestamp: new Date(),
            clauseIndex
          };
          setMessages(prev => [...prev, landlordMessage]);
          
          dispatch({ type: 'NEXT_STEP' });
          
          // Check if user wants to pause after this clause
          if (shouldPauseAfterClause && round >= exchanges.length - 1) {
            dispatch({ type: 'PAUSE' });
            setShouldPauseAfterClause(false);
            
            const pauseMessage: Message = {
              id: `pause-${Date.now()}`,
              sender: 'moderator',
              content: `Discussion paused at the end of ${clause.title}. Feel free to share your thoughts or continue to the next clause.`,
              timestamp: new Date(),
              clauseIndex
            };
            setMessages(prev => [...prev, pauseMessage]);
          } else {
            addTimeout(() => executeNextDebateStep(executionId), 2000, executionId);
          }
        }
        break;
        
      case DebateAction.END_DEBATE:
        const endMessage: Message = {
          id: `end-${Date.now()}`,
          sender: 'moderator',
          content: "We've discussed all clauses of this policy. Thank you for this comprehensive debate. You can now generate an email to the SF City Council based on our discussion.",
          timestamp: new Date(),
          clauseIndex
        };
        setMessages(prev => [...prev, endMessage]);
        break;
        
      default:
        // If we reach a clause transition, start the next clause
        if (debateState.nextAction === DebateAction.RENTER_MESSAGE && clauseIndex < clauses.length) {
          addTimeout(() => startClauseDebate(clauseIndex, executionId), 2000, executionId);
        }
    }
  };

  const pauseDebate = () => {
    console.log('Pausing debate at state:', debateState);
    clearAllTimeouts();
    dispatch({ type: 'PAUSE' });
  };

  const resumeDebate = () => {
    console.log('Resuming debate from state:', debateState);
    clearAllTimeouts();
    
    // Clear user interaction state
    isUserInteracting.current = false;
    setWaitingForUserInput(false);
    setUserTyping(false);
    setShouldPauseAfterClause(false);
    
    const executionId = generateExecutionId();
    dispatch({ type: 'RESUME' });
    
    // Resume execution with the current debate state
    addTimeout(() => {
      executeNextDebateStep(executionId);
    }, 500, executionId);
  };

  const skipToNextClause = () => {
    if (debateState.clauseIndex < clauses.length - 1) {
      clearAllTimeouts();
      const executionId = generateExecutionId();
      
      // Add a message indicating the clause was skipped
      const skipMessage: Message = {
        id: `skip-${Date.now()}`,
        sender: 'moderator',
        content: `Clause ${debateState.clauseIndex + 1} "${clauses[debateState.clauseIndex]?.title}" has been skipped. Moving to the next clause.`,
        timestamp: new Date(),
        clauseIndex: debateState.clauseIndex
      };
      setMessages(prev => [...prev, skipMessage]);
      
      dispatch({ type: 'SKIP_CLAUSE' });
      setShouldPauseAfterClause(false);
      
      // Start the next clause immediately
      addTimeout(() => {
        startClauseDebate(debateState.clauseIndex + 1, executionId);
      }, 1000, executionId);
    }
  };

  const restartDebate = () => {
    clearAllTimeouts();
    setMessages([]);
    setShouldPauseAfterClause(false);
    setUserTyping(false);
    setWaitingForUserInput(false);
    isUserInteracting.current = false;
    startDebate();
  };

  const handleInputChange = (value: string) => {
    setUserInput(value);
    
    // Immediately pause and clear timeouts when user starts typing
    if (value.length > 0 && !userTyping && !debateState.isPaused) {
      setUserTyping(true);
      isUserInteracting.current = true;
      clearAllTimeouts();
      dispatch({ type: 'PAUSE' });
      setShouldPauseAfterClause(true);
    } else if (value.length === 0 && userTyping) {
      setUserTyping(false);
      // Don't immediately clear isUserInteracting - let resume button handle it
      setShouldPauseAfterClause(false);
    }
  };

  const handleUserMessage = () => {
    if (!userInput.trim()) return;

    // Clear all timeouts when user sends message
    clearAllTimeouts();
    isUserInteracting.current = true;
    setWaitingForUserInput(true);

    const newMessage: Message = {
      id: Date.now().toString(),
      sender: 'user',
      content: userInput,
      timestamp: new Date(),
      clauseIndex: debateState.clauseIndex
    };

    setMessages(prev => [...prev, newMessage]);
    const userMessageContent = userInput;
    setUserInput('');
    setUserTyping(false);

    // Keep the debate paused for user interaction
    dispatch({ type: 'PAUSE' });

    // Generate contextual AI responses that incorporate user's input
    addTimeout(() => {
      const currentClause = clauses[debateState.clauseIndex];
      
      // More sophisticated response generation based on user input content
      const userInputLower = userMessageContent.toLowerCase();
      let responses = [];

      if (userInputLower.includes('agree') || userInputLower.includes('support')) {
        responses = [
          {
            sender: 'moderator' as const,
            content: `Your support for ${currentClause?.title} adds weight to this discussion. What specific aspects do you find most compelling?`
          },
          {
            sender: 'renter' as const,
            content: `I'm glad you see the value in ${currentClause?.title}. Your perspective reinforces why this protection is crucial for tenants.`
          },
          {
            sender: 'landlord' as const,
            content: `While I understand your support for ${currentClause?.title}, we should also consider the practical implementation challenges.`
          }
        ];
      } else if (userInputLower.includes('concern') || userInputLower.includes('worry') || userInputLower.includes('problem')) {
        responses = [
          {
            sender: 'moderator' as const,
            content: `Your concerns about ${currentClause?.title} are valid. How might we address these issues while maintaining the clause's intent?`
          },
          {
            sender: 'renter' as const,
            content: `I understand your concerns, but ${currentClause?.title} provides essential protections. Perhaps we can find ways to address your specific worries.`
          },
          {
            sender: 'landlord' as const,
            content: `You've raised important concerns about ${currentClause?.title} that reflect real-world implementation challenges we face.`
          }
        ];
      } else {
        responses = [
          {
            sender: 'moderator' as const,
            content: `Thank you for that insight on ${currentClause?.title}. Your perspective adds valuable context to our discussion.`
          },
          {
            sender: 'renter' as const,
            content: `Your viewpoint on ${currentClause?.title} highlights important aspects we should consider in this debate.`
          },
          {
            sender: 'landlord' as const,
            content: `I appreciate your input on ${currentClause?.title}. It's important we hear from all stakeholders in this discussion.`
          }
        ];
      }

      const selectedResponse = responses[Math.floor(Math.random() * responses.length)];
      const responseMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: selectedResponse.sender,
        content: selectedResponse.content,
        timestamp: new Date(),
        clauseIndex: debateState.clauseIndex
      };

      setMessages(prev => [...prev, responseMessage]);

      // Add a follow-up question or continuation prompt
      addTimeout(() => {
        const followUpMessage: Message = {
          id: (Date.now() + 2).toString(),
          sender: 'moderator',
          content: `Would you like to continue the debate on this clause, or shall we move to the next section? Feel free to share more thoughts or click resume to continue the automated discussion.`,
          timestamp: new Date(),
          clauseIndex: debateState.clauseIndex
        };
        setMessages(prev => [...prev, followUpMessage]);
        // Mark that we're waiting for user input after AI response
        setWaitingForUserInput(true);
        isUserInteracting.current = false; // Allow resume button to work
      }, 2000);
    }, 1500);
  };

  const getAgentColor = (sender: string) => {
    switch (sender) {
      case 'renter': return 'bg-blue-100 border-l-4 border-l-blue-500';
      case 'landlord': return 'bg-orange-100 border-l-4 border-l-orange-500';
      case 'moderator': return 'bg-green-100 border-l-4 border-l-green-500';
      case 'user': return 'bg-purple-100 border-l-4 border-l-purple-500';
      default: return 'bg-gray-100';
    }
  };

  const getAgentName = (sender: string) => {
    switch (sender) {
      case 'renter': return 'Renter Agent';
      case 'landlord': return 'Landlord Agent';
      case 'moderator': return 'Moderator';
      case 'user': return 'You';
      default: return sender;
    }
  };

  const getAvatarInitials = (sender: string) => {
    switch (sender) {
      case 'renter': return 'RA';
      case 'landlord': return 'LA';
      case 'moderator': return 'M';
      case 'user': return 'U';
      default: return sender[0].toUpperCase();
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b bg-green-50">
        <h2 className="text-xl font-bold text-gray-800 mb-1">Policy Debate</h2>
            {selectedPolicy ? (
              <div className="space-y-2">
                <p className="text-sm text-gray-600">Discussing: {selectedPolicy.title}</p>
                {debateState.isActive && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">
                        Clause {debateState.clauseIndex + 1} of {clauses.length}
                      </Badge>
                      {debateState.clauseIndex < clauses.length && (
                        <span className="text-xs text-gray-500">
                          {clauses[debateState.clauseIndex]?.title}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      {waitingForUserInput && (
                        <Badge variant="secondary" className="mr-2 text-xs">
                          Waiting for input
                        </Badge>
                      )}
                      {!debateState.isPaused ? (
                        <Button size="sm" variant="outline" onClick={pauseDebate}>
                          <Pause className="w-3 h-3" />
                        </Button>
                      ) : (
                        <Button 
                          size="sm" 
                          variant="outline" 
                          onClick={resumeDebate}
                          disabled={waitingForUserInput}
                        >
                          <Play className="w-3 h-3" />
                        </Button>
                      )}
                      <Button size="sm" variant="outline" onClick={skipToNextClause} title="Skip current clause discussion">
                    <SkipForward className="w-3 h-3" />
                  </Button>
                  <Button size="sm" variant="outline" onClick={restartDebate}>
                    <RotateCcw className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-500">Select a policy to start the debate</p>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {!selectedPolicy ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <MessageSquare className="w-12 h-12 mb-4" />
            <p className="text-center">Select a policy from the left panel to begin the AI-powered debate</p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div key={message.id} className={`p-4 rounded-lg ${getAgentColor(message.sender)}`}>
                <div className="flex items-start gap-3">
                  <Avatar className="w-8 h-8">
                    <AvatarFallback className="text-xs font-semibold">
                      {getAvatarInitials(message.sender)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-sm">{getAgentName(message.sender)}</span>
                      {message.clauseIndex !== undefined && (
                        <Badge variant="secondary" className="text-xs">
                          Clause {message.clauseIndex + 1}
                        </Badge>
                      )}
                      <span className="text-xs text-gray-500">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700">{message.content}</p>
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      {selectedPolicy && (
        <div className="p-4 border-t bg-white space-y-3">
          <div className="flex gap-2">
            <Input
              placeholder={debateState.isPaused ? "Join the discussion..." : shouldPauseAfterClause ? "Will pause at end of current clause..." : "Type to pause at end of current clause..."}
              value={userInput}
              onChange={(e) => handleInputChange(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleUserMessage()}
              className="flex-1"
            />
            <Button onClick={handleUserMessage} size="sm">
              <Send className="w-4 h-4" />
            </Button>
          </div>
          
          {debateState.clauseIndex < clauses.length && (
            <div className="bg-blue-50 p-3 rounded-lg">
              <h4 className="font-medium text-sm text-blue-900 mb-1">
                Current Clause: {clauses[debateState.clauseIndex]?.title}
              </h4>
              <p className="text-xs text-blue-700 mb-2">
                {clauses[debateState.clauseIndex]?.content}
              </p>
              <div className="flex flex-wrap gap-1">
                {clauses[debateState.clauseIndex]?.keyPoints.map((point, index) => (
                  <Badge key={index} variant="secondary" className="text-xs">
                    {point}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          
          {messages.length > 5 && (
            <Button 
              onClick={onGenerateEmail} 
              className="w-full bg-blue-600 hover:bg-blue-700"
            >
              Generate Email to SF City Council
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

export default DebatePanel;
