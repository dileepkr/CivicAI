# CivicAI - Dynamic Policy Analysis & Debate System

An intelligent multi-agent system for policy analysis and stakeholder debate using CrewAI, Gemini API, Serper search, and advanced natural language processing.

## 🚀 Features

- **📁 Local Policy Analysis**: Read and analyze policy documents from local files
- **🤖 Dynamic Agent Creation**: Automatically create specialized agents for each stakeholder
- **🧠 AI-Powered Stakeholder Identification**: Use Gemini API to identify key stakeholders
- **📚 Knowledge Base Management**: Each stakeholder agent maintains its own research database
- **⚖️ Multi-Perspective Analysis**: Comprehensive policy analysis from all stakeholder viewpoints
- **🎭 Automated Debate Facilitation**: Agents debate policy implications and generate balanced summaries
- **🔍 Advanced Web Search**: Serper-powered web search for comprehensive policy research

## 🛠️ Setup

### Prerequisites
- Python 3.10+
- Gemini API key
- Serper API key

### Installation

1. **Clone and navigate to the project**
   ```bash
   cd CivicAI
   ```

2. **Install dependencies**
   ```bash
   pip install -e .
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   SERPER_API_KEY=your_serper_api_key_here
   POLICY_DATA_PATH=./test_data
   KNOWLEDGE_BASE_PATH=./knowledge
   DEBUG=True
   VERBOSE=True
   ```

## 🚀 Usage

### Basic Analysis
```bash
python main.py run policy_1
```

### Enhanced Analysis with Dynamic Agents
```bash
python main.py dynamic policy_1
```

### Structured Policy Debate
```bash
python main.py debate policy_1
```
*Conducts structured debates between stakeholder agents using A2A protocols*

### Demo
```bash
python demo.py
```
*Demonstrates all features including debate system*

### Available Commands
- `run` - Basic policy analysis
- `dynamic` - Enhanced analysis with dynamic stakeholder agents
- `debate` - Structured debate with A2A protocols
- `train` - Train the crew with custom data
- `replay` - Replay specific tasks
- `test` - Test crew performance

## 📁 Policy File Format

Place your policy files in the `test_data/` directory with the following JSON structure:

```json
{
    "request_id": "unique_identifier",
    "user_profile": {
        "persona": "Stakeholder Type",
        "location": "Geographic Location",
        "initial_stance": "Position"
    },
    "policy_document": {
        "title": "Policy Title",
        "source_url": "https://example.com/policy",
        "text": "Full policy text content..."
    }
}
```

## 🎭 How It Works

### 1. **Policy Discovery Agent**
- Reads local policy files from `test_data/`
- Extracts policy text and metadata
- Uses Serper search for additional policy context and research
- Prepares content for analysis

### 2. **Stakeholder Identification**
- Uses Gemini API to identify key stakeholders
- Analyzes policy text for affected parties
- Determines stakeholder interests and concerns

### 3. **Dynamic Agent Creation**
- Creates specialized agents for each stakeholder
- Configures agents with stakeholder-specific knowledge
- Assigns appropriate tools and capabilities

### 4. **Research & Analysis**
- Each stakeholder agent researches policy impacts
- Uses Serper search for comprehensive web research
- Generates perspective-specific arguments
- Stores findings in individual knowledge bases

### 5. **Synthesis & Reporting**
- Collects all stakeholder perspectives
- Creates balanced policy analysis
- Generates comprehensive summary report

## 🧠 Agent Architecture

### Core Agents
- **Coordinator Agent**: Orchestrates the entire process
- **Policy Discovery Agent**: Handles policy file reading and web research
- **Policy Debate Agent**: Identifies stakeholders and creates dynamic agents
- **Action Agent**: Synthesizes results and generates final reports

### Dynamic Stakeholder Agents
- **Tenant Advocates**: Represent renter interests
- **Landlord Representatives**: Advocate for property owner concerns
- **City Officials**: Focus on regulatory and public safety aspects
- **Community Organizations**: Represent neighborhood and social concerns

