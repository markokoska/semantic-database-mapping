import sys
import asyncio
import argparse
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

from src.core.schema_parser import SchemaParser
from src.core.mapping_engine import MappingEngine
from src.semantic.rdf_generator import RDFGenerator

async def process_file(file_path: str):
    print(f"⚡ Processing file: {file_path}")
    
    schema_parser = SchemaParser()
    mapping_engine = MappingEngine()
    rdf_generator = RDFGenerator()
    
    try:
        schema_info = schema_parser.parse_file(file_path)
        print(f"✅ Parsed schema with {len(schema_info.tables)} tables")
        
        job_id = await mapping_engine.create_mapping_job(file_path)
        schema_mapping = await mapping_engine.process_mapping_job(job_id)
        print(f"✅ Generated mappings with confidence: {schema_mapping.overall_confidence:.2f}")
        
        rdf_graph = rdf_generator.generate_ontology(schema_mapping)
        output_file = f"{Path(file_path).stem}_ontology.ttl"
        rdf_generator.export_rdf(rdf_graph, output_file)
        print(f"✅ RDF ontology saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error processing file: {e}")

def main():
    parser = argparse.ArgumentParser(description="Semantic Database Schema Mapping System - CLI Only")
    parser.add_argument("--file", type=str, required=True, help="CSV file to process")
    
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"❌ File not found: {args.file}")
        sys.exit(1)
    
    print("🚀 Semantic Database Schema Mapping System")
    print("=" * 50)
    
    asyncio.run(process_file(args.file))

if __name__ == "__main__":
    main()
