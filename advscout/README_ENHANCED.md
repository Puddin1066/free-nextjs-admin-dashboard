# ADVScout Enhanced - Multi-Provider AI Venture Scout Platform

**Version 2.0 with OpenRouter Integration & Tiered Pricing**

ADVScout Enhanced is a next-generation venture scouting platform that combines multiple AI providers with tiered pricing to deliver cost-effective, professional-grade company intelligence for contractors and consulting firms.

## 🚀 What's New in Version 2.0

### ✅ **Multi-Provider AI Integration**
- **OpenRouter Support**: Access to GPT-4o-mini, Claude-3-Haiku, Llama-3-70b, Gemini-Pro
- **Cost Optimization**: Automatic model selection based on task and budget
- **Failover Protection**: Automatic fallback between providers
- **Cost Tracking**: Real-time cost monitoring and budget controls

### ✅ **Tiered Pricing Structure**
- **Free Tier**: $25/month - Perfect for demos and small analyses
- **Professional Tier**: $225/month - Full business intelligence
- **Enterprise Tier**: $750/month - Complete platform with custom features

### ✅ **Contractor Economics**
- **High Profit Margins**: 46-89% depending on tier
- **Scalable Business Model**: Grow from free demos to enterprise clients
- **Cost Transparency**: Clear breakdown of all expenses and profits

## 💰 Pricing & Profitability

| Tier | Monthly Cost | Client Fee | Contractor Profit | Margin | Companies/Month |
|------|-------------|------------|-------------------|---------|-----------------|
| **Free** | $25 | $225 | $200 | 89% | 50 |
| **Professional** | $233 | $450 | $217 | 48% | 200 |
| **Enterprise** | $652 | $1,200 | $548 | 46% | 500 |

## 🔧 Quick Start

### 1. **Installation**
```bash
git clone [repository]
cd advscout
pip install -r requirements.txt
```

### 2. **Environment Setup**
```bash
# Required for all tiers
export OPENROUTER_API_KEY="sk-or-your-key-here"
export GITHUB_TOKEN="ghp_your-token-here"
export NEWSAPI_KEY="your-news-api-key"

# Optional (Premium tiers)
export LINKEDIN_EMAIL="your-email@domain.com"
export LINKEDIN_PASSWORD="your-password"
export CRUNCHBASE_API_KEY="your-crunchbase-key"
```

### 3. **Demo the Platform**
```bash
# Free tier demo
python scripts/quick_start_openrouter.py --tier free --client demo

# Professional tier demo
python scripts/quick_start_openrouter.py --tier professional --client advantary

# Compare all tiers
python scripts/quick_start_openrouter.py --compare-tiers
```

### 4. **Run Analysis**
```bash
# Free tier analysis (5 free APIs + OpenRouter AI)
python scripts/run_full_scout.py \
  --tier free \
  --client demo \
  --input companies.csv \
  --output results/

# Professional tier analysis (8 APIs + OpenRouter AI)
python scripts/run_full_scout.py \
  --tier professional \
  --client advantary \
  --input companies.csv \
  --output results/
```

## 🎯 Tier Comparison

### **Free Tier - Demo & Proof of Concept**
**Perfect for:** Initial client demos, small analyses, proving platform value

**APIs Included:**
- ✅ GitHub (Technical assessment)
- ✅ SEC EDGAR (Financial data)
- ✅ USPTO (Patent analysis)
- ✅ NewsAPI (Market sentiment)
- ✅ NIH Reporter (Research validation)
- ✅ OpenRouter AI (Cost-effective analysis)

**Features:**
- 85% complete intelligence profiles
- AI-powered insights and recommendations
- Decision maker identification
- Strategic recommendations
- Markdown and CSV reports

**Limitations:**
- 50 companies/month limit
- No real-time monitoring
- Standard support only

### **Professional Tier - Client-Committed Mode**
**Perfect for:** Established client relationships, regular intelligence needs

**Additional APIs:**
- ✅ LinkedIn Sales Navigator ($80/month)
- ✅ Crunchbase ($29/month) 
- ✅ Clearbit ($99/month)

**Enhanced Features:**
- 95% complete intelligence profiles
- Direct decision maker contacts
- Network pathway mapping
- Funding intelligence
- Contact enrichment
- Priority support

### **Enterprise Tier - Full Intelligence Mode**
**Perfect for:** Large clients, comprehensive intelligence operations

**Additional APIs:**
- ✅ BuiltWith ($295/month)
- ✅ Glassdoor ($99/month)
- ✅ Custom integrations available

**Advanced Features:**
- Real-time monitoring
- Technology stack analysis
- Cultural fit assessment
- Custom reporting
- API access
- Dedicated support

## 🤖 AI Provider Integration

### **Supported Models**
```yaml
OpenRouter Models:
  - openai/gpt-4o-mini: $0.00015/1K tokens (Most cost-effective)
  - anthropic/claude-3-haiku: $0.00025/1K tokens (Best inference)
  - meta-llama/llama-3-70b-instruct: $0.0004/1K tokens (Open source)
  - google/gemini-pro: $0.000125/1K tokens (Fastest)

OpenAI Direct:
  - gpt-4o-mini: $0.00015/1K tokens (Backup)
  - gpt-4: $0.03/1K tokens (Premium tier only)
```

