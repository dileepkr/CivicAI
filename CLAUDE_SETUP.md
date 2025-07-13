# Claude LLM Setup Guide

This guide explains how to configure Claude as the primary LLM for all CrewAI agents in the CivicAI system.

## Overview

The system has been updated to use **Claude 3.5 Sonnet** as the primary LLM for all CrewAI agents, with fallback options to other providers if Claude is not available.

## Prerequisites

1. **Anthropic API Key**: You need an API key from Anthropic to use Claude
2. **Python Environment**: Python 3.10+ with the required dependencies

## Setup Steps

### 1. Get Your Anthropic API Key

1. Visit [Anthropic's Console](https://console.anthropic.com/)
2. Sign up or log in to your account
3. Navigate to the API Keys section
4. Create a new API key
5. Copy the API key (it starts with `sk-ant-`)

### 2. Set Environment Variable

Set your Anthropic API key as an environment variable:

```bash
# On macOS/Linux
export ANTHROPIC_API_KEY="sk-ant-your-api-key-here"

# On Windows (Command Prompt)
set ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# On Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-your-api-key-here"
```

### 3. Install Dependencies

The system now includes the Anthropic SDK. Install dependencies:

```bash
# Using UV (recommended)
uv sync

# Using pip (fallback)
pip install -e .
```

### 4. Test Configuration

Run the test script to verify Claude is working:

```bash
python test_claude_config.py
```

You should see output like:
```
🚀 Claude Configuration Test Suite
============================================================
🧪 Testing Claude LLM Configuration
==================================================
✅ ANTHROPIC_API_KEY found
🔄 Initializing CrewAI system with Claude...
✅ LLM configured successfully
   Model: claude-3-5-sonnet-20241022
   Provider: anthropic
🎉 Claude is successfully configured as the primary LLM!
```

## Configuration Details

### Primary LLM: Claude 3.5 Sonnet

- **Model**: `claude-3-5-sonnet-20241022`
- **Provider**: Anthropic
- **Priority**: First choice for all agents

### Fallback Providers (in order)

1. **Gemini 1.5 Flash** (Google)
   - Requires: `GOOGLE_API_KEY`
   - Model: `gemini-1.5-flash`

2. **OpenAI GPT-3.5 Turbo**
   - Requires: `OPENAI_API_KEY`
   - Model: `gpt-3.5-turbo`

3. **Groq** (Fast inference)
   - Requires: `GROQ_API_KEY`
   - Model: `llama3-8b-8192`

4. **Robust Multi-Provider Client**
   - Last resort fallback
   - Uses available providers from W&B Inference

## Usage

Once configured, all CrewAI agents will automatically use Claude:

```python
from src.dynamic_crew.crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew

# Initialize the system
crew_system = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()

# All agents will use Claude automatically
coordinator = crew_system.coordinator_agent()
policy_agent = crew_system.policy_discovery_agent()
# ... etc
```

## Troubleshooting

### Claude Not Working

1. **Check API Key**: Ensure `ANTHROPIC_API_KEY` is set correctly
2. **Check Balance**: Verify you have sufficient credits in your Anthropic account
3. **Check Rate Limits**: Claude has rate limits; check your usage
4. **Fallback**: The system will automatically fall back to other providers

### Common Errors

- **"ANTHROPIC_API_KEY not found"**: Set the environment variable
- **"Claude configuration failed"**: Check your API key and account status
- **"Expected Claude but got [other model]"**: System fell back to another provider

### Testing Fallback Providers

To test fallback providers, temporarily unset the Claude API key:

```bash
unset ANTHROPIC_API_KEY
python test_claude_config.py
```

## Performance Notes

- **Claude 3.5 Sonnet**: Best performance, highest cost
- **Response Time**: Generally 2-5 seconds for typical prompts
- **Context Window**: 200K tokens
- **Rate Limits**: Check Anthropic's current limits

## Cost Considerations

- Claude 3.5 Sonnet pricing: ~$3 per 1M input tokens, ~$15 per 1M output tokens
- Monitor usage in your Anthropic console
- Consider using fallback providers for development/testing

## Support

If you encounter issues:

1. Check the test script output
2. Verify your API key and account status
3. Check the system logs for detailed error messages
4. Ensure all dependencies are installed correctly 