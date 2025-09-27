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
- **Web Interface**: User-friendly mapping review and editing

## Technology Stack

- **Backend**: Python 3.9+, FastAPI
- **Semantic Web**: RDFLib, Owlready2, SPARQLWrapper
- **AI/ML**: Transformers, spaCy, sentence-transformers
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: React, TypeScript, Material-UI
- **Containerization**: Docker, Docker Compose

## Quick Start

```bash
# Clone and setup
git clone <repository>
cd wbsproject

# Install dependencies
pip install -r requirements.txt

# Run the system
python -m src.main

# Access web interface
http://localhost:8000
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
wbsproject/
├── src/                    # Source code
│   ├── core/              # Core mapping logic
│   ├── ai/                # AI/ML components
│   ├── semantic/          # RDF/OWL handling
│   ├── api/               # REST API
│   └── web/               # Web interface
├── data/                  # Sample datasets
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation
├── examples/              # Usage examples
└── evaluation/            # Performance metrics
```

## License

MIT License - See LICENSE file for details.
