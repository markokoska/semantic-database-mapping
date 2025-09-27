"""
Simple example runner for the Semantic Database Schema Mapping System

This script demonstrates the complete workflow:
1. Parse CSV files
2. Generate semantic mappings
3. Create RDF ontologies
4. Export results
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.schema_parser import SchemaParser
from src.core.mapping_engine import MappingEngine
from src.semantic.rdf_generator import RDFGenerator


async def run_simple_example():
    """Run a simple mapping example"""
    
    print("🚀 Semantic Database Schema Mapping System")
    print("=" * 50)
    print("Starting simple example...")
    
    try:
        # Initialize components
        print("\n📚 Initializing components...")
        schema_parser = SchemaParser()
        mapping_engine = MappingEngine()
        rdf_generator = RDFGenerator()
        print("✅ Components initialized")
        
        # Check for sample data
        sample_files = [
            Path("data/sample_customers.csv"),
            Path("data/sample_products.csv")
        ]
        
        available_files = [f for f in sample_files if f.exists()]
        
        if not available_files:
            print("❌ No sample files found. Please ensure sample data exists in the data/ directory.")
            return
        
        # Process each file
        for sample_file in available_files:
            print(f"\n📊 Processing: {sample_file.name}")
            print("-" * 30)
            
            start_time = time.time()
            
            # Parse schema
            print("  🔍 Parsing schema...")
            schema_info = schema_parser.parse_file(sample_file)
            print(f"  ✅ Found {len(schema_info.tables)} table(s) with {len(schema_info.tables[0].columns) if schema_info.tables else 0} columns")
            
            # Create mapping job
            print("  🤖 Creating semantic mappings...")
            job_id = await mapping_engine.create_mapping_job(str(sample_file))
            
            # Process mappings
            schema_mapping = await mapping_engine.process_mapping_job(job_id)
            
            processing_time = time.time() - start_time
            print(f"  ✅ Mappings created in {processing_time:.2f} seconds")
            print(f"  📈 Overall confidence: {schema_mapping.overall_confidence:.2f}")
            
            # Show some mappings
            if schema_mapping.table_mappings:
                table_mapping = schema_mapping.table_mappings[0]
                print(f"  📋 Table: {table_mapping.table_info.name}")
                
                if table_mapping.class_mapping:
                    print(f"     → Class: {table_mapping.class_mapping.uri}")
                
                print("     Column mappings:")
                for col_mapping in table_mapping.column_mappings[:5]:  # Show first 5
                    col_name = col_mapping.column_info.name
                    vocab_uri = col_mapping.selected_mapping.uri
                    confidence = col_mapping.confidence_score
                    print(f"       • {col_name} → {vocab_uri} ({confidence:.2f})")
                
                if len(table_mapping.column_mappings) > 5:
                    remaining = len(table_mapping.column_mappings) - 5
                    print(f"       ... and {remaining} more mappings")
            
            # Generate RDF
            print("  🔗 Generating RDF ontology...")
            rdf_graph = rdf_generator.generate_ontology(schema_mapping)
            
            # Export RDF
            output_file = f"examples/{sample_file.stem}_ontology.ttl"
            rdf_generator.export_rdf(rdf_graph, output_file, format="turtle")
            print(f"  💾 Ontology saved to: {output_file}")
            
            # Generate data RDF if it's a small file
            if sample_file.stat().st_size < 1024 * 1024:  # Less than 1MB
                print("  📊 Generating data RDF...")
                data_graph = rdf_generator.generate_data_rdf(schema_mapping, str(sample_file))
                data_output = f"examples/{sample_file.stem}_data.ttl"
                rdf_generator.export_rdf(data_graph, data_output, format="turtle")
                print(f"  💾 Data RDF saved to: {data_output}")
            
            print(f"  🎉 {sample_file.name} processing completed!")
        
        print(f"\n🎊 All files processed successfully!")
        print("📁 Check the examples/ directory for generated RDF files")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function"""
    # Create examples directory if it doesn't exist
    Path("examples").mkdir(exist_ok=True)
    
    # Run the example
    asyncio.run(run_simple_example())


if __name__ == "__main__":
    main()
