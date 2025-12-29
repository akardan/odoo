# OpenRouter Integration for AK AI Module

## Overview
OpenRouter is now integrated into the AK AI assistant module, giving you access to multiple AI models through a single, unified API.

## What is OpenRouter?
[OpenRouter](https://openrouter.ai) is a unified API that provides access to various AI models from different providers, including:
- OpenAI (GPT-4, GPT-3.5, etc.)
- Anthropic (Claude 3.5 Sonnet, Haiku, etc.)
- Meta (Llama models)
- Google (Gemini Pro, etc.)
- And many more...

## Benefits
1. **Multiple Models**: Access to 100+ AI models through one API
2. **Best Pricing**: Competitive pricing across different providers
3. **Fallback Options**: Automatic model fallback if one is unavailable
4. **Unified Interface**: Same API for all models

## Configuration

### 1. Get OpenRouter API Key
1. Visit [https://openrouter.ai](https://openrouter.ai)
2. Sign up or log in
3. Go to Keys section
4. Generate a new API key

### 2. Configure in Odoo
1. Go to **Settings → AI Assistant → Assistants**
2. Open or create an assistant
3. Set:
   - **AI Provider**: OpenRouter
   - **API Key**: Your OpenRouter API key
   - **API Base URL**: `https://openrouter.ai/api/v1` (default)
   - **Model Name**: Choose from available models (see below)

### 3. Recommended Models

#### For Turkish Language (Best Performance)
```
anthropic/claude-3.5-haiku          # Fast, cost-effective
anthropic/claude-3.5-sonnet         # Best quality
openai/gpt-4o-mini                  # Budget friendly
openai/gpt-4-turbo                  # High quality
```

#### For General Use
```
meta-llama/llama-3.1-70b-instruct   # Open source, good quality
google/gemini-pro-1.5               # Google's best model
mistralai/mixtral-8x7b-instruct     # Fast and efficient
```

#### For Code Generation
```
anthropic/claude-3.5-sonnet         # Excellent for Odoo development
openai/gpt-4-turbo                  # Great code understanding
meta-llama/llama-3.1-70b-instruct   # Good for Python
```

### 4. Example Configuration
```
Name: KAI with OpenRouter
AI Provider: OpenRouter
API Key: sk-or-v1-xxxxxxxxxxxxx
API Base URL: https://openrouter.ai/api/v1
Model Name: anthropic/claude-3.5-haiku
Max Tokens: 1000
Temperature: 0.7
```

## Model Selection Tips

### By Use Case
- **Customer Support**: `anthropic/claude-3.5-haiku` (fast responses)
- **Complex Analysis**: `anthropic/claude-3.5-sonnet` (deep understanding)
- **Budget Operations**: `openai/gpt-4o-mini` (low cost)
- **Code Generation**: `anthropic/claude-3.5-sonnet` (best for Odoo)

### By Speed
- **Fastest**: `anthropic/claude-3.5-haiku`, `openai/gpt-4o-mini`
- **Balanced**: `anthropic/claude-3.5-sonnet`, `meta-llama/llama-3.1-70b-instruct`
- **Most Capable**: `anthropic/claude-3.5-sonnet`, `openai/gpt-4-turbo`

### By Cost
- **Most Economical**: `openai/gpt-4o-mini`, `meta-llama/llama-3.1-8b-instruct`
- **Balanced**: `anthropic/claude-3.5-haiku`, `google/gemini-pro-1.5`
- **Premium**: `anthropic/claude-3.5-sonnet`, `openai/gpt-4-turbo`

## Advanced Features

### Custom Headers
The integration automatically sends:
- **HTTP-Referer**: Your Odoo instance URL
- **X-Title**: "Odoo AI Assistant"

These help with OpenRouter's ranking system.

### Error Handling
If a model is unavailable or returns an error, the system will:
1. Log the error
2. Return a user-friendly Turkish message
3. Keep interaction logs for debugging

## Pricing
OpenRouter pricing varies by model. Check current prices at:
[https://openrouter.ai/models](https://openrouter.ai/models)

## Troubleshooting

### API Key Issues
```
Error: OpenRouter API key not configured
Solution: Add your API key in assistant settings
```

### Model Not Found
```
Error: Model not available
Solution: Check model name spelling and availability at openrouter.ai
```

### Rate Limits
```
Error: Rate limit exceeded
Solution: 
- Increase rate limits in OpenRouter dashboard
- Use a different model
- Implement user-level rate limiting
```

## Technical Details

### Implementation
The OpenRouter service (`ak_ai.service.openrouter`) uses the OpenAI-compatible API format, making it easy to integrate without requiring a separate SDK.

### Security
- API keys are stored encrypted (Odoo system group only)
- All security rules from base AI service apply
- User permissions are always respected
- No sudo() or privilege escalation

### Dependencies
```python
# Required
pip install openai  # OpenRouter uses OpenAI-compatible API
```

## Support
For OpenRouter-specific issues:
- OpenRouter Docs: [https://openrouter.ai/docs](https://openrouter.ai/docs)
- OpenRouter Discord: [Community](https://discord.gg/openrouter)

For module issues:
- Check logs: Odoo → Settings → Technical → Logging
- Review interaction logs: Settings → AI Assistant → Interaction Logs
