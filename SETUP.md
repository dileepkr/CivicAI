# CivicAI Setup Guide

This guide will help you set up the CivicAI Policy Analysis system with Serper web search integration.

## 🔑 API Keys Required

You'll need to obtain the following API keys:

### 1. Gemini API Key
- Visit [Google AI Studio](https://ai.google.dev/)
- Create an account or sign in
- Generate a new API key
- Copy the key for use in your `.env` file

### 2. Serper API Key
- Visit [Serper.dev](https://serper.dev/)
- Create an account or sign in
- Navigate to your dashboard
- Generate a new API key
- Copy the key for use in your `.env` file

## 🛠️ Environment Setup

1. **Create `.env` file** in the root directory:
   ```bash
   touch .env
   ```

2. **Add your API keys** to the `.env` file:
   ```env
   # API Keys - Required for the system to function
   GEMINI_API_KEY=your_gemini_api_key_here
   SERPER_API_KEY=your_serper_api_key_here
   
   # Policy Analysis Configuration
   POLICY_DATA_PATH=./test_data
   KNOWLEDGE_BASE_PATH=./knowledge
   
   # Debug Settings
   DEBUG=True
   VERBOSE=True
   ```

3. **Install dependencies**:
   ```bash
   pip install -e .
   ```

## 🧪 Testing Your Setup

1. **Run the demo**:
   ```bash
   python demo.py
   ```

2. **Check for errors**:
   - If you see "❌ Error: GEMINI_API_KEY not found", add your Gemini API key
   - If you see "❌ Error: SERPER_API_KEY not found", add your Serper API key
   - If you see "✅ API keys configured", you're ready to go!

## 🚀 Running Policy Analysis

### Basic Analysis
```bash
python -m src.dynamic_crew_automation_for_policy_analysis_and_debate.main run policy_1
```

### Enhanced Analysis with Dynamic Agents
```bash
python -m src.dynamic_crew_automation_for_policy_analysis_and_debate.main dynamic policy_1
```

## 🔍 What Serper Brings to the System

Serper provides powerful web search capabilities that enhance policy analysis by:

- **Real-time Search**: Access current information from across the web
- **Comprehensive Results**: Find relevant policy documents, news, and analysis
- **Stakeholder Research**: Discover how policies affect different groups
- **Fast Performance**: Quick search results for efficient policy analysis
- **Cost-effective**: Affordable web search API for research purposes

## 🛠️ Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   # Reinstall dependencies
   pip install -e .
   ```

2. **API Key Issues**:
   - Double-check your API keys are correctly copied
   - Ensure no extra spaces or characters
   - Verify the keys are active in your respective accounts
   - Check that you have sufficient credits in Serper

3. **Permission Errors**:
   ```bash
   # Make sure you have write permissions
   chmod +x demo.py
   ```

### Getting Help

If you encounter issues:
1. Check the console output for specific error messages
2. Verify your API keys are working by testing them directly
3. Ensure all required files are in the correct directories

## 📊 Expected Output

When everything is working correctly, you should see:
- ✅ API keys configured
- ✅ Policy loaded: [Policy Title]
- ✅ Found X stakeholders
- 🤖 Created agent: [Agent Name]
- 📚 Knowledge base entries created
- ✅ Research completed

## 🎯 Next Steps

Once setup is complete:
1. Try analyzing different policies by adding JSON files to `test_data/`
2. Experiment with the dynamic agent creation
3. Explore the knowledge base files created in `knowledge/stakeholders/`
4. Run full policy analysis with web research capabilities

## 🔄 Future Integration

When you're ready to add Exa search capabilities:
1. Sign up for an Exa API key at [Exa.ai](https://exa.ai/)
2. Add `EXA_API_KEY=your_key_here` to your `.env` file
3. Update the dependencies to include `"exa-py>=1.0.0"`
4. The system can be easily configured to use both search providers 