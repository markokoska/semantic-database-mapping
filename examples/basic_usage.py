"""
Basic usage example for the Semantic Database Schema Mapping System

This example demonstrates how to:
1. Parse a CSV file
2. Generate semantic mappings
3. Export RDF ontology
4. Query the semantic data
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.core.schema_parser import SchemaParser
from src.core.mapping_engine import MappingEngine
from src.semantic.rdf_generator import RDFGenerator


async def main():
    """Main example function"""
    
    print("🚀 Semantic Database Schema Mapping System - Basic Usage Example")
    print("=" * 70)
    
    # Initialize components
    schema_parser = SchemaParser()
    mapping_engine = MappingEngine()
    rdf_generator = RDFGenerator()
    
    # Example 1: Parse a CSV file
    print("\n📊 Step 1: Parsing CSV Schema")
    print("-" * 30)
    
    csv_file = Path("data/sample_customers.csv")
    if not csv_file.exists():
        print(f"❌ Sample file not found: {csv_file}")
        return
    
    try:
        schema_info = schema_parser.parse_file(csv_file)
        print(f"✅ Successfully parsed schema: {schema_info.name}")
        print(f"   - Tables: {len(schema_info.tables)}")
        print(f"   - Columns: {len(schema_info.tables[0].columns) if schema_info.tables else 0}")
        
        # Display column information
        if schema_info.tables:
            table = schema_info.tables[0]
            print(f"\n   Table: {table.name}")
            for col in table.columns[:5]:  # Show first 5 columns
                print(f"     - {col.name} ({col.data_type.value})")
        
    except Exception as e:
        print(f"❌ Error parsing schema: {e}")
        return
    
    # Example 2: Create and process mapping job
    print("\n🤖 Step 2: Creating Semantic Mappings")
    print("-" * 35)
    
    try:
        # Create mapping job
        job_id = await mapping_engine.create_mapping_job(str(csv_file))
        print(f"✅ Created mapping job: {job_id}")
        
        # Process the job
        print("   Processing mappings...")
        schema_mapping = await mapping_engine.process_mapping_job(job_id)
        
        print(f"✅ Mapping completed!")
        print(f"   - Overall confidence: {schema_mapping.overall_confidence:.2f}")
        print(f"   - Tables processed: {len(schema_mapping.table_mappings)}")
        
        # Display mapping results
        if schema_mapping.table_mappings:
            table_mapping = schema_mapping.table_mappings[0]
            print(f"\n   Table: {table_mapping.table_info.name}")
            print(f"   Class mapping: {table_mapping.class_mapping.uri if table_mapping.class_mapping else 'None'}")
            
            print("   Column mappings:")
            for col_mapping in table_mapping.column_mappings[:5]:  # Show first 5
                vocab_term = col_mapping.selected_mapping
                print(f"     - {col_mapping.column_info.name} → {vocab_term.uri}")
                print(f"       Confidence: {col_mapping.confidence_score:.2f}")
        
    except Exception as e:
        print(f"❌ Error creating mappings: {e}")
        return
    
    # Example 3: Generate RDF Ontology
    print("\n🔗 Step 3: Generating RDF Ontology")
    print("-" * 32)
    
    try:
        rdf_graph = rdf_generator.generate_ontology(schema_mapping)
        print(f"✅ Generated RDF ontology with {len(rdf_graph)} triples")
        
        # Export to file
        output_file = "examples/customer_ontology.ttl"
        rdf_generator.export_rdf(rdf_graph, output_file, format="turtle")
        print(f"✅ Exported ontology to: {output_file}")
        
        # Show sample triples
        print("\n   Sample RDF triples:")
        for i, (s, p, o) in enumerate(rdf_graph):
            if i >= 5:  # Show first 5 triples
                break
            print(f"     {i+1}. {s} {p} {o}")
        
    except Exception as e:
        print(f"❌ Error generating RDF: {e}")
        return
    
    # Example 4: Generate Data RDF
    print("\n📊 Step 4: Generating Data RDF")
    print("-" * 28)
    
    try:
        data_graph = rdf_generator.generate_data_rdf(schema_mapping, str(csv_file))
        print(f"✅ Generated data RDF with {len(data_graph)} triples")
        
        # Export data RDF
        data_output_file = "examples/customer_data.ttl"
        rdf_generator.export_rdf(data_graph, data_output_file, format="turtle")
        print(f"✅ Exported data RDF to: {data_output_file}")
        
    except Exception as e:
        print(f"❌ Error generating data RDF: {e}")
        return
    
    # Example 5: Display Statistics
    print("\n📈 Step 5: Mapping Statistics")
    print("-" * 25)
    
    stats = schema_mapping.mapping_statistics
    print(f"✅ Mapping Statistics:")
    print(f"   - Total tables: {stats.get('total_tables', 0)}")
    print(f"   - Total columns: {stats.get('total_columns', 0)}")
    print(f"   - Schema.org mappings: {stats.get('schema_org_mappings', 0)}")
    print(f"   - DBpedia mappings: {stats.get('dbpedia_mappings', 0)}")
    print(f"   - High confidence mappings: {stats.get('high_confidence_mappings', 0)}")
    print(f"   - Medium confidence mappings: {stats.get('medium_confidence_mappings', 0)}")
    print(f"   - Low confidence mappings: {stats.get('low_confidence_mappings', 0)}")
    
    print("\n🎉 Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
