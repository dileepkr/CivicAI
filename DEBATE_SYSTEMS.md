# CivicAI Policy Debate Systems

A comprehensive policy debate system with three distinct implementations for different use cases.

## 🎭 Systems Overview

### 1. **Debug Debate System** (`debug`)
- **Purpose**: Real-time development and debugging
- **Features**: Live agent action logging, minimal overhead
- **Best for**: Development, testing, quick iterations
- **Output**: Console logs with timestamped agent actions

### 2. **Weave Debate System** (`weave`)
- **Purpose**: Production demonstrations with full tracing
- **Features**: Complete W&B Weave integration, comprehensive logging
- **Best for**: Hackathons, demos, production monitoring
- **Output**: Rich traces viewable at https://wandb.ai/aniruddhr04-university-of-cincinnati/civicai-hackathon

### 3. **Human Debate System** (`human`)
- **Purpose**: Natural, conversational policy debates
- **Features**: AI moderator, human-like personas, emotional responses
- **Best for**: Public demonstrations, realistic debate simulations
- **Output**: Natural conversations with moderator guidance and unbiased conclusions

## 🚀 Quick Start

### Running a Debate

```bash
# Debug system - Fast development
python run_debate.py debug policy_1

# Weave system - Full tracing
python run_debate.py weave policy_2

# Human system - Natural conversations
python run_debate.py human policy_1
```

### Using Individual Systems

```python
from src.dynamic_crew.debate import DebugDebateSystem, WeaveDebateSystem, HumanDebateSystem

# Debug system
debug_system = DebugDebateSystem()
results = debug_system.run_debate("policy_1")

# Weave system
weave_system = WeaveDebateSystem()
results = weave_system.run_debate("policy_2")

# Human system
human_system = HumanDebateSystem()
results = human_system.run_debate("policy_1")
```

## 📁 Project Structure

```
src/dynamic_crew/debate/
├── __init__.py                 # Main exports
├── base.py                     # Common functionality
├── moderator.py                # AI moderator logic
├── personas.py                 # Human-like persona creation
├── systems/
│   ├── debug.py               # Debug debate system
│   ├── weave.py               # Weave-integrated system
│   └── human.py               # Human-like system
└── examples/
    ├── run_debug_debate.py    # Debug system runner
    ├── run_weave_debate.py    # Weave system runner
    └── run_human_debate.py    # Human system runner
```

## 🔧 System Details

### Debug Debate System

**Key Features:**
- Real-time agent action logging
- Minimal performance overhead
- Live debate round visualization
- A2A message tracking
- Error handling with detailed feedback

**Use Cases:**
- Development and debugging
- Quick policy testing
- Performance optimization
- Integration testing

**Example Output:**
```
[14:32:15] 🤖 Tenants Agent: Preparing claim...
[14:32:16] ✅ Tenants Agent: Statement delivered
💬 Tenants: Rent caps are essential for housing stability...
   (Argument strength: 8/10)
```

### Weave Debate System

**Key Features:**
- Full W&B Weave integration
- Comprehensive operation tracing
- Rich metadata logging
- Performance monitoring
- Hackathon-ready demonstrations

**Use Cases:**
- Production monitoring
- Hackathon demonstrations
- Performance analysis
- Team collaboration

**Trace Dashboard:**
- View at: https://wandb.ai/aniruddhr04-university-of-cincinnati/civicai-hackathon
- Includes: Agent actions, argument generation, A2A messaging, timing data

### Human Debate System

**Key Features:**
- AI moderator (Dr. Patricia Williams)
- Human-like personas with personalities
- Natural conversation flow
- Emotional responses and triggers
- Unbiased conclusion synthesis

**Personas Available:**
- **Maria Rodriguez** (Tenants) - Passionate single mother
- **Robert Chen** (Landlords) - Practical property owner
- **Councilwoman Sarah Kim** (City Officials) - Data-driven diplomat
- **Dr. James Washington** (Housing Advocates) - Rights attorney

**Moderator Capabilities:**
- Topic transitions
- Speaking balance enforcement
- Direct exchange facilitation
- Unbiased conclusion synthesis

## 🛠️ Configuration

### Environment Variables

```bash
# Required for all systems
GEMINI_API_KEY=your_gemini_key_here
SERPER_API_KEY=your_serper_key_here

# Optional for Weave system
WANDB_API_KEY=your_wandb_key_here
```

### Policy Files

Place policy files in `test_data/` directory:
- `policy_1.json` - AB 1248: Property fees and charges
- `policy_2.json` - Rent Stabilization Ordinance

### Custom Policies

Create new policy files with structure:
```json
{
  "request_id": "unique_id",
  "user_profile": {
    "persona": "Renter",
    "location": "San Francisco, CA",
    "initial_stance": "Undecided"
  },
  "policy_document": {
    "title": "Policy Title",
    "source_url": "https://source.url",
    "text": "Full policy text here..."
  }
}
```

