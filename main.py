#!/usr/bin/env python3
"""
Sample MCP Server for ChatGPT Deep Research Integration with Azure OpenAI

This server implements the Model Context Protocol (MCP) with search and fetch
capabilities designed to work with ChatGPT's deep research feature using Azure OpenAI.
"""

import logging
import os
from typing import Dict, List, Any

from fastmcp import FastMCP
from openai import AzureOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure OpenAI configuration
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION",
                                          "2024-05-01-preview")
AZURE_OPENAI_DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID", "")

# Initialize Azure OpenAI client
azure_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
) if AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT else None

server_instructions = """
This MCP server provides search and document retrieval capabilities 
for deep research using Azure OpenAI. Use the search tool to find relevant documents 
based on keywords, then use the fetch tool to retrieve complete 
document content with citations.
"""


def create_server():
    """Create and configure the MCP server with search and fetch tools."""

    # Initialize the FastMCP server
    mcp = FastMCP(name="Azure OpenAI Deep Research MCP Server",
                  instructions=server_instructions)

    @mcp.tool()
    async def search(query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for documents using Azure OpenAI Vector Store through Assistants API.

        This tool searches through the vector store to find semantically relevant matches
        using Azure OpenAI's enhanced file search capabilities with hybrid search,
        query optimization, and result reranking.

        Args:
            query: Search query string. Natural language queries work best for semantic search.

        Returns:
            Dictionary with 'results' key containing list of matching documents.
            Each result includes id, title, text snippet, and optional URL.
        """
        if not query or not query.strip():
            return {"results": []}

        if not azure_client:
            logger.error(
                "Azure OpenAI client not initialized - check API key and endpoint"
            )
            raise ValueError(
                "Azure OpenAI API key and endpoint are required for vector store search"
            )

        if not AZURE_OPENAI_DEPLOYMENT_NAME:
            logger.error("Azure OpenAI deployment name not configured")
            raise ValueError(
                "AZURE_OPENAI_DEPLOYMENT_NAME environment variable is required"
            )

        # Search using Azure OpenAI Assistants API with file_search tool
        logger.info(
            f"Searching Azure OpenAI vector store {VECTOR_STORE_ID} for query: '{query}'"
        )

        try:
            # Create a temporary assistant for search
            assistant = azure_client.beta.assistants.create(
                name="MCP Search Assistant",
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                tools=[{
                    "type": "file_search"
                }],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [VECTOR_STORE_ID]
                    }
                })

            # Create thread with the search query
            thread = azure_client.beta.threads.create(
                messages=[{
                    "role":
                    "user",
                    "content":
                    f"Search for information about: {query}. Please provide specific details and cite sources."
                }],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [VECTOR_STORE_ID]
                    }
                })

            # Run the search
            run = azure_client.beta.threads.runs.create_and_poll(
                thread_id=thread.id, assistant_id=assistant.id)

            # Get the assistant's response with citations
            messages = azure_client.beta.threads.messages.list(
                thread_id=thread.id)

            results = []

            if messages.data:
                assistant_message = messages.data[
                    0]  # Latest message from assistant

                # Extract text content and citations
                if hasattr(assistant_message,
                           'content') and assistant_message.content:
                    for content_item in assistant_message.content:
                        if hasattr(content_item, 'text'):
                            text_content = content_item.text.value

                            # Extract citations if available
                            citations = []
                            if hasattr(content_item.text, 'annotations'):
                                for annotation in content_item.text.annotations:
                                    if hasattr(annotation, 'file_citation'):
                                        citation = annotation.file_citation
                                        citations.append({
                                            "file_id":
                                            citation.file_id,
                                            "quote":
                                            getattr(citation, 'quote', '')
                                        })

                            # Create result entries for each citation or main content
                            if citations:
                                for i, citation in enumerate(citations):
                                    # Get file info for better title
                                    try:
                                        file_info = azure_client.files.retrieve(
                                            citation["file_id"])
                                        title = getattr(
                                            file_info, 'filename',
                                            f"Document {i+1}")
                                    except:
                                        title = f"Document {i+1}"

                                    snippet = citation[
                                        "quote"][:200] + "..." if len(
                                            citation["quote"]
                                        ) > 200 else citation["quote"]

                                    results.append({
                                        "id":
                                        citation["file_id"],
                                        "title":
                                        title,
                                        "text":
                                        snippet,
                                        "url":
                                        f"https://{AZURE_OPENAI_ENDPOINT.split('//')[1]}/openai/files/{citation['file_id']}"
                                    })
                            else:
                                # No specific citations, use general response
                                snippet = text_content[:200] + "..." if len(
                                    text_content) > 200 else text_content
                                results.append({
                                    "id":
                                    "search_result_1",
                                    "title":
                                    "Search Results",
                                    "text":
                                    snippet,
                                    "url":
                                    f"https://{AZURE_OPENAI_ENDPOINT.split('//')[1]}/openai/vector_stores/{VECTOR_STORE_ID}"
                                })

            # Cleanup - delete temporary assistant
            try:
                azure_client.beta.assistants.delete(assistant.id)
                azure_client.beta.threads.delete(thread.id)
            except:
                pass  # Continue even if cleanup fails

            logger.info(f"Azure OpenAI search returned {len(results)} results")
            return {"results": results}

        except Exception as e:
            logger.error(f"Azure OpenAI search failed: {e}")
            raise ValueError(f"Search operation failed: {str(e)}")

    @mcp.tool()
    async def fetch(id: str) -> Dict[str, Any]:
        """
        Retrieve complete document content by ID using Azure OpenAI Assistants API.

        Since Azure OpenAI doesn't allow direct download of assistant files,
        this tool uses the Assistants API to extract and return the full content
        of a specific document from the vector store.

        Args:
            id: File ID from vector store (file-xxx) or local document ID

        Returns:
            Complete document with id, title, full text content, 
            optional URL, and metadata

        Raises:
            ValueError: If the specified ID is not found
        """
        if not id:
            raise ValueError("Document ID is required")

        if not azure_client:
            logger.error(
                "Azure OpenAI client not initialized - check API key and endpoint"
            )
            raise ValueError(
                "Azure OpenAI API key and endpoint are required for vector store file retrieval"
            )

        if not AZURE_OPENAI_DEPLOYMENT_NAME:
            logger.error("Azure OpenAI deployment name not configured")
            raise ValueError(
                "AZURE_OPENAI_DEPLOYMENT_NAME environment variable is required"
            )

        logger.info(
            f"Fetching content from Azure OpenAI vector store for file ID: {id}"
        )

        try:
            # First, get file metadata to get the filename
            try:
                file_info = azure_client.files.retrieve(id)
                filename = getattr(file_info, 'filename', f"Document {id}")
            except Exception as e:
                logger.warning(
                    f"Could not retrieve file metadata for {id}: {e}")
                filename = f"Document {id}"

            # Create a temporary assistant for content extraction
            assistant = azure_client.beta.assistants.create(
                name="MCP Content Extractor",
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                tools=[{
                    "type": "file_search"
                }],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [VECTOR_STORE_ID]
                    }
                },
                instructions=
                """You are a document content extractor. When asked to retrieve the full content of a specific file, 
                you should return the complete text content of that file in a structured format. 
                Extract all text content including headers, paragraphs, lists, and any other textual information.
                Do not summarize - provide the full content.""")

            # Create thread asking for full document content
            thread = azure_client.beta.threads.create(
                messages=[{
                    "role":
                    "user",
                    "content":
                    f"""Please extract and return the complete full text content from the file with ID: {id} 
                    (filename: {filename}). I need the entire document content, not a summary. 
                    Return all text including headers, sections, paragraphs, lists, tables, and any other content.
                    Structure the output clearly but include everything from the document."""
                }],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [VECTOR_STORE_ID]
                    }
                })

            # Run the content extraction
            run = azure_client.beta.threads.runs.create_and_poll(
                thread_id=thread.id, assistant_id=assistant.id)

            # Get the assistant's response with full content
            messages = azure_client.beta.threads.messages.list(
                thread_id=thread.id)

            file_content = "No content available"

            if messages.data:
                assistant_message = messages.data[
                    0]  # Latest message from assistant

                # Extract text content
                if hasattr(assistant_message,
                           'content') and assistant_message.content:
                    content_parts = []
                    for content_item in assistant_message.content:
                        if hasattr(content_item, 'text'):
                            content_parts.append(content_item.text.value)

                    if content_parts:
                        file_content = "\n".join(content_parts)

            # Cleanup - delete temporary assistant and thread
            try:
                azure_client.beta.assistants.delete(assistant.id)
                azure_client.beta.threads.delete(thread.id)
            except Exception as cleanup_error:
                logger.warning(f"Cleanup failed: {cleanup_error}")

            result = {
                "id": id,
                "title": filename,
                "text": file_content,
                "url":
                f"https://{AZURE_OPENAI_ENDPOINT.split('//')[1]}/openai/files/{id}",
                "metadata": {
                    "extraction_method":
                    "assistants_api",
                    "note":
                    "Content extracted via Azure OpenAI Assistants API due to file access restrictions"
                }
            }

            logger.info(
                f"Successfully extracted content from Azure OpenAI file: {id}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch file {id}: {e}")
            raise ValueError(f"File content extraction failed: {str(e)}")

    return mcp


def main():
    """Main function to start the MCP server."""
    # Verify Azure OpenAI client is initialized
    if not azure_client:
        logger.error(
            "Azure OpenAI configuration incomplete. Please set AZURE_OPENAI_API_KEY, "
            "AZURE_OPENAI_ENDPOINT, and optionally AZURE_OPENAI_API_VERSION environment variables."
        )
        raise ValueError("Azure OpenAI configuration is required")

    if not AZURE_OPENAI_DEPLOYMENT_NAME:
        logger.error(
            "Azure OpenAI deployment name not configured. Please set AZURE_OPENAI_DEPLOYMENT_NAME environment variable."
        )
        raise ValueError("Azure OpenAI deployment name is required")

    logger.info(f"Using Azure OpenAI endpoint: {AZURE_OPENAI_ENDPOINT}")
    logger.info(f"Using deployment: {AZURE_OPENAI_DEPLOYMENT_NAME}")
    logger.info(f"Using vector store: {VECTOR_STORE_ID}")

    # Create the MCP server
    server = create_server()

    # Configure and start the server
    logger.info("Starting Azure OpenAI MCP server on 0.0.0.0:8000")
    logger.info("Server will be accessible via SSE transport")

    try:
        # Use FastMCP's built-in run method with SSE transport
        server.run(transport="sse", host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
