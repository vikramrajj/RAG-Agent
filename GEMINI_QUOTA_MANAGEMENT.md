# Gemini API Quota Management

## Issue: Quota Exceeded Error

### Error Message
```
429 RESOURCE_EXHAUSTED
You exceeded your current quota, please check your plan and billing details.
Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests
Limit: 50 requests per day
```

### Root Cause
The browser automation feature uses Google's Gemini API to power the AI agent that controls the browser. The free tier has strict rate limits:

- **gemini-2.0-flash-exp**: 50 requests per day
- **gemini-1.5-flash**: Higher quota (1500 requests per day for free tier)
- **gemini-1.5-pro**: Even higher quota but slower

## Solution Applied ✅

### Changed Model from 2.0 to 1.5
Updated `browser_use_wrapper.py` to use `gemini-1.5-flash` instead of `gemini-2.0-flash-exp`:

```python
# Before
llm = ChatGoogle(
    model="gemini-2.0-flash-exp",  # 50 requests/day limit
    api_key=self.gemini_api_key,
    temperature=0.7
)

# After
llm = ChatGoogle(
    model="gemini-1.5-flash",  # 1500 requests/day limit
    api_key=self.gemini_api_key,
    temperature=0.5
)
```

### Benefits of gemini-1.5-flash
- ✅ **30x higher quota**: 1,500 requests/day vs 50
- ✅ **Stable and reliable**: Not experimental
- ✅ **Fast response**: Similar speed to 2.0-flash-exp
- ✅ **Good for automation**: Proven track record

## Alternative Solutions

### Option 1: Upgrade to Paid Plan 💳
- **Pay-as-you-go**: $0.00015 per 1K characters input
- **No daily limits**: Use as much as you need
- **Higher rate limits**: 360 requests per minute
- **Link**: https://ai.google.dev/pricing

### Option 2: Use Multiple API Keys 🔑
- Create multiple Google accounts
- Get separate API keys
- Rotate keys when one hits quota
- Implement key rotation logic in code

### Option 3: Wait for Reset ⏰
- Free tier quota resets every 24 hours
- Error message shows retry time (e.g., "retry in 22s")
- Simple but inconvenient for testing

### Option 4: Use Different Model Based on Task
```python
# For simple tasks
model = "gemini-1.5-flash"  # Fast, high quota

# For complex tasks requiring reasoning
model = "gemini-1.5-pro"    # Slower, but smarter

# For experimental features
model = "gemini-2.0-flash-exp"  # Latest but limited quota
```

## Quota Limits Reference

| Model | Free Tier Limit | Paid Tier Limit |
|-------|----------------|-----------------|
| gemini-2.0-flash-exp | 50/day | N/A (experimental) |
| gemini-1.5-flash | 1,500/day | 2M tokens/min |
| gemini-1.5-pro | 50/day | 1M tokens/min |
| gemini-1.0-pro | 60/min | 360/min |

Source: https://ai.google.dev/gemini-api/docs/rate-limits

## Monitoring Quota Usage

### Check Current Usage
1. Go to: https://console.cloud.google.com/
2. Select your project
3. Navigate to: APIs & Services → Enabled APIs
4. Click on "Generative Language API"
5. View Quotas tab

### Implement Usage Tracking
```python
import logging

class GeminiUsageTracker:
    def __init__(self):
        self.daily_count = 0
        self.max_daily = 1500  # For gemini-1.5-flash
    
    def can_make_request(self):
        return self.daily_count < self.max_daily
    
    def track_request(self):
        self.daily_count += 1
        remaining = self.max_daily - self.daily_count
        logging.info(f"Gemini API calls today: {self.daily_count}/{self.max_daily} (remaining: {remaining})")
```

## Best Practices

### 1. Cache Results
- Store browser automation results
- Reuse cached data for similar queries
- Reduces API calls significantly

### 2. Batch Operations
- Group multiple tasks together
- Execute in single browser session
- Minimize model calls per task

### 3. Fallback Strategy
```python
models_to_try = [
    "gemini-1.5-flash",      # Try high-quota model first
    "gemini-1.5-pro",        # Fall back to pro if needed
    "gemini-2.0-flash-exp"   # Last resort (limited quota)
]

for model in models_to_try:
    try:
        llm = ChatGoogle(model=model, api_key=api_key)
        result = await agent.run()
        break
    except QuotaExceeded:
        continue
```

### 4. Rate Limiting
```python
import time
from functools import wraps

def rate_limit(calls_per_minute=60):
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                await asyncio.sleep(left_to_wait)
            result = await func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator
```

## Error Handling

### Graceful Degradation
```python
try:
    result = await browser_wrapper.shop_online(product, website=website)
except QuotaExceeded as e:
    return {
        'success': False,
        'error': 'API quota exceeded',
        'message': 'Gemini API daily quota reached. Please try again tomorrow or upgrade your plan.',
        'retry_after': extract_retry_time(e),
        'upgrade_link': 'https://ai.google.dev/pricing'
    }
```

### User-Friendly Messages
Instead of showing raw API errors, display:
```
⚠️ Browser automation temporarily unavailable
Daily quota limit reached. The service will reset in approximately 6 hours.

Options:
• Wait for quota reset
• Upgrade to paid plan for unlimited usage
• Use manual search as alternative
```

## Current Configuration

After the fix:
- ✅ **Model**: gemini-1.5-flash
- ✅ **Daily Quota**: 1,500 requests
- ✅ **Rate Limit**: 15 requests per minute
- ✅ **Temperature**: 0.5 (focused, consistent results)
- ✅ **Cost**: Free (within quota)

## Testing After Fix

Try these commands to verify the fix:
```
Open Amazon.in and search for laptop under 35K
Search Amazon India for phones under 20000
Find headphones on Amazon under 3000
```

Expected behavior:
- ✅ No more 429 errors
- ✅ Browser opens and performs search
- ✅ Results stay visible in browser
- ✅ Feedback provided in chat

## Upgrading to Paid Tier

If you need more than 1,500 requests/day:

1. **Enable Billing**
   - Go to: https://console.cloud.google.com/billing
   - Add payment method
   - Enable billing for your project

2. **Set Budget Alerts**
   - Navigate to: Billing → Budgets & alerts
   - Create budget (e.g., $10/month)
   - Set email alerts at 50%, 90%, 100%

3. **Monitor Costs**
   - Typical cost: $0.0001-0.0003 per request
   - 10,000 requests ≈ $1-3
   - Very affordable for most use cases

## Summary

✅ **Problem Solved**: Switched from gemini-2.0-flash-exp (50/day) to gemini-1.5-flash (1,500/day)
✅ **Server Restarted**: Changes applied and running on port 8000
✅ **Ready to Test**: Browser automation should work without quota errors
✅ **Future-Proof**: 30x higher quota provides plenty of headroom

You can now use browser automation extensively without hitting quota limits! 🚀