## 🎯 Use Case Examples

### For Development
```bash
# Quick testing during development
python run_debate.py debug policy_1

# Check specific functionality
python src/dynamic_crew/examples/run_debug_debate.py policy_2
```

### For Demonstrations
```bash
# Full-featured demo with tracing
python run_debate.py weave policy_1

# Human-like conversation for audiences
python run_debate.py human policy_2
```

### For Production
```python
from src.dynamic_crew.debate import WeaveDebateSystem

# Production monitoring
system = WeaveDebateSystem()
results = system.run_debate("policy_name")

# Access trace URL
trace_url = "https://wandb.ai/aniruddhr04-university-of-cincinnati/civicai-hackathon"
```

## 📊 Output Structure

### Common Fields (All Systems)
```python
{
    "session_id": "system_name_abc123",
    "policy_info": {...},
    "stakeholders": [...],
    "topics": [...],
    "conversation_history": [...],
    "duration": 45.2,
    "start_time": "2024-01-01T12:00:00",
    "end_time": "2024-01-01T12:00:45"
}
```

### Debug System Specific
```python
{
    "debate_rounds": [...],
    "a2a_messages": [...],
    "research": {...}
}
```

### Weave System Specific
```python
{
    "round_results": [...],
    "stakeholder_research": {...},
    "all_arguments": [...]
}
```

### Human System Specific
```python
{
    "personas": {...},
    "moderator_conclusion": "...",
    "speaking_stats": {...},
    "topics_discussed": [...]
}
```

## 🔍 Troubleshooting

### Common Issues

1. **Missing API Keys**
   ```bash
   # Check environment variables
   echo $GEMINI_API_KEY
   echo $SERPER_API_KEY
   ```

2. **Import Errors**
   ```python
   # Ensure proper Python path
   import sys
   sys.path.insert(0, '/path/to/CivicAI')
   ```

3. **Policy File Not Found**
   ```bash
   # Check file exists
   ls test_data/policy_1.json
   ```

### Debugging Tips

- Use `debug` system for development
- Check console logs for error details
- Verify policy JSON format
- Ensure virtual environment is activated

## 🤝 Integration with Existing Code

### With CrewAI
```python
from src.dynamic_crew.debate import HumanDebateSystem
from src.dynamic_crew.crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew

# Use debate system with existing crew
debate_system = HumanDebateSystem()
crew_instance = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()

# Run integrated workflow
results = debate_system.run_debate("policy_1")
```

### With Custom Tools
```python
from src.dynamic_crew.debate.base import BaseDebateSystem

class CustomDebateSystem(BaseDebateSystem):
    def __init__(self):
        super().__init__("custom_debate")
        
    def run_debate(self, policy_name):
        # Custom implementation
        pass
```

## 📈 Performance Considerations

### Debug System
- **Fastest**: Minimal overhead, real-time logging
- **Memory**: Low memory usage
- **Network**: Standard API calls only

### Weave System
- **Moderate**: Additional tracing overhead
- **Memory**: Higher due to trace data
- **Network**: Extra W&B communication

### Human System
- **Slowest**: Complex persona interactions
- **Memory**: Highest due to conversation history
- **Network**: Standard API calls + optional Weave

## 🎨 Customization

### Adding New Personas
```python
# In personas.py
PERSONA_TEMPLATES["New Stakeholder"] = {
    "name": "Custom Name",
    "age": 40,
    "background": "Custom background",
    "speech_style": "Custom style",
    # ... other attributes
}
```

### Custom Moderator Phrases
```python
# In moderator.py
def __init__(self):
    self.transition_phrases = [
        "Moving to our next topic...",
        # Add custom phrases
    ]
```

### New System Implementation
```python
from src.dynamic_crew.debate.base import BaseDebateSystem

class YourCustomSystem(BaseDebateSystem):
    def __init__(self):
        super().__init__("your_system")
        
    def create_personas(self, stakeholder_list):
        # Custom persona creation
        pass
        
    def run_debate(self, policy_name):
        # Custom debate implementation
        pass
```

## 📚 API Reference

### Base Classes
- `BaseDebateSystem`: Common functionality
- `HumanModerator`: AI moderator logic
- `HumanPersona`: Persona creation utilities

### System Classes
- `DebugDebateSystem`: Debug implementation
- `WeaveDebateSystem`: Weave-traced implementation
- `HumanDebateSystem`: Human-like implementation

### Key Methods
- `run_debate(policy_name)`: Main debate execution
- `load_policy(policy_name)`: Policy loading
- `identify_stakeholders(policy_text)`: Stakeholder identification
- `create_personas(stakeholder_list)`: Persona creation

---

This system is designed to be easily extensible while maintaining clean separation of concerns. Each system can be used independently or integrated into larger workflows. 