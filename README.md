# Semantic Database Schema Mapping System

## Overview

An AI-powered system that automatically maps relational database schemas and CSV files to semantic web technologies (RDF, OWL, SPARQL) using established vocabularies like DBpedia and Schema.org.

## Features

- **Automated Schema Analysis**: Parses CSV files and database schemas
- **AI-Powered Semantic Mapping**: Uses NLP to understand data semantics
- **Vocabulary Integration**: Maps to DBpedia, Schema.org, and custom ontologies
- **RDF Generation**: Creates semantic triples and OWL ontologies
- **SPARQL Interface**: Enables semantic querying
- **Confidence Scoring**: Provides mapping quality metrics
- **Command Line Interface**: Simple terminal-based processing

## Technology Stack

- **Backend**: Python 3.9+
- **Semantic Web**: RDFLib, Owlready2, SPARQLWrapper
- **AI/ML**: Transformers, spaCy, sentence-transformers
- **Interface**: Command Line Interface (CLI)

## Quick Start

```bash
# Clone and setup
git clone https://github.com/markokoska/semantic-database-mapping.git
cd semantic-database-mapping

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Process your CSV files
python run_cli.py --file data/sample_customers.csv
python run_cli.py --file your_data.csv

# View generated semantic mappings
notepad filename_ontology.ttl
```

## Academic Context

This system demonstrates:
- Semantic Web Technologies (RDF, OWL, SPARQL)
- Knowledge Engineering and Ontology Mapping
- AI/ML for Natural Language Understanding
- Software Engineering Best Practices
- Performance Evaluation and Metrics

## Project Structure

```
semantic-database-mapping/
├── src/                    # Source code
│   ├── core/              # Core mapping logic
│   ├── ai/                # AI/ML components
│   ├── semantic/          # RDF/OWL handling
│   └── utils/             # Utilities
├── data/                  # Sample datasets
├── examples/              # Usage examples
├── evaluation/            # Performance metrics
├── run_cli.py             # Command line interface
└── requirements.txt       # Dependencies
```

## Contributors

- **[Your Name]** - Main Developer
- **[Contributor Name]** - [Role/Contribution]

## License

MIT License - See LICENSE file for details.