## 📚 Knowledge Base System

Each stakeholder agent maintains its own knowledge base:
- **Location**: `knowledge/stakeholders/`
- **Format**: JSON files with research data
- **Features**: Versioning, timestamps, research history

## 🔧 Advanced Features

### Custom Tools
- **PolicyFileReader**: Local policy document reader
- **StakeholderIdentifier**: AI-powered stakeholder detection
- **KnowledgeBaseManager**: Research data management
- **StakeholderResearcher**: Perspective-specific analysis

### API Integration
- **Gemini API**: Advanced language understanding
- **Serper API**: Web search and research
- **CrewAI**: Multi-agent orchestration
- **Web Scraping**: Additional content extraction

## 🎯 Enhanced Features

### 📊 **Dynamic Stakeholder Analysis**
- AI-powered stakeholder identification using Gemini API
- Automatic creation of specialized agents for each stakeholder perspective
- Individual knowledge bases for research storage and retrieval
- Structured policy impact analysis with validated JSON outputs

### 🔍 **Comprehensive Research Tools**
- **PolicyFileReader**: Reads local policy files with structured data validation
- **StakeholderIdentifier**: Uses AI to identify affected parties and their interests
- **StakeholderResearcher**: Conducts detailed analysis from each stakeholder's perspective
- **KnowledgeBaseManager**: Stores and retrieves research findings with version control

### 🎭 **Structured Debate System**
- **DebateModerator**: Unbiased agent that analyzes topics and guides discussions
- **TopicAnalyzer**: Identifies key areas of contention and debate priorities
- **ArgumentGenerator**: Creates evidence-based arguments from stakeholder perspectives
- **A2AMessenger**: Facilitates structured Agent-to-Agent communication
- **A2A Protocols**: Ensures proper argumentative framework and communication flow

### 🌐 **Web Research Integration**
- Powered by Serper search API for comprehensive web research
- Scrapes relevant websites for additional policy context
- Combines local policy analysis with current web information

## 🎯 Example: San Francisco Soft Story Retrofit

The system analyzes SF's Mandatory Soft Story Retrofit Program and automatically identifies:

**Stakeholders Identified:**
- Residential Tenants
- Property Owners/Landlords  
- City Building Department
- Earthquake Safety Commission
- Housing Rights Organizations
- Construction Industry

**Analysis Generated:**
- Economic impact assessments
- Legal compliance requirements
- Safety benefit evaluations
- Cost-sharing implications
- Timeline considerations
- Hardship exemption analysis

## 🚀 Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `run` | Basic policy analysis | `python main.py run policy_1` |
| `dynamic` | Enhanced analysis with dynamic agents | `python main.py dynamic policy_1` |
| `train` | Train the system | `python main.py train 5 training.json policy_1` |
| `replay` | Replay specific task | `python main.py replay task_id` |
| `test` | Test system performance | `python main.py test 3 gemini-pro policy_1` |

## 📈 Output

The system generates:
- **Stakeholder Analysis Reports**: Detailed impact assessments
- **Policy Summary**: Balanced overview of all perspectives  
- **Email Draft**: Professional communication for stakeholders
- **Knowledge Base**: Persistent research data for future reference

## 🔍 Debugging

Enable verbose output by setting `DEBUG=True` in your `.env` file. The system will provide detailed logging of:
- Agent interactions
- Tool usage
- Knowledge base operations
- API calls and responses
- Web search results

## 🔑 API Keys Setup

You'll need to obtain API keys from:
- **Gemini API**: Get your key from Google AI Studio
- **Serper API**: Get your key from Serper.dev

Add both keys to your `.env` file for the system to function properly.

## 🤝 Contributing

This system is designed for policy analysis and civic engagement. Contributions welcome for:
- Additional policy document formats
- New stakeholder identification algorithms
- Enhanced debate facilitation features
- Integration with civic databases
- Advanced search and research capabilities
- Additional search providers (Exa, Tavily, etc.)

## 📄 License

See LICENSE file for details.
