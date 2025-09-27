"""
API Client Example for the Semantic Database Schema Mapping System

This example demonstrates how to use the REST API to:
1. Upload a schema file
2. Monitor job progress
3. Retrieve results
4. Export RDF
"""

import asyncio
import aiohttp
import json
import time
from pathlib import Path


class SemanticMappingClient:
    """Client for interacting with the Semantic Mapping API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
    
    async def upload_file(self, file_path: str) -> str:
        """Upload a schema file and return job ID"""
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=Path(file_path).name)
                
                async with session.post(f"{self.api_base}/upload-schema", data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['job_id']
                    else:
                        raise Exception(f"Upload failed: {response.status}")
    
    async def get_job_status(self, job_id: str) -> dict:
        """Get job status and progress"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_base}/job/{job_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get job status: {response.status}")
    
    async def wait_for_completion(self, job_id: str, timeout: int = 300) -> dict:
        """Wait for job completion with timeout"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            job_status = await self.get_job_status(job_id)
            
            print(f"Job {job_id}: {job_status['status']} ({job_status['progress']:.1%})")
            
            if job_status['status'] == 'completed':
                return job_status
            elif job_status['status'] == 'failed':
                raise Exception(f"Job failed: {job_status.get('error_message', 'Unknown error')}")
            
            await asyncio.sleep(2)  # Wait 2 seconds before checking again
        
        raise Exception("Job timeout")
    
    async def get_mapping_results(self, job_id: str) -> dict:
        """Get the complete mapping results"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_base}/job/{job_id}/mapping") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get mapping results: {response.status}")
    
    async def download_rdf(self, job_id: str, format: str = "turtle", output_file: str = None) -> str:
        """Download RDF ontology"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_base}/job/{job_id}/rdf?format={format}") as response:
                if response.status == 200:
                    content = await response.read()
                    
                    if not output_file:
                        output_file = f"ontology_{job_id}.ttl"
                    
                    with open(output_file, 'wb') as f:
                        f.write(content)
                    
                    return output_file
                else:
                    raise Exception(f"Failed to download RDF: {response.status}")


async def main():
    """Main example function"""
    
    print("🌐 Semantic Mapping System - API Client Example")
    print("=" * 50)
    
    # Initialize client
    client = SemanticMappingClient()
    
    # Example 1: Upload and process customer data
    print("\n📤 Step 1: Uploading Customer Data")
    print("-" * 32)
    
    try:
        customer_file = "data/sample_customers.csv"
        if not Path(customer_file).exists():
            print(f"❌ Sample file not found: {customer_file}")
            return
        
        job_id = await client.upload_file(customer_file)
        print(f"✅ File uploaded successfully!")
        print(f"   Job ID: {job_id}")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return
    
    # Example 2: Monitor job progress
    print("\n⏳ Step 2: Monitoring Job Progress")
    print("-" * 33)
    
    try:
        completed_job = await client.wait_for_completion(job_id)
        print(f"✅ Job completed successfully!")
        
    except Exception as e:
        print(f"❌ Job processing failed: {e}")
        return
    
    # Example 3: Retrieve mapping results
    print("\n📊 Step 3: Retrieving Mapping Results")
    print("-" * 35)
    
    try:
        mapping_results = await client.get_mapping_results(job_id)
        
        print(f"✅ Retrieved mapping results!")
        print(f"   Overall confidence: {mapping_results['overall_confidence']:.2f}")
        print(f"   Tables: {len(mapping_results['table_mappings'])}")
        
        # Display sample mappings
        if mapping_results['table_mappings']:
            table = mapping_results['table_mappings'][0]
            print(f"\n   Sample mappings for table '{table['table_info']['name']}':")
            
            for col_mapping in table['column_mappings'][:3]:  # Show first 3
                col_name = col_mapping['column_info']['name']
                vocab_uri = col_mapping['selected_mapping']['uri']
                confidence = col_mapping['confidence_score']
                print(f"     - {col_name} → {vocab_uri} (confidence: {confidence:.2f})")
        
    except Exception as e:
        print(f"❌ Failed to retrieve results: {e}")
        return
    
    # Example 4: Download RDF ontology
    print("\n🔗 Step 4: Downloading RDF Ontology")
    print("-" * 33)
    
    try:
        rdf_file = await client.download_rdf(job_id, format="turtle", output_file="examples/api_ontology.ttl")
        print(f"✅ RDF ontology downloaded!")
        print(f"   File: {rdf_file}")
        
        # Show file size
        file_size = Path(rdf_file).stat().st_size
        print(f"   Size: {file_size} bytes")
        
    except Exception as e:
        print(f"❌ RDF download failed: {e}")
        return
    
    # Example 5: Process product data
    print("\n📦 Step 5: Processing Product Data")
    print("-" * 31)
    
    try:
        product_file = "data/sample_products.csv"
        if Path(product_file).exists():
            
            # Upload product file
            product_job_id = await client.upload_file(product_file)
            print(f"✅ Product file uploaded! Job ID: {product_job_id}")
            
            # Wait for completion
            await client.wait_for_completion(product_job_id)
            print(f"✅ Product mapping completed!")
            
            # Get results
            product_results = await client.get_mapping_results(product_job_id)
            print(f"   Product confidence: {product_results['overall_confidence']:.2f}")
            
        else:
            print(f"⚠️  Product file not found, skipping")
        
    except Exception as e:
        print(f"❌ Product processing failed: {e}")
    
    print("\n🎉 API example completed successfully!")
    print("=" * 50)


async def health_check():
    """Check if the API server is running"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/v1/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ API server is healthy: {health_data['status']}")
                    return True
                else:
                    print(f"❌ API server unhealthy: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        print("   Make sure to start the server with: python -m src.main")
        return False


if __name__ == "__main__":
    print("Checking API server health...")
    
    # Run health check first
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    if loop.run_until_complete(health_check()):
        # Server is healthy, run the example
        loop.run_until_complete(main())
    else:
        print("\n💡 To run this example:")
        print("   1. Start the API server: python -m src.main")
        print("   2. Run this example: python examples/api_client_example.py")
    
    loop.close()
