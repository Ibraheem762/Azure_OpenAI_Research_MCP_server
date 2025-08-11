#!/usr/bin/env python3
"""
Validate Azure OpenAI MCP server functionality by testing the actual protocol methods
"""

import asyncio
import os
import main

async def validate_azure_mcp_server():
    """Complete validation of Azure OpenAI MCP server functionality"""

    print("Azure OpenAI MCP Server Validation")
    print("=" * 35)

    # Verify environment variables first
    print("0. Checking environment variables...")
    required_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT", 
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "VECTOR_STORE_ID"
    ]

    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"   ✗ Missing environment variables: {', '.join(missing_vars)}")
        print("   Please set the following:")
        for var in missing_vars:
            print(f"     export {var}=your_value")
        return False
    else:
        print("   ✓ All required environment variables are set")
        print(f"     Endpoint: {os.environ.get('AZURE_OPENAI_ENDPOINT')}")
        print(f"     Deployment: {os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME')}")
        print(f"     Vector Store: {os.environ.get('VECTOR_STORE_ID')}")

    server = main.create_server()

    # Test 1: List tools
    print("\n1. Testing list_tools...")
    try:
        tools = await server._list_tools()
        print(f"   Tools found: {len(tools)}")

        tool_data = []
        for tool in tools:
            data = {
                "name": tool.name,
                "description": tool.description,
                "has_schema": hasattr(tool, 'input_schema')
            }
            tool_data.append(data)
            print(f"   - {tool.name}: {tool.description[:50]}...")

        # Verify expected tools
        names = [t["name"] for t in tool_data]
        if "search" in names and "fetch" in names:
            print("   ✓ Both required tools present")
        else:
            print(f"   ✗ Missing tools. Found: {names}")

    except Exception as e:
        print(f"   ✗ List tools failed: {e}")
        return False

    # Test 2: Test Azure OpenAI client connectivity
    print("\n2. Testing Azure OpenAI client connectivity...")
    try:
        if main.azure_client:
            # Test basic API connectivity by listing models/deployments
            try:
                # Test with a simple API call
                models = main.azure_client.models.list()
                print(f"   ✓ Azure OpenAI client connected successfully")
                print(f"     Available models: {len(list(models.data)) if hasattr(models, 'data') else 'N/A'}")
            except Exception as e:
                print(f"   ! Client connected but API call failed: {e}")
                print("     This might be normal if your deployment doesn't support model listing")
        else:
            print("   ✗ Azure OpenAI client not initialized")
            return False
    except Exception as e:
        print(f"   ✗ Azure OpenAI client test failed: {e}")
        return False

    # Test 3: Test search tool with Assistant API
    print("\n3. Testing search tool with Azure OpenAI Assistants API...")
    try:
        if main.azure_client and main.AZURE_OPENAI_DEPLOYMENT_NAME:
            # Test creating an assistant first
            test_assistant = main.azure_client.beta.assistants.create(
                name="Test Assistant",
                model=main.AZURE_OPENAI_DEPLOYMENT_NAME,
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [main.VECTOR_STORE_ID]
                    }
                } if main.VECTOR_STORE_ID else {}
            )

            print(f"   ✓ Successfully created test assistant: {test_assistant.id}")

            # Test thread creation
            test_thread = main.azure_client.beta.threads.create(
                messages=[{
                    "role": "user",
                    "content": "Test search query"
                }],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [main.VECTOR_STORE_ID]
                    }
                } if main.VECTOR_STORE_ID else {}
            )

            print(f"   ✓ Successfully created test thread: {test_thread.id}")

            # Cleanup test objects
            try:
                main.azure_client.beta.assistants.delete(test_assistant.id)
                main.azure_client.beta.threads.delete(test_thread.id)
                print("   ✓ Test objects cleaned up successfully")
            except Exception as cleanup_error:
                print(f"   ! Cleanup warning: {cleanup_error}")

        else:
            print("   ✗ Azure OpenAI client or deployment name not available")
    except Exception as e:
        print(f"   ✗ Search tool test failed: {e}")
        print(f"     This could indicate issues with your deployment or vector store configuration")

    # Test 4: Test vector store access
    print("\n4. Testing vector store access...")
    try:
        if main.azure_client and main.VECTOR_STORE_ID:
            # Try to retrieve vector store info
            try:
                vector_store = main.azure_client.beta.vector_stores.retrieve(main.VECTOR_STORE_ID)
                print(f"   ✓ Vector store accessible: {vector_store.name if hasattr(vector_store, 'name') else 'Unnamed'}")

                # List files in vector store
                files = main.azure_client.beta.vector_stores.files.list(
                    vector_store_id=main.VECTOR_STORE_ID,
                    limit=5
                )
                file_count = len(list(files.data)) if hasattr(files, 'data') else 0
                print(f"   ✓ Found {file_count} files in vector store")

                if file_count > 0 and hasattr(files, 'data'):
                    # Test fetch with first file
                    first_file = files.data[0]
                    file_id = first_file.id

                    try:
                        file_info = main.azure_client.beta.vector_stores.files.retrieve(
                            vector_store_id=main.VECTOR_STORE_ID,
                            file_id=file_id
                        )
                        print(f"   ✓ Successfully retrieved file info for: {file_id}")
                    except Exception as fetch_error:
                        print(f"   ! File fetch test failed: {fetch_error}")

            except Exception as vs_error:
                print(f"   ✗ Vector store access failed: {vs_error}")
        else:
            print("   ✗ Azure OpenAI client or vector store ID not available")
    except Exception as e:
        print(f"   ✗ Vector store test failed: {e}")

    # Test 5: Server accessibility  
    print("\n5. Testing server accessibility...")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://0.0.0.0:8000/sse/")
            if response.status_code == 200:
                print("   ✓ SSE endpoint accessible")
            else:
                print(f"   ✗ SSE endpoint returned {response.status_code}")
    except ImportError:
        print("   ! httpx not available for server accessibility test")
        print("     Install with: pip install httpx")
    except Exception as e:
        print(f"   ! Server not accessible (this is normal if server isn't running): {e}")

    # Test 6: Environment configuration summary
    print("\n6. Configuration Summary...")
    print(f"   API Version: {main.AZURE_OPENAI_API_VERSION}")
    print(f"   Endpoint: {main.AZURE_OPENAI_ENDPOINT}")
    print(f"   Deployment: {main.AZURE_OPENAI_DEPLOYMENT_NAME}")
    print(f"   Vector Store ID: {main.VECTOR_STORE_ID}")
    print(f"   Client Initialized: {'✓' if main.azure_client else '✗'}")

    print("\nAzure OpenAI MCP validation completed!")
    print("\nTo run the server:")
    print("  python main.py")
    print("\nRequired environment variables:")
    print("  export AZURE_OPENAI_API_KEY=your_api_key")
    print("  export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com")
    print("  export AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name") 
    print("  export VECTOR_STORE_ID=vs_your_vector_store_id")
    print("  export AZURE_OPENAI_API_VERSION=2024-05-01-preview  # Optional")

    return True

if __name__ == "__main__":
    asyncio.run(validate_azure_mcp_server())