"""
Main runner script for the Semantic Database Schema Mapping System

This script provides different modes of operation:
1. API server mode
2. CLI processing mode
3. Example demonstration mode
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from src.main import main as run_server
from examples.run_example import run_simple_example


def run_api_server():
    """Run the FastAPI server"""
    print("🌐 Starting Semantic Mapping API Server...")
    run_server()


def run_examples():
    """Run example demonstrations"""
    print("📚 Running example demonstrations...")
    asyncio.run(run_simple_example())


def run_cli_mode(file_path: str):
    """Run in CLI mode for a specific file"""
    print(f"⚡ Processing file: {file_path}")
    
    async def process_file():
        from src.core.schema_parser import SchemaParser
        from src.core.mapping_engine import MappingEngine
        from src.semantic.rdf_generator import RDFGenerator
        
        # Initialize components
        schema_parser = SchemaParser()
        mapping_engine = MappingEngine()
        rdf_generator = RDFGenerator()
        
        # Process file
        try:
            # Parse schema
            schema_info = schema_parser.parse_file(file_path)
            print(f"✅ Parsed schema with {len(schema_info.tables)} tables")
            
            # Create mappings
            job_id = await mapping_engine.create_mapping_job(file_path)
            schema_mapping = await mapping_engine.process_mapping_job(job_id)
            print(f"✅ Generated mappings with confidence: {schema_mapping.overall_confidence:.2f}")
            
            # Generate RDF
            rdf_graph = rdf_generator.generate_ontology(schema_mapping)
            output_file = f"{Path(file_path).stem}_ontology.ttl"
            rdf_generator.export_rdf(rdf_graph, output_file)
            print(f"✅ RDF ontology saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Error processing file: {e}")
    
    asyncio.run(process_file())


def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Semantic Database Schema Mapping System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py --server          # Start API server
  python run.py --examples        # Run examples
  python run.py --file data/sample.csv  # Process specific file
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--server", action="store_true", help="Start API server")
    group.add_argument("--examples", action="store_true", help="Run examples")
    group.add_argument("--file", type=str, help="Process specific file")
    
    args = parser.parse_args()
    
    print("🚀 Semantic Database Schema Mapping System")
    print("=" * 50)
    
    if args.server:
        run_api_server()
    elif args.examples:
        run_examples()
    elif args.file:
        if not Path(args.file).exists():
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        run_cli_mode(args.file)


if __name__ == "__main__":
    main()
