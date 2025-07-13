# Gemini LLM Setup Guide

This guide will help you set up Gemini LLMs for the CivicAI Policy Debate System.

## Prerequisites

1. **Google Cloud Account**: You need a Google Cloud account to access Gemini API
2. **API Key**: Generate a Google API key for Gemini access
3. **Python Environment**: Make sure you have Python 3.9+ installed

## Step 1: Get Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

## Step 2: Set Environment Variable

Set your Google API key as an environment variable:

```bash
export GOOGLE_API_KEY="your_google_api_key_here"
```

For permanent setup, add it to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
echo 'export GOOGLE_API_KEY="your_google_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

## Step 3: Install Dependencies

Make sure you're in your virtual environment:

```bash
# If using uv
source .venv/bin/activate

# Install crewai if not already installed
uv pip install crewai
```

## Step 4: Test the Setup

Run the test script to verify everything is working:

```bash
python test_gemini_setup.py
```

## Step 5: Use the System

The system will now automatically use Gemini as the primary LLM. If Gemini is not available, it will fall back to:

1. **Groq** (if `GROQ_API_KEY` is set)
2. **OpenAI** (if `OPENAI_API_KEY` is set)
3. **Robust multi-provider client** (as last resort)

## Configuration Details

### Primary Configuration
- **Model**: `gemini-1.5-flash` (fast and capable)
- **Provider**: Google
- **API Key**: `GOOGLE_API_KEY` environment variable

### Fallback Configuration
- **Groq**: `llama3-8b-8192` model
- **OpenAI**: `gpt-3.5-turbo` model
- **Robust Client**: Multi-provider with automatic fallback

## Troubleshooting

### Common Issues

1. **"GOOGLE_API_KEY not found"**
   - Make sure you've set the environment variable
   - Restart your terminal after setting it

2. **"Gemini configuration failed"**
   - Check your API key is valid
   - Ensure you have billing enabled on Google Cloud
   - Verify your API key has Gemini access

3. **"ModuleNotFoundError: No module named 'crewai'"**
   - Make sure you're in the correct virtual environment
   - Install crewai: `uv pip install crewai`

### Testing Individual Components

Test Gemini directly:
```python
from crewai import LLM

llm = LLM(
    model="gemini-1.5-flash",
    api_key="your_api_key",
    provider="google"
)

response = llm.call("Hello, world!")
print(response)
```

## API Usage and Costs

- **Gemini 1.5 Flash**: Fast and cost-effective for most tasks
- **Pricing**: Check [Google AI Studio pricing](https://ai.google.dev/pricing)
- **Rate Limits**: Monitor usage in Google Cloud Console

## Support

If you encounter issues:

1. Check the test script output for specific error messages
2. Verify your API key and billing setup
3. Ensure you're using the correct virtual environment
4. Check that all dependencies are installed

## Next Steps

Once Gemini is working:

1. Run the full system: `python main.py`
2. Test policy analysis workflows
3. Monitor performance and costs
4. Adjust configuration as needed 