# CivicAI - Comprehensive Policy Analysis & Civic Engagement Platform

A sophisticated multi-agent system that combines dynamic policy analysis, stakeholder debate facilitation, and intelligent policy discovery across multiple levels of government. Built with CrewAI framework, supporting both Gemini API/Serper search and Exa API for comprehensive civic engagement.

## 🚀 Features

### 📊 **Dynamic Policy Analysis & Debate**
- **📁 Local Policy Analysis**: Read and analyze policy documents from local files
- **🤖 Dynamic Agent Creation**: Automatically create specialized agents for each stakeholder
- **🧠 AI-Powered Stakeholder Identification**: Use Gemini API to identify key stakeholders
- **📚 Knowledge Base Management**: Each stakeholder agent maintains its own research database
- **⚖️ Multi-Perspective Analysis**: Comprehensive policy analysis from all stakeholder viewpoints
- **🎭 Automated Debate Facilitation**: Agents debate policy implications and generate balanced summaries
- **🔍 Advanced Web Search**: Serper-powered web search for comprehensive policy research

### 🏛️ **Multi-Level Policy Discovery**
- **Multi-Level Government Search**: Federal, State (California), Local (San Francisco)
- **Intelligent Policy Classification**: Automated domain and stakeholder impact analysis
- **Real-time Discovery**: Up-to-date policy information from government sources
- **Stakeholder-Aware**: Personalized policy relevance based on user roles
- **Multi-Agent Architecture**: Scalable CrewAI-based design

## 🛠️ Setup

### Prerequisites
- Python 3.10+
- UV package manager (recommended) or pip
- API keys: Gemini API, Serper API, and/or Exa API

### Installation

#### Option 1: UV (Recommended)
Install [UV](https://docs.astral.sh/uv/) - the fast Python package manager:

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then install dependencies:
```bash
# Clone the repository
git clone <repository-url>
cd CivicAI

# Install dependencies with UV
uv sync

# Install with development dependencies
uv sync --extra dev
```

#### Option 2: Pip (Fallback)
```bash
cd CivicAI
pip install -e .
```

### Configuration

1. Copy `.env.example` to `.env`
2. Add your API keys:
```env
# For debate system
GEMINI_API_KEY=your_gemini_api_key_here
SERPER_API_KEY=your_serper_api_key_here

# For policy discovery
EXA_API_KEY=your_exa_api_key_here

# Optional configuration
POLICY_DATA_PATH=./test_data
KNOWLEDGE_BASE_PATH=./knowledge
DEBUG=True
VERBOSE=True
```

## 🚀 Usage

### Policy Analysis & Debate System

#### Basic Analysis
```bash
python main.py run policy_1
```

#### Enhanced Analysis with Dynamic Agents
```bash
python main.py dynamic policy_1
```

#### Structured Policy Debate
```bash
python main.py debate policy_1
```
*Conducts structured debates between stakeholder agents using A2A protocols*

#### Demo
```bash
python demo.py
```
*Demonstrates all features including debate system*

#### Available Commands
- `run` - Basic policy analysis
- `dynamic` - Enhanced analysis with dynamic stakeholder agents
- `debate` - Structured debate with A2A protocols
- `train` - Train the crew with custom data
- `replay` - Replay specific tasks
- `test` - Test crew performance

### Policy Discovery System

#### Quick Test
```bash
# Run the policy discovery example
uv run python policy_discovery/example.py

# Or with make
make run-example
```

#### Development Commands
```bash
# View all commands
make help

# Development setup
make dev-setup

# Run tests and quality checks
make test
make lint
make type-check
make check        # Run all checks

# Format code
make format

# Clean up
make clean
```

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
- Uses Serper search and/or Exa API for additional policy context and research
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
- Uses multiple search APIs for comprehensive web research
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
- **Exa API**: Intelligent policy discovery
- **CrewAI**: Multi-agent orchestration
- **Web Scraping**: Additional content extraction

### 🎭 **Structured Debate System**
- **DebateModerator**: Unbiased agent that analyzes topics and guides discussions
- **TopicAnalyzer**: Identifies key areas of contention and debate priorities
- **ArgumentGenerator**: Creates evidence-based arguments from stakeholder perspectives
- **A2AMessenger**: Facilitates structured Agent-to-Agent communication
- **A2A Protocols**: Ensures proper argumentative framework and communication flow

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
- **Exa API**: Get your key from Exa.ai

Add the keys to your `.env` file for the system to function properly.

## 🏗️ Project Structure

- `policy_discovery/` - Core policy discovery module
- `src/dynamic_crew/` - Dynamic debate system components
- `pyproject.toml` - Project configuration
- `Makefile` - Development automation
- `uv.lock` - Dependency lock file
- `knowledge/` - Knowledge base storage
- `test_data/` - Sample policy documents

## 🤝 Contributing

This system is designed for policy analysis and civic engagement. Contributions welcome for:
- Additional policy document formats
- New stakeholder identification algorithms
- Enhanced debate facilitation features
- Integration with civic databases
- Advanced search and research capabilities
- Additional search providers (Exa, Tavily, etc.)

### Development Setup
1. Set up development environment: `make dev-setup`
2. Make your changes
3. Run quality checks: `make check`
4. Submit a pull request

## 📄 License

See LICENSE file for details.
