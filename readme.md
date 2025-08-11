# Azure OpenAI MCP Server for ChatGPT Deep Research

This is a Model Context Protocol (MCP) server designed to work with ChatGPT's Deep Research feature using Azure OpenAI. It provides semantic search through Azure OpenAI's Vector Store API and document retrieval capabilities, demonstrating how to build custom MCP servers that can extend ChatGPT with company-specific knowledge and tools using Azure's enterprise-grade AI services.

## Features

- **Enhanced Search Tool**: Semantic search using Azure OpenAI Assistants API with file_search tool
- **Intelligent Fetch Tool**: Complete document content extraction using Azure OpenAI Assistants API
- **SSE Transport**: Server-Sent Events transport for real-time communication with ChatGPT
- **Azure Integration**: Full Azure OpenAI integration with enterprise security and compliance
- **Hybrid Search**: Azure's enhanced search with vector similarity and keyword matching
- **Automatic Citations**: Built-in citation support with source file references
- **MCP Compliance**: Follows OpenAI's MCP specification for deep research integration

## Requirements

- Python 3.8+
- fastmcp (>=2.9.0)
- uvicorn (>=0.34.3)
- openai (Python SDK - works with Azure OpenAI)
- pydantic (dependency of fastmcp)
- Azure OpenAI Service with vector store capabilities

## Installation

### 1. Install Dependencies

```bash
pip install fastmcp uvicorn openai
```

### 2. Azure OpenAI Setup

Set up your Azure OpenAI environment variables:

```bash
export AZURE_OPENAI_API_KEY="your-azure-openai-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com"
export AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment-name"
export VECTOR_STORE_ID="vs_your_vector_store_id"
export AZURE_OPENAI_API_VERSION="2024-05-01-preview"  # Optional, defaults to this
```

### 3. Get Your Azure Configuration

**API Key**: Found in Azure Portal → Your OpenAI Resource → Keys and Endpoint

**Endpoint**: Found in Azure Portal → Your OpenAI Resource → Keys and Endpoint (format: `https://your-resource.openai.azure.com`)

**Deployment Name**: The name you gave your GPT-4 deployment in Azure OpenAI Studio

**Vector Store ID**: Create a vector store in Azure OpenAI Playground and note the ID (format: `vs_xxxxxxxxx`)

### 4. Run the Server

```bash
python main.py
```

The server will start on `http://0.0.0.0:8000` with SSE transport enabled.

### 5. Validate Setup

Run the validation script to test your configuration:

```bash
python validate.py  # or whatever you named the validation file
```

## Usage

### Connecting to ChatGPT Deep Research

1. **Access ChatGPT Settings**: Go to ChatGPT settings
2. **Navigate to Connectors**: Click on the "Connectors" tab  
3. **Add MCP Server**: Add your server URL: `http://your-domain:8000/sse/`
4. **Test Connection**: The server should appear as available for deep research

### Server Endpoints

- **SSE Endpoint**: `http://0.0.0.0:8000/sse/` - Main MCP communication endpoint
- **Health Check**: Server logs will show successful startup and tool registration

## Available Tools

### Search Tool

- **Purpose**: Find relevant documents using Azure OpenAI Assistants API with enhanced file_search
- **Input**: Search query string (natural language works best)
- **Output**: List of matching documents with citations, file IDs, titles, and text snippets
- **Features**: 
  - Hybrid search combining vector similarity and keyword matching
  - Automatic query optimization and result reranking
  - Built-in citation support with source file references
  - Context-aware search with up to 20 relevant chunks

### Fetch Tool

- **Purpose**: Extract complete document content using Azure OpenAI Assistants API
- **Input**: File ID from vector store search results (file-xxx format)
- **Output**: Full document content extracted via AI-powered content extraction
- **Features**:
  - Works around Azure OpenAI file download restrictions
  - AI-powered content extraction for complete document text
  - Automatic cleanup of temporary assistants and threads
  - Structured content extraction with headers, sections, and formatting

## Vector Store Integration

The server integrates with your Azure OpenAI vector store containing your uploaded documents. Azure OpenAI provides enhanced capabilities over standard OpenAI:

- **Enhanced Chunking**: 800 tokens per chunk with 400-token overlap
- **Hybrid Search**: Combines semantic similarity with keyword matching
- **Query Optimization**: Automatic query rewriting for better results
- **Result Reranking**: Intelligent selection of most relevant content
- **Enterprise Security**: Azure's enterprise-grade security and compliance

### Supported File Types

Azure OpenAI vector stores support:
- PDF documents
- Text files
- Word documents (.docx)
- Markdown files
- And other text-based formats

## Customization

### Using Your Own Vector Store