### **Cost Optimization**
- **Automatic Model Selection**: Best model for each task type
- **Budget Controls**: Maximum cost per analysis ($0.50-1.00)
- **Real-time Monitoring**: Track costs as they accrue
- **Intelligent Failover**: Switch providers if one fails

## 📊 Sample Output

### **Company Intelligence Report**
```markdown
# Company Intelligence Report: TechCorp Inc

## Executive Summary
- Overall Score: 8.5/10
- Investment Opportunity: High
- Service Opportunity: Go-to-market advisory
- Engagement Priority: High

## AI-Generated Insights
Based on comprehensive analysis across 6 data sources, TechCorp demonstrates 
strong technical capabilities with active development (250+ commits/month) 
and positive market sentiment (0.85 sentiment score). Patent portfolio 
indicates significant IP development in AI/ML space.

## Decision Makers
- CEO: John Smith (ex-Google PM, Stanford MBA)
  - Communication Style: Data-driven, technical depth
  - Best Approach: Technical product demo + ROI analysis
  
- CTO: Jane Doe (ex-Microsoft Principal, MIT CS)
  - Technical Philosophy: Scalable architecture, open source
  - Engagement Strategy: Architecture discussion, technical advisory

## Strategic Recommendations
1. **Immediate**: Outreach for Series B go-to-market advisory
2. **Medium-term**: Monitor for acquisition opportunities
3. **Investment**: Consider Series B participation (Q2 2024)
```

## 📈 Business Model for Contractors

### **Revenue Streams**
1. **Monthly Platform Fees**: $225-1,200/month per client
2. **Setup Fees**: $500-2,000 per client onboarding
3. **Custom Analysis**: $50-200 per additional company
4. **Consulting Services**: $150-500/hour leveraging platform data

### **Scalability**
```
Year 1: 3 clients x $225/month = $8,100/year profit
Year 2: 8 clients x $450/month = $43,200/year profit  
Year 3: 15 clients x $600/month = $108,000/year profit
```

### **Client Onboarding Process**
1. **Week 1**: Free tier demo (10 companies, $0 risk)
2. **Week 2-4**: Professional tier trial (25 companies, prove ROI)
3. **Month 2+**: Full engagement with regular reporting

## 🔧 Advanced Configuration

### **Client-Specific Setup**
```bash
# Create client configuration
mkdir -p config/clients
cat > config/clients/advantary.yaml << EOF
client: advantary
business_model: [advisory_services, investment]
focus_sectors: [b2b_saas, fintech, healthcare]
geographic_focus: [north_america, europe]
portfolio_size: 15
investment_stage: [series_a, series_b]
EOF
```

### **Custom API Integration**
```python
# Add new API to pricing tier
# config/pricing_tiers.yaml
professional:
  apis:
    new_api:
      enabled: true
      cost: 50
      rate_limit: "1000/month"
      priority: 9
```

## 🚀 Deployment Options

### **Local Development**
```bash
python scripts/run_full_scout.py --tier free --input companies.csv
```

### **Docker Deployment**
```bash
docker build -t advscout:enhanced .
docker run -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY advscout:enhanced
```

### **Cloud Deployment**
- **AWS/Azure/GCP**: Container deployment with environment variables
- **Kubernetes**: Multi-client deployment with namespace isolation
- **Serverless**: Function-based deployment for cost optimization

## 📋 API Documentation

### **Tier Management**
```python
from config.config_updated import get_config, get_ai_config

# Get tier configuration
config = get_config("professional", "advantary")
ai_config = config.get_ai_config()
usage_limits = config.get_usage_limits()

# Validate usage
validation = config.validate_usage(
    companies_analyzed=150,
    api_calls_made=2000,
    ai_cost_incurred=45.50
)
```

### **AI Provider Usage**
```python
from core.ai_providers import ai_provider, TaskType

# Cost-optimized analysis
response = ai_provider.complete(
    prompt="Analyze this company...",
    task_type=TaskType.ENRICHMENT,
    max_cost=0.50
)

print(f"Model used: {response.model_used}")
print(f"Cost: ${response.cost_estimate:.3f}")
print(f"Analysis: {response.content}")
```

## 🔍 Troubleshooting

### **Common Issues**
1. **API Key Errors**: Ensure all required keys are set in environment
2. **Rate Limiting**: Check API usage limits for your tier
3. **Cost Overruns**: Monitor AI costs and adjust max_cost_per_analysis
4. **Model Failures**: Platform automatically falls back to available models

### **Support Channels**
- **Free Tier**: Documentation and community support
- **Professional**: Email support (24-48 hour response)
- **Enterprise**: Dedicated support manager

## 📄 License

MIT License - Commercial use permitted

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

---

**Ready to transform your venture intelligence operations?**

Start with the free tier demo and scale to enterprise as your client base grows. The platform pays for itself with just one client engagement.

```bash
python scripts/quick_start_openrouter.py --tier free --setup-env
```