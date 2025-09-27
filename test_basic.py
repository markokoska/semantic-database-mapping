"""
Basic test script for the Semantic Database Schema Mapping System
Tests core functionality without requiring heavy ML dependencies
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_basic_imports():
    """Test basic imports"""
    print("🧪 Testing basic imports...")
    
    try:
        from src.core.models import ColumnInfo, TableInfo, SchemaInfo, DataType
        print("✅ Core models imported")
        
        from src.core.config import settings
        print("✅ Configuration loaded")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_schema_parser():
    """Test schema parser with sample data"""
    print("🧪 Testing schema parser...")
    
    try:
        from src.core.schema_parser import SchemaParser
        
        # Create sample CSV data
        sample_csv = Path("test_sample.csv")
        sample_data = """id,name,email,age
1,John Doe,john@example.com,25
2,Jane Smith,jane@example.com,30
3,Bob Johnson,bob@example.com,35"""
        
        with open(sample_csv, 'w') as f:
            f.write(sample_data)
        
        # Parse the sample
        parser = SchemaParser()
        schema_info = parser.parse_file(sample_csv)
        
        # Verify results
        assert len(schema_info.tables) == 1
        assert len(schema_info.tables[0].columns) == 4
        assert schema_info.tables[0].columns[0].name == "id"
        assert schema_info.tables[0].columns[1].name == "name"
        
        # Clean up
        sample_csv.unlink()
        
        print("✅ Schema parser working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Schema parser test failed: {e}")
        return False


def test_models():
    """Test data models"""
    print("🧪 Testing data models...")
    
    try:
        from src.core.models import ColumnInfo, TableInfo, DataType
        
        # Create test column
        column = ColumnInfo(
            name="test_column",
            data_type=DataType.STRING,
            nullable=True,
            sample_values=["test1", "test2"]
        )
        
        # Create test table
        table = TableInfo(
            name="test_table",
            columns=[column],
            row_count=100
        )
        
        # Verify
        assert column.name == "test_column"
        assert table.name == "test_table"
        assert len(table.columns) == 1
        
        print("✅ Data models working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Models test failed: {e}")
        return False


def test_sample_data():
    """Test with actual sample data files"""
    print("🧪 Testing with sample data...")
    
    try:
        from src.core.schema_parser import SchemaParser
        
        sample_files = [
            "data/sample_customers.csv",
            "data/sample_products.csv"
        ]
        
        parser = SchemaParser()
        results = {}
        
        for sample_file in sample_files:
            if Path(sample_file).exists():
                schema_info = parser.parse_file(sample_file)
                results[sample_file] = {
                    "tables": len(schema_info.tables),
                    "columns": len(schema_info.tables[0].columns) if schema_info.tables else 0
                }
                print(f"  ✅ {sample_file}: {results[sample_file]['columns']} columns")
            else:
                print(f"  ⚠️  {sample_file}: File not found")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Sample data test failed: {e}")
        return False


def main():
    """Run all basic tests"""
    print("🚀 Semantic Database Schema Mapping System - Basic Tests")
    print("=" * 60)
    
    tests = [
        test_basic_imports,
        test_models,
        test_schema_parser,
        test_sample_data
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All basic tests passed! The core system is working.")
        print("\nNext steps:")
        print("  1. Install full dependencies: pip install -r requirements.txt")
        print("  2. Run examples: python run.py --examples")
        print("  3. Start API server: python run.py --server")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