1. **Create Vector Store**: In Azure OpenAI Playground, create a new vector store
2. **Upload Documents**: Add your documents to the vector store via the playground
3. **Update Configuration**: Set `VECTOR_STORE_ID` to your new vector store ID
4. **Restart Server**: The server loads configuration at startup

### Modifying Search Behavior

The search function in `main.py` can be customized for:

- Different assistant instructions for specialized search behavior
- Custom result processing and formatting
- Additional metadata extraction from search results
- Custom content snippet length and formatting
- Multiple vector store support

### Environment Configuration

Create a `.env` file for easier configuration management:

```bash
# .env file
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
VECTOR_STORE_ID=vs_your_vector_store_id
AZURE_OPENAI_API_VERSION=2024-05-01-preview
```

## Deployment

### Local Development

The server runs locally on port 8000 and is accessible for testing with ChatGPT.

### Production Deployment

For production use:

- **Use HTTPS**: Ensure your server has SSL/TLS certificates
- **Authentication**: Consider adding OAuth or API key authentication
- **Rate Limiting**: Implement rate limiting for Azure OpenAI API calls
- **Monitoring**: Add logging and monitoring for server health
- **Scaling**: Consider load balancing for high-traffic scenarios
- **Azure Integration**: Use Azure App Service or Container Instances for hosting

### Tunneling for Local Testing

If running locally and need external access:

```bash
# Using ngrok
ngrok http 8000

# Using cloudflare tunnel  
cloudflared tunnel --url http://localhost:8000
```

## Architecture

This Azure OpenAI MCP server uses:

- **FastMCP**: Simplified MCP protocol implementation
- **Uvicorn**: ASGI server for HTTP/SSE transport
- **Azure OpenAI**: Enterprise-grade AI services with enhanced capabilities
- **Assistants API**: Azure OpenAI's advanced assistant framework for search and content extraction
- **Vector Store API**: Azure's semantic search with hybrid capabilities

### Key Differences from Standard OpenAI

- **Authentication**: Uses Azure API keys and endpoint-based authentication
- **Enhanced Search**: Hybrid search combining vector and keyword matching
- **Content Extraction**: AI-powered content extraction instead of direct file downloads
- **Enterprise Features**: Built-in compliance, security, and monitoring capabilities

## Troubleshooting

### Common Issues

- **Server won't start**: Check if port 8000 is already in use
- **ChatGPT can't connect**: Ensure the server URL is correct and accessible
- **No search results**: Verify Azure OpenAI configuration and vector store ID
- **Authentication errors**: Check API key and endpoint configuration
- **Vector store errors**: Verify the vector store exists and contains documents
- **Deployment not found**: Ensure your deployment name is correct and deployed

### Debugging Steps

1. **Run Validation**: Use the validation script to check configuration
2. **Check Logs**: Server logs show detailed error messages
3. **Test SSE Endpoint**: `curl http://localhost:8000/sse/`
4. **Verify Azure Connection**: 
   ```python
   from openai import AzureOpenAI
   client = AzureOpenAI(api_key="...", azure_endpoint="...", api_version="...")
   print(client.models.list())
   ```
5. **Check Vector Store**: Verify in Azure OpenAI Playground that your vector store contains files

### Azure-Specific Issues

- **API Version Errors**: Ensure you're using `2024-05-01-preview` or later
- **Deployment Errors**: Verify your deployment name matches exactly what's in Azure OpenAI Studio
- **Vector Store Access**: Ensure your API key has access to the vector store
- **File Upload Issues**: Use Azure OpenAI Playground to upload and verify files

## Performance Considerations

- **Search Latency**: Azure OpenAI Assistants API calls take longer than direct vector search
- **Rate Limits**: Be aware of Azure OpenAI rate limits for your deployment
- **Cost Optimization**: Monitor token usage, especially for large document extractions
- **Caching**: Consider implementing response caching for frequently accessed documents

## Security Best Practices

- **API Key Management**: Store API keys securely, use Azure Key Vault in production
- **Network Security**: Use HTTPS and consider VPN or private endpoints
- **Access Control**: Implement authentication for your MCP server
- **Audit Logging**: Enable Azure OpenAI logging for compliance and monitoring
- **Data Privacy**: Ensure uploaded documents comply with your data governance policies

## Contributing

This is a production-ready implementation that can be extended with:

- Multi-vector store support for different document categories
- Advanced search filtering and faceted search
- Integration with Azure Active Directory for authentication  
- Monitoring and alerting with Azure Application Insights
- Horizontal scaling with Azure Container Apps or AKS

## License

This implementation is provided for educational and commercial use. Ensure compliance with Azure OpenAI service terms and your organization's data policies.