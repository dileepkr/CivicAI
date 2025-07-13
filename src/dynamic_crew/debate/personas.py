"""
Human-like persona creation for policy debate participants.
"""

import random
from typing import Dict, List, Any


class HumanPersona:
    """
    Creates human-like personas for debate agents
    """
    
    PERSONA_TEMPLATES = {
        "Tenants": {
            "name": "Maria Rodriguez",
            "age": 34,
            "background": "Single mother working two jobs to afford rent in SF",
            "personality": "passionate, articulate, speaks from personal experience",
            "speech_style": "direct, emotional, uses personal anecdotes",
            "key_phrases": ["As someone who's lived this...", "Let me tell you what really happens...", "This isn't about numbers, it's about families"],
            "concerns": ["rent affordability", "housing stability", "family welfare"],
            "emotional_triggers": ["eviction fears", "rising costs", "displacement"],
            "response_style": "interrupts when emotional, uses personal stories to counter statistics"
        },
        "Landlords": {
            "name": "Robert Chen",
            "age": 52,
            "background": "Small property owner with 8 rental units, former contractor",
            "personality": "practical, business-minded, but understands tenant struggles",
            "speech_style": "measured, uses business examples, appeals to economic logic",
            "key_phrases": ["From a practical standpoint...", "I've seen what happens when...", "Let's look at the real numbers here"],
            "concerns": ["property maintenance costs", "regulatory compliance", "investment viability"],
            "emotional_triggers": ["unfair regulations", "financial losses", "property damage"],
            "response_style": "becomes defensive when called greedy, uses concrete examples"
        },
        "City Officials": {
            "name": "Councilwoman Sarah Kim",
            "age": 41,
            "background": "Former urban planner, elected to city council 3 years ago",
            "personality": "diplomatic, data-driven, seeks compromise",
            "speech_style": "formal but approachable, cites studies and statistics",
            "key_phrases": ["The data shows us...", "We need to balance...", "Our constituents deserve"],
            "concerns": ["policy effectiveness", "public welfare", "political feasibility"],
            "emotional_triggers": ["housing crisis", "constituent pressure", "budget constraints"],
            "response_style": "tries to find middle ground, cites research and best practices"
        },
        "Housing Advocates": {
            "name": "Dr. James Washington",
            "age": 39,
            "background": "Housing rights attorney and community organizer",
            "personality": "passionate advocate, well-informed, confrontational when needed",
            "speech_style": "forceful, uses legal terminology, challenges opposition directly",
            "key_phrases": ["This is a fundamental right...", "The law clearly states...", "We cannot stand by while..."],
            "concerns": ["tenant rights", "housing justice", "systemic inequality"],
            "emotional_triggers": ["discrimination", "exploitation", "displacement"],
            "response_style": "challenges opponents directly, quotes legal precedents"
        },
        "Property Owners": {
            "name": "Jennifer Martinez",
            "age": 48,
            "background": "Real estate investor with 15 rental properties",
            "personality": "analytical, business-focused, concerned about regulations",
            "speech_style": "professional, uses market data, focuses on economics",
            "key_phrases": ["The market reality is...", "From an investment perspective...", "This affects property values because..."],
            "concerns": ["return on investment", "regulatory compliance", "market stability"],
            "emotional_triggers": ["rent control", "excessive regulations", "profit margins"],
            "response_style": "defends position with data, warns about market consequences"
        },
        "Community Organizations": {
            "name": "Rev. Michael Thompson",
            "age": 55,
            "background": "Community leader and affordable housing advocate",
            "personality": "compassionate, experienced, speaks for the community",
            "speech_style": "inspiring, uses community examples, appeals to fairness",
            "key_phrases": ["Our community needs...", "I've seen families struggle with...", "This is about basic human dignity"],
            "concerns": ["community stability", "affordable housing", "social justice"],
            "emotional_triggers": ["displacement", "gentrification", "inequality"],
            "response_style": "speaks from community experience, emphasizes moral imperatives"
        }
    }
    
    @classmethod
    def create_persona(cls, stakeholder_name: str, stakeholder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a human persona for a stakeholder"""
        
        # Find the best matching template
        template = cls._find_best_template(stakeholder_name)
        
        if not template:
            # Create generic template
            template = {
                "name": f"{stakeholder_name} Representative",
                "age": random.randint(25, 65),
                "background": f"Experienced advocate for {stakeholder_name.lower()}",
                "personality": "articulate, passionate about their cause",
                "speech_style": "direct, uses examples from experience",
                "key_phrases": [f"Speaking for {stakeholder_name.lower()}...", "Our experience shows...", "This directly affects us because..."],
                "concerns": stakeholder_data.get("interests", []),
                "emotional_triggers": stakeholder_data.get("key_concerns", []),
                "response_style": "responds with facts and personal experience"
            }
        
        # Enhance with stakeholder-specific data
        enhanced_persona = {
            **template,
            "stakeholder_group": stakeholder_name,
            "likely_stance": stakeholder_data.get("likely_stance", "neutral"),
            "specific_interests": stakeholder_data.get("interests", []),
            "policy_concerns": stakeholder_data.get("key_concerns", []),
            "impact_level": stakeholder_data.get("impact", "moderate")
        }
        
        return enhanced_persona
    
    @classmethod
    def _find_best_template(cls, stakeholder_name: str) -> Dict[str, Any]:
        """Find the best matching template for a stakeholder"""
        stakeholder_lower = stakeholder_name.lower()
        
        # Direct matches
        if stakeholder_name in cls.PERSONA_TEMPLATES:
            return cls.PERSONA_TEMPLATES[stakeholder_name].copy()
        
        # Keyword matching
        for template_name, template in cls.PERSONA_TEMPLATES.items():
            if template_name.lower() in stakeholder_lower or stakeholder_lower in template_name.lower():
                return template.copy()
        
        # Partial matches
        keyword_matches = {
            "tenant": "Tenants",
            "renter": "Tenants", 
            "landlord": "Landlords",
            "property owner": "Property Owners",
            "owner": "Property Owners",
            "city": "City Officials",
            "government": "City Officials",
            "official": "City Officials",
            "advocate": "Housing Advocates",
            "housing": "Housing Advocates",
            "community": "Community Organizations",
            "organization": "Community Organizations"
        }
        
        for keyword, template_name in keyword_matches.items():
            if keyword in stakeholder_lower:
                return cls.PERSONA_TEMPLATES[template_name].copy()
        
        return None
    
    @classmethod
    def humanize_argument(cls, persona: Dict[str, Any], content: str, evidence: List[str], argument_type: str, context: str = "") -> str:
        """Convert structured argument to natural human speech with context awareness"""
        
        person_name = persona['name']
        response_style = persona.get('response_style', 'responds thoughtfully')
        
        # Physical cues based on argument type and context
        if "responding to" in context.lower():
            physical_cues = ["*leans forward intensely*", "*gestures emphatically*", "*voice rising slightly*"]
        elif argument_type == "rebuttal":
            physical_cues = ["*shakes head*", "*looks directly at opponent*", "*taps table for emphasis*"]
        else:
            physical_cues = ["*adjusts posture*", "*looks around table*", "*speaks clearly*"]
        
        physical_cue = random.choice(physical_cues)
        
        # Conversational starters based on context
        if "responding to" in context.lower():
            starters = ["Wait, hold on...", "That's not how I see it...", "I have to push back on that...", "Let me respond to that point..."]
        elif argument_type == "rebuttal":
            starters = ["I disagree with that completely...", "That's simply not true...", "I need to challenge that..."]
        else:
            starters = persona.get('key_phrases', ["Let me be clear..."])
        
        starter = random.choice(starters if isinstance(starters, list) else [starters])
        
        # Emotional intensity based on persona and context
        if any(trigger in content.lower() for trigger in persona.get('emotional_triggers', [])):
            intensity = ["*voice passionate*", "*speaking with conviction*", "*clearly emotional*"]
            intensity_cue = random.choice(intensity)
        else:
            intensity_cue = ""
        
        # Build the human speech
        human_speech = f"{physical_cue}\n\n{starter} {content}"
        
        # Add evidence naturally
        if evidence:
            evidence_intro = ["Look at the facts:", "The evidence shows:", "We know that:"]
            human_speech += f"\n\n{random.choice(evidence_intro)} {evidence[0]}"
        
        # Add emotional intensity if present
        if intensity_cue:
            human_speech += f"\n\n{intensity_cue}"
        
        # Add conversational elements
        return cls._add_conversational_elements(human_speech, persona, argument_type, context)
    
    @classmethod
    def _add_conversational_elements(cls, content: str, persona: Dict[str, Any], argument_type: str, context: str = "") -> str:
        """Add natural conversational elements"""
        
        # Add natural pauses and emphasis
        conversation_elements = []
        
        if "responding to" in context.lower():
            conversation_elements.extend([
                "You know what?",
                "Here's the thing...",
                "I need to be honest here...",
                "Let me be straight with you..."
            ])
        
        if argument_type == "rebuttal":
            conversation_elements.extend([
                "That's just not realistic...",
                "I've seen this before...",
                "We tried that approach...",
                "The reality is..."
            ])
        
        # Add dramatic pauses
        if random.random() < 0.3:  # 30% chance
            content += "\n\n*pauses dramatically*"
        
        # Add conversational element
        if conversation_elements and random.random() < 0.4:  # 40% chance
            element = random.choice(conversation_elements)
            content = f"{element} {content}"
        
        return content 