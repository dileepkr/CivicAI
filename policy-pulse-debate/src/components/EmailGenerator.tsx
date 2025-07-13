
import React, { useState } from 'react';
import { Copy, Send, FileText, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';

interface EmailGeneratorProps {
  selectedPolicy: any;
  debateMessages: any[];
}

const EmailGenerator: React.FC<EmailGeneratorProps> = ({ selectedPolicy, debateMessages }) => {
  const [senderEmail, setSenderEmail] = useState('');
  const [receiverEmail, setReceiverEmail] = useState('board.of.supervisors@sfgov.org');
  const [subject, setSubject] = useState('');
  const [emailContent, setEmailContent] = useState('');
  const [isCopied, setIsCopied] = useState(false);
  const { toast } = useToast();

  const generateEmailContent = () => {
    if (!selectedPolicy) return;

    const generatedSubject = `Public Comment on ${selectedPolicy?.title}`;
    
    // Extract user input and debate messages
    const userMessages = debateMessages
      .filter(msg => msg.sender === 'user')
      .map(msg => msg.content);
    
    // Group messages by stakeholder
    const stakeholderGroups = debateMessages.reduce((groups, msg) => {
      if (msg.sender && msg.sender !== 'user' && msg.sender !== 'moderator') {
        if (!groups[msg.sender]) {
          groups[msg.sender] = [];
        }
        groups[msg.sender].push(msg.content);
      }
      return groups;
    }, {});

    const moderatorSummary = debateMessages
      .filter(msg => msg.sender === 'moderator')
      .slice(-3) // Get last few moderator comments for context
      .map(msg => msg.content)
      .join(' ');

    // Get unique debate rounds
    const discussedRounds = debateMessages
      .filter(msg => msg.round !== undefined)
      .map(msg => msg.round)
      .filter((value, index, self) => self.indexOf(value) === index)
      .sort((a, b) => a - b);

    // Generate stakeholder sections
    const stakeholderSections = Object.entries(stakeholderGroups).map(([stakeholder, messages]) => {
      const stakeholderContent = (messages as string[]).join(' ');
      return `${stakeholder.toUpperCase()} PERSPECTIVE:
${stakeholderContent.substring(0, 400)}${stakeholderContent.length > 400 ? '...' : ''}

`;
    }).join('');

    const content = `Dear Members of the San Francisco City Council,

I am writing as a San Francisco resident to provide input on the recently proposed "${selectedPolicy?.title}" policy scheduled for consideration on ${selectedPolicy?.date}.

POLICY DETAILS:
${selectedPolicy?.summary}

${discussedRounds.length > 0 ? `DEBATE ROUNDS PARTICIPATED:
The following debate rounds were part of our structured discussion:
${discussedRounds.map(round => `• Round ${round}: Comprehensive analysis of key policy provisions`).join('\n')}

` : ''}USER INPUT & POSITION:
${userMessages.length > 0 ? `Based on my participation in the public policy discussion, I want to share my specific concerns and position:

${userMessages.map((msg, index) => `${index + 1}. ${msg}`).join('\n\n')}

` : 'After carefully reviewing this policy and participating in the public discussion, '}${stakeholderSections}${moderatorSummary ? `BALANCED ANALYSIS:
${moderatorSummary.substring(0, 300)}${moderatorSummary.length > 300 ? '...' : ''}

` : ''}SPECIFIC REQUEST:
${userMessages.length > 0 ? 
  'Based on my input above, I request that the City Council:' : 
  'After reviewing this policy, I request that the City Council:'}

1. Consider the specific concerns I have raised in the discussion
2. Ensure adequate transition periods for policy implementation
3. Include clear guidelines and enforcement mechanisms
4. Establish a stakeholder advisory committee for ongoing policy refinement
5. Provide comprehensive resources and education for all affected parties

${userMessages.length > 0 ? 
  'My participation in this discussion represents my commitment as a San Francisco resident to engage constructively in our democratic process. ' : 
  ''}I urge the Council to carefully weigh all public input when finalizing this important legislation.

Thank you for your consideration of public input in this important matter.

Sincerely,
[Your Name]
[Your Address]
[Your Contact Information]

---
Generated via SF Policy Discussion Platform`;

    setSubject(generatedSubject);
    setEmailContent(content);
    
    toast({
      title: "Email generated!",
      description: "Email content has been generated based on the debate discussion.",
    });
  };

  const copyToClipboard = async () => {
    const fullEmail = `Subject: ${subject}
From: ${senderEmail}
To: ${receiverEmail}

${emailContent}`;
    
    try {
      await navigator.clipboard.writeText(fullEmail);
      setIsCopied(true);
      toast({
        title: "Email copied!",
        description: "The complete email has been copied to your clipboard.",
      });
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      toast({
        title: "Copy failed",
        description: "Unable to copy email to clipboard.",
        variant: "destructive",
      });
    }
  };

  const sendEmail = () => {
    const encodedSubject = encodeURIComponent(subject);
    const encodedBody = encodeURIComponent(emailContent);
    const mailtoLink = `mailto:${receiverEmail}?subject=${encodedSubject}&body=${encodedBody}`;
    window.open(mailtoLink);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b bg-orange-50">
        <h2 className="text-xl font-bold text-gray-800 mb-1">Generated Email</h2>
        <p className="text-sm text-gray-600">Ready to send to SF City Council</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {!selectedPolicy ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <FileText className="w-12 h-12 mb-4" />
            <p className="text-center">Complete the policy debate to generate an email</p>
          </div>
        ) : (
          <Card className="h-full">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Email Draft
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="sender-email">From</Label>
                  <Input
                    id="sender-email"
                    type="email"
                    placeholder="your.email@example.com"
                    value={senderEmail}
                    onChange={(e) => setSenderEmail(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="receiver-email">To</Label>
                  <Input
                    id="receiver-email"
                    type="email"
                    value={receiverEmail}
                    onChange={(e) => setReceiverEmail(e.target.value)}
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="subject">Subject</Label>
                <Input
                  id="subject"
                  placeholder="Email subject"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="email-content">Message</Label>
                <Textarea
                  id="email-content"
                  value={emailContent}
                  onChange={(e) => setEmailContent(e.target.value)}
                  className="min-h-[300px] font-mono text-sm"
                  placeholder="Click 'Generate Email from Discussion' to create content based on the debate..."
                />
              </div>
              
              <div className="space-y-3">
                <Button 
                  onClick={generateEmailContent}
                  className="w-full bg-green-600 hover:bg-green-700"
                  disabled={!selectedPolicy}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Generate Email from Discussion
                </Button>
                
                <div className="flex gap-2">
                  <Button 
                    onClick={copyToClipboard}
                    variant="outline"
                    className="flex-1"
                    disabled={!emailContent || !senderEmail || !receiverEmail || !subject}
                  >
                    {isCopied ? (
                      <>
                        <Check className="w-4 h-4 mr-2" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4 mr-2" />
                        Copy Email
                      </>
                    )}
                  </Button>
                  
                  <Button 
                    onClick={sendEmail}
                    className="flex-1 bg-blue-600 hover:bg-blue-700"
                    disabled={!emailContent || !senderEmail || !receiverEmail || !subject}
                  >
                    <Send className="w-4 h-4 mr-2" />
                    Send Email
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default EmailGenerator;
