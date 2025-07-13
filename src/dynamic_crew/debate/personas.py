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
            "personality": "passionate, caring, speaks from personal experience",
            "speech_style": "simple, emotional, uses everyday examples",
            "key_phrases": ["As someone who rents...", "Let me tell you what happens to families like mine...", "This isn't just about money, it's about our homes"],
            "concerns": ["affordable rent", "keeping my apartment", "my family's safety"],
            "emotional_triggers": ["losing my home", "rent going up", "having to move"],
            "response_style": "gets emotional when talking about home, uses simple stories about daily life"
        },
        "Landlords": {
            "name": "Robert Chen",
            "age": 52,
            "background": "Small property owner with 8 rental units, former contractor",
            "personality": "practical, business-minded, but cares about tenants",
            "speech_style": "straightforward, uses real examples, talks about costs",
            "key_phrases": ["From what I've seen...", "Here's what actually happens...", "Let's look at the real costs"],
            "concerns": ["fixing and maintaining properties", "following new rules", "making enough to stay in business"],
            "emotional_triggers": ["unfair rules", "losing money", "property damage"],
            "response_style": "gets defensive about being called greedy, uses concrete examples from his properties"
        },
        "City Officials": {
            "name": "Councilwoman Sarah Kim",
            "age": 41,
            "background": "Former urban planner, elected to city council 3 years ago",
            "personality": "diplomatic, fair-minded, seeks solutions that work for everyone",
            "speech_style": "clear, balanced, explains things simply",
            "key_phrases": ["The research shows...", "We need to find a balance...", "Our neighbors deserve"],
            "concerns": ["making policies that work", "helping everyone", "using taxpayer money wisely"],
            "emotional_triggers": ["housing crisis", "people losing homes", "budget problems"],
            "response_style": "tries to find middle ground, explains research in simple terms"
        },
        "Housing Advocates": {
            "name": "Dr. James Washington",
            "age": 39,
            "background": "Housing rights attorney and community organizer",
            "personality": "passionate advocate, well-informed, fights for housing rights",
            "speech_style": "strong, uses simple legal terms, challenges unfairness directly",
            "key_phrases": ["Everyone deserves a home...", "The law says...", "We can't let this happen to families..."],
            "concerns": ["tenant rights", "fair housing", "helping people keep their homes"],
            "emotional_triggers": ["discrimination", "people being taken advantage of", "families being forced out"],
            "response_style": "challenges opponents directly, explains legal rights in simple terms"
        },
        "Property Owners": {
            "name": "Jennifer Martinez",
            "age": 48,
            "background": "Real estate investor with 15 rental properties",
            "personality": "analytical, business-focused, concerned about rules affecting her investments",
            "speech_style": "professional, uses market examples, talks about money and business",
            "key_phrases": ["The market shows...", "From a business view...", "This affects property values because..."],
            "concerns": ["making money on investments", "following all the rules", "property values staying up"],
            "emotional_triggers": ["rent control", "too many regulations", "profit margins going down"],
            "response_style": "defends business decisions with data, warns about effects on the housing market"
        },
        "Community Organizations": {
            "name": "Rev. Michael Thompson",
            "age": 55,
            "background": "Community leader and affordable housing advocate",
            "personality": "compassionate, experienced, speaks for the community",
            "speech_style": "inspiring, uses community examples, talks about fairness",
            "key_phrases": ["Our community needs...", "I've seen families struggle with...", "This is about treating people fairly"],
            "concerns": ["keeping the community together", "affordable housing", "helping everyone"],
            "emotional_triggers": ["families being forced out", "neighborhoods changing too fast", "unfair treatment"],
            "response_style": "speaks from community experience, emphasizes doing what's right"
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
        """Convert structured argument to natural human speech in simple language"""
        
        person_name = persona['name']
        response_style = persona.get('response_style', 'responds thoughtfully')
        
        # Simple physical cues based on argument type
        if "responding to" in context.lower():
            physical_cues = ["*leans forward*", "*gestures with hands*", "*voice getting louder*"]
        elif argument_type == "rebuttal":
            physical_cues = ["*shakes head*", "*looks directly at them*", "*taps table*"]
        else:
            physical_cues = ["*sits up straight*", "*looks around table*", "*speaks clearly*"]
        
        physical_cue = random.choice(physical_cues)
        
        # Simple conversational starters
        if "responding to" in context.lower():
            starters = ["Wait, wait...", "I don't see it that way...", "I have to say something about that...", "Let me tell you what I think..."]
        elif argument_type == "rebuttal":
            starters = ["I don't agree with that...", "That's not right...", "I need to say something..."]
        else:
            starters = persona.get('key_phrases', ["Let me explain..."])
        
        starter = random.choice(starters if isinstance(starters, list) else [starters])
        
        # Simple emotional responses
        if any(trigger in content.lower() for trigger in persona.get('emotional_triggers', [])):
            intensity = ["*voice getting emotional*", "*speaking with feeling*", "*clearly upset*"]
            intensity_cue = random.choice(intensity)
        else:
            intensity_cue = ""
        
        # Simplify the content for laypeople
        simplified_content = cls._simplify_content(content)
        
        # Build the simple human speech
        human_speech = f"{physical_cue}\n\n{starter} {simplified_content}"
        
        # Add evidence in simple terms
        if evidence:
            evidence_intro = ["Here's what I know:", "This is what happens:", "Let me show you:"]
            simple_evidence = cls._simplify_content(evidence[0])
            human_speech += f"\n\n{random.choice(evidence_intro)} {simple_evidence}"
        
        # Add emotional intensity if present
        if intensity_cue:
            human_speech += f"\n\n{intensity_cue}"
        
        # Add conversational elements
        return cls._add_conversational_elements(human_speech, persona, argument_type, context)
    
    @classmethod
    def _simplify_content(cls, content: str) -> str:
        """Simplify complex content for layman understanding"""
        # Replace complex terms with simpler ones
        replacements = {
            "implementation": "putting into action",
            "regulatory compliance": "following the rules",
            "stakeholder": "person affected",
            "legislation": "law",
            "pursuant": "according to",
            "comprehensive": "complete",
            "facilitate": "help",
            "substantial": "big",
            "significant": "important",
            "optimize": "make better",
            "utilize": "use",
            "demonstrate": "show",
            "accommodation": "place to live",
            "affordable housing": "homes people can afford",
            "rent control": "limits on rent increases",
            "displacement": "being forced to move",
            "gentrification": "neighborhoods getting expensive",
            "market dynamics": "how the housing market works",
            "property values": "how much homes are worth",
            "investment viability": "whether it's worth investing",
            "regulatory framework": "the rules and laws",
            "socioeconomic": "about money and social class",
            "policy effectiveness": "how well the policy works",
            "constituent": "voter",
            "budgetary constraints": "not having enough money",
            "infrastructure": "basic systems like roads and utilities",
            "zoning": "rules about what can be built where"
        }
        
        simplified = content
        for complex_term, simple_term in replacements.items():
            simplified = simplified.replace(complex_term, simple_term)
        
        # Break up long sentences
        sentences = simplified.split('. ')
        short_sentences = []
        for sentence in sentences:
            if len(sentence) > 100:  # If sentence is too long
                # Try to break it at commas or conjunctions
                parts = sentence.replace(', ', '. ').replace(' and ', '. ').replace(' but ', '. But ')
                short_sentences.append(parts)
            else:
                short_sentences.append(sentence)
        
        return '. '.join(short_sentences)
    
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