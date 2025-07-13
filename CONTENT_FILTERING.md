# Content Filtering Feature

## Overview

The CivicAI system now includes intelligent content filtering to help users distinguish between official policy documents and news articles in search results.

## Features

### 🔍 **Smart Content Classification**
- **Automatic Detection**: AI-powered classification of content as "policy", "news", or "mixed"
- **URL Analysis**: Domain-based classification for high accuracy
- **Content Analysis**: Keyword analysis of titles and content
- **Visual Indicators**: Clear badges and icons for content types

### 🎛️ **Filtering Options**

| Filter | Description | Use Case |
|--------|-------------|----------|
| **📄 All Content** | Shows both policies and news | Comprehensive research |
| **📋 Policies Only** | Official documents, bills, regulations | Legislative research |
| **📰 News Only** | News articles, coverage, analysis | Current events tracking |

### 🏷️ **Content Type Indicators**

- **📋 Policy**: Official government documents, bills, regulations, ordinances
- **📰 News**: News articles, breaking news, coverage, analysis  
- **📊 Mixed**: Content with characteristics of both types

## How It Works

### Backend Classification

The system uses multiple signals to classify content:

1. **URL Domain Analysis** (Highest Priority)
   - Government domains (.gov, congress.gov, etc.) → Policy
   - News domains (cnn.com, npr.org, etc.) → News

2. **Title/Content Keywords**
   - Policy indicators: "bill", "act", "regulation", "ordinance", "law"
   - News indicators: "breaking", "announced", "investigation", "latest"

3. **Weighted Scoring**
   - Title matches weighted 2x higher than content matches
   - Confidence-based classification

### Frontend Features

- **Filter Dropdown**: Easy selection of content type
- **Visual Badges**: Color-coded content type indicators
- **Real-time Filtering**: Applied during search execution
- **Smart Defaults**: "All Content" selected by default

## API Usage

### Search with Filtering

```bash
POST /policies/search/stream
{
  "prompt": "housing policy San Francisco",
  "max_results": 10,
  "content_filter": "policies"  // "policies", "news", or "both"
}
```

### Response Format

```json
{
  "type": "result",
  "priority_policies": [
    {
      "id": "policy_123",
      "title": "San Francisco Housing Policy Update",
      "content_type": "policy",  // Added field
      "government_level": "local",
      "domain": "housing",
      // ... other fields
    }
  ]
}
```

## User Interface

### Search Interface

```tsx
// Filter Selection
<Select value={contentFilter} onValueChange={setContentFilter}>
  <SelectItem value="both">📄 All Content</SelectItem>
  <SelectItem value="policies">📋 Policies Only</SelectItem>
  <SelectItem value="news">📰 News Only</SelectItem>
</Select>

// Content Type Badge
<Badge className={getContentTypeColor(policy.content_type)}>
  <span>{getContentTypeIcon(policy.content_type)}</span>
  {policy.content_type}
</Badge>
```

### Color Scheme

- **Policy**: `bg-emerald-100 text-emerald-800` (Green)
- **News**: `bg-orange-100 text-orange-800` (Orange)  
- **Mixed**: `bg-indigo-100 text-indigo-800` (Indigo)

## Testing

### Manual Testing

```bash
# Test all filters
python3 test_content_filtering.py

# Test specific filter
curl -X POST "http://localhost:8000/policies/search/stream" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "housing policy", "content_filter": "policies"}'
```

### Expected Behavior

1. **Policies Filter**: Should return primarily .gov sources, bills, regulations
2. **News Filter**: Should return news articles, coverage, analysis
3. **Both Filter**: Should return mixed results with content type labels

## Benefits

### For Users
- **Focused Research**: Find exactly what you're looking for
- **Clear Distinction**: Understand source types at a glance
- **Comprehensive Options**: Choose broad or narrow search scope

### For Developers
- **Extensible**: Easy to add new content types
- **Configurable**: Adjustable classification rules
- **Maintainable**: Clear separation of classification logic

## Future Enhancements

### Planned Features
- **Source Credibility**: Trust indicators for sources
- **Date Filtering**: Filter by publication/effective dates
- **Jurisdiction Filtering**: Filter by specific government levels
- **Custom Filters**: User-defined content categories

### Technical Improvements
- **ML Classification**: Machine learning-based content classification
- **Real-time Updates**: Live classification as content changes
- **Performance Optimization**: Caching of classification results

## Configuration

### Customizing Classification

Edit `api/main.py` to modify classification rules:

```python
def classify_content_type(title: str, url: str, content: str = "") -> str:
    # Add custom policy indicators
    policy_indicators = [
        "your_custom_keyword",
        # ... existing keywords
    ]
    
    # Add custom news domains
    news_domains = [
        "your_news_domain.com",
        # ... existing domains
    ]
```

### Frontend Customization

Modify `PolicyList.tsx` to customize UI:

```tsx
// Add new filter options
<SelectItem value="custom">
  <span>🔧</span>
  <span>Custom Content</span>
</SelectItem>

// Customize colors and icons
const getContentTypeColor = (contentType: string) => {
  switch (contentType) {
    case 'custom': return 'bg-purple-100 text-purple-800';
    // ... existing cases
  }
};
```

## Troubleshooting

### Common Issues

1. **No Results with Filter**: Content may be misclassified
   - Solution: Use "All Content" to see full results
   - Check classification rules in backend

2. **Wrong Content Type**: Classification may need tuning
   - Solution: Review and adjust keyword lists
   - Consider domain-specific rules

3. **Performance Issues**: Too many classification calls
   - Solution: Add caching layer
   - Optimize classification logic

### Debug Tools

```bash
# Test classification directly
python3 -c "
from api.main import classify_content_type
result = classify_content_type('Title', 'https://example.com', 'content')
print(f'Classification: {result}')
"
```

## Contributing

To improve content filtering:

1. **Add Keywords**: Update policy/news indicator lists
2. **Add Domains**: Include new trusted/news domains
3. **Improve Logic**: Enhance classification algorithm
4. **Test Changes**: Use provided test scripts
5. **Update Documentation**: Keep this guide current

---

*This feature enhances the CivicAI system's ability to provide targeted, relevant search results for policy research and civic engagement.*