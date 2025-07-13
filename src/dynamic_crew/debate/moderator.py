"""
AI Moderator for human-like policy debates.
"""

import random
from typing import Dict, List, Any


class HumanModerator:
    """
    AI moderator with personality and natural speech patterns
    """
    
    def __init__(self):
        self.name = "Dr. Patricia Williams"
        self.background = "Former journalist and policy expert, now facilitates public debates"
        self.personality = "Professional but warm, keeps discussions focused while allowing passion"
        self.transition_phrases = [
            "Let's move to our next important topic...",
            "This brings us to another crucial issue...",
            "I'd like to shift our focus to...",
            "Building on what we've heard, let's explore...",
            "Now, let's examine..."
        ]
        self.interruption_phrases = [
            "Hold on, let me make sure everyone gets a chance to respond...",
            "I want to give everyone a chance to address this point...",
            "Let's hear from other perspectives on this...",
            "That's a strong point - how do others respond to that?",
            "I'm seeing some passionate reactions here..."
        ]
        self.wrap_up_phrases = [
            "As we wrap up this topic...",
            "Before we move on...",
            "Let me summarize what I'm hearing...",
            "This seems to be a key point of disagreement...",
            "I think we've identified the core tensions here..."
        ]
    
    def introduce_debate(self, policy_title: str, participants: List[str], topics: List[str]) -> str:
        """Opening introduction"""
        return f"""
*adjusts glasses and looks at the panel*

Good evening, everyone. I'm Dr. Patricia Williams, and I'll be moderating tonight's discussion on {policy_title}.

We have {len(participants)} distinguished panelists with us tonight: {', '.join(participants)}. Each brings a unique perspective to this important policy debate.

*gestures to the agenda*

Tonight we'll explore {len(topics)} key areas: {', '.join(topics[:3])}{'...' if len(topics) > 3 else ''}. 

I encourage passionate but respectful dialogue. This is about real people and real consequences.

*turns to the panel*

Let's begin with opening statements. Each of you will have a chance to present your perspective, and then we'll dive into the details.
"""
    
    def transition_to_topic(self, topic_title: str, topic_number: int, total_topics: int) -> str:
        """Transition to new topic"""
        phrase = random.choice(self.transition_phrases)
        return f"""
*leans forward slightly*

{phrase} {topic_title}.

*looks around the table*

This is topic {topic_number} of {total_topics}, and I suspect we'll see some strong opinions here. Let's hear how each of you views this issue.
"""
    
    def facilitate_exchange(self, speaker1: str, speaker2: str, topic: str) -> str:
        """Encourage direct exchange between speakers"""
        return f"""
*notices the tension*

{speaker1}, I can see you have a strong reaction to what {speaker2} just said. Please respond directly to their point about {topic}.

*turns to {speaker2}*

And {speaker2}, I want you to have a chance to respond to {speaker1}'s concerns as well.
"""
    
    def interrupt_for_balance(self, dominant_speaker: str, quiet_speakers: List[str]) -> str:
        """Interrupt to give others a chance"""
        phrase = random.choice(self.interruption_phrases)
        quiet_list = ', '.join(quiet_speakers)
        return f"""
*raises hand gently*

{dominant_speaker}, you're making important points, but {phrase}

*turns to others*

{quiet_list}, I'd like to hear your thoughts on this. How do you see this issue?
"""
    
    def wrap_up_topic(self, topic_title: str, key_points: List[str]) -> str:
        """Wrap up discussion of a topic"""
        phrase = random.choice(self.wrap_up_phrases)
        return f"""
*pauses thoughtfully*

{phrase} on {topic_title}.

*counts on fingers*

I'm hearing several key tensions: {', '.join(key_points[:3])}. These seem to be the fundamental disagreements we need to grapple with.

*looks at the panel*

Let's carry these insights forward as we continue.
"""
    
    def synthesize_conclusion(self, policy_title: str, all_arguments: List[Dict], participants: List[str]) -> str:
        """Create unbiased conclusion based on all arguments"""
        # Extract key themes and concerns from arguments
        participant_concerns = {}
        common_themes = []
        
        for arg in all_arguments:
            speaker = arg.get('speaker', 'Unknown')
            stakeholder = arg.get('stakeholder_group', 'Unknown')
            if stakeholder not in participant_concerns:
                participant_concerns[stakeholder] = []
            participant_concerns[stakeholder].append(arg.get('content', ''))
        
        # Identify common themes (simplified approach)
        if len(participants) > 1:
            common_themes = [
                "the complexity of implementation",
                "the need for balanced solutions",
                "concerns about unintended consequences"
            ]
        
        # Build conclusion based on actual arguments
        conclusion_parts = []
        
        for i, participant in enumerate(participants):
            if i < len(all_arguments):
                stakeholder_group = all_arguments[i].get('stakeholder_group', participant)
                conclusion_parts.append(f"From {participant}'s perspective, we heard genuine concerns about the impacts on {stakeholder_group.lower()}. Their lived experience brings credibility to arguments about practical implementation challenges.")
        
        return f"""
*removes glasses and looks thoughtfully at the panel*

Thank you all for this rich discussion on {policy_title}. As someone who's moderated hundreds of these debates, I want to offer an unbiased synthesis of what we've heard tonight.

*gestures to notes*

**The Situation As I See It:**

{' '.join(conclusion_parts)}

**Areas of Surprising Agreement:**
- All participants seem to agree that this policy addresses real problems
- Everyone acknowledges {', '.join(common_themes[:2])}
- There's consensus that effective implementation requires careful planning

**The Core Tensions:**
1. **Immediate vs. Long-term**: Some prioritize immediate relief, others focus on sustainable solutions
2. **Individual vs. Collective**: Tension between personal rights and community needs  
3. **Practical vs. Idealistic**: Disagreement on what's actually achievable

**My Unbiased Assessment:**
This policy addresses real problems, but implementation will require balancing competing interests. The most viable path forward likely involves incremental implementation with ongoing monitoring, while addressing the legitimate concerns raised by all sides.

*looks directly at audience*

The truth is, all our panelists raised valid points. Good policy isn't about winning debates - it's about finding solutions that work for real people in real situations.

*pauses*

That's the situation as I see it. Thank you all for your participation tonight.
""" 