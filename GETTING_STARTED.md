# Getting Started - Semantic Database Schema Mapping System

## Quick Start Guide

### 1. System Overview
This AI-powered system automatically maps database schemas and CSV files to semantic web technologies (RDF, OWL, SPARQL) using established vocabularies like DBpedia and Schema.org.

### 2. Installation

#### Basic Installation (Core Features)
```bash
# Install basic dependencies
pip install pandas numpy fastapi uvicorn pydantic pydantic-settings rdflib

# Test basic functionality
python test_basic.py
```

#### Full Installation (All Features)
```bash
# Install all dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 3. Usage Examples

#### Option 1: Run Examples
```bash
python run.py --examples
```

#### Option 2: Process a Specific File
```bash
python run.py --file data/sample_customers.csv
```

#### Option 3: Start API Server
```bash
python run.py --server
# Then visit: http://localhost:8000/docs
```

### 4. Sample Data
The system includes sample datasets:
- `data/sample_customers.csv` - Customer data with personal information
- `data/sample_products.csv` - Product catalog data

### 5. Expected Output
The system will generate:
- **Semantic Mappings**: Column → Vocabulary term mappings
- **RDF Ontologies**: OWL ontologies in Turtle format
- **Confidence Scores**: Quality metrics for each mapping
- **SPARQL Endpoints**: Query interfaces for semantic data

### 6. Key Features Demonstrated

#### Core Components
- ✅ **Schema Parser**: Extracts structure from CSV/DB files
- ✅ **AI Semantic Analyzer**: Uses NLP to understand data meaning
- ✅ **Vocabulary Matcher**: Maps to DBpedia and Schema.org
- ✅ **RDF Generator**: Creates semantic triples and ontologies
- ✅ **REST API**: Web interface for processing
- ✅ **Evaluation Metrics**: Quality and performance analysis

#### Academic Value
- **Semantic Web Technologies**: Practical RDF, OWL, SPARQL implementation
- **AI/ML Integration**: NLP for automated semantic understanding
- **Knowledge Engineering**: Ontology mapping and vocabulary alignment
- **Software Engineering**: Clean architecture, testing, documentation

### 7. System Architecture

```
Input (CSV/DB) → Schema Parser → AI Semantic Analyzer → Vocabulary Matcher → RDF Generator → Output (RDF/OWL)
                                        ↓
                                 [DBpedia, Schema.org APIs]
```

### 8. Troubleshooting

#### Common Issues
1. **Import Errors**: Install missing dependencies with `pip install -r requirements.txt`
2. **spaCy Model Missing**: Run `python -m spacy download en_core_web_sm`
3. **File Not Found**: Ensure sample data exists in `data/` directory

#### Dependency Issues
If you encounter dependency conflicts, try:
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 9. Project Structure
```
wbsproject/
├── src/                    # Source code
│   ├── core/              # Core mapping logic
│   ├── ai/                # AI/ML components  
│   ├── semantic/          # RDF/OWL handling
│   ├── api/               # REST API
│   └── utils/             # Utilities
├── data/                  # Sample datasets
├── examples/              # Usage examples
├── evaluation/            # Performance metrics
├── run.py                 # Main runner script
├── test_basic.py          # Basic functionality test
└── requirements.txt       # Dependencies
```

### 10. For University Course Submission

This system demonstrates:
- **Technical Implementation**: Complete working system with AI/ML integration
- **Academic Rigor**: Proper software engineering practices
- **Innovation**: Novel approach to automated semantic mapping
- **Practical Value**: Real-world applicable technology

The system is ready for demonstration and evaluation in an academic context.
