import pandas as pd
import sqlite3
import json
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import logging

from .models import (
    SchemaInfo, TableInfo, ColumnInfo, DataType
)

logger = logging.getLogger(__name__)


class SchemaParser:
    def __init__(self):
        self.supported_formats = ['.csv', '.json', '.sqlite', '.db']
    
    def parse_file(self, file_path: Union[str, Path]) -> SchemaInfo:

        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.csv':
            return self._parse_csv(file_path)
        elif file_extension == '.json':
            return self._parse_json(file_path)
        elif file_extension in ['.sqlite', '.db']:
            return self._parse_sqlite(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def _parse_csv(self, file_path: Path) -> SchemaInfo:
        try:
            df = pd.read_csv(file_path, nrows=100)
            
            columns = []
            for col_name in df.columns:
                col_data = df[col_name]
                
                data_type = self._infer_data_type(col_data)
                
                nullable = col_data.isnull().any()
                
                sample_values = col_data.dropna().head(5).tolist()
                
                column_info = ColumnInfo(
                    name=col_name,
                    data_type=data_type,
                    nullable=nullable,
                    sample_values=sample_values
                )
                columns.append(column_info)
            
            table_info = TableInfo(
                name=file_path.stem,
                columns=columns,
                row_count=len(df)
            )
            
            schema_info = SchemaInfo(
                name=file_path.stem,
                tables=[table_info],
                source_type="csv"
            )
            
            logger.info(f"Successfully parsed CSV: {file_path}")
            return schema_info
            
        except Exception as e:
            logger.error(f"Error parsing CSV {file_path}: {e}")
            raise
    
    def _parse_json(self, file_path: Path) -> SchemaInfo:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list) and len(data) > 0:
                sample_obj = data[0]
                columns = self._extract_columns_from_dict(sample_obj, data[:100])
                
                table_info = TableInfo(
                    name=file_path.stem,
                    columns=columns,
                    row_count=len(data)
                )
                
                schema_info = SchemaInfo(
                    name=file_path.stem,
                    tables=[table_info],
                    source_type="json"
                )
                
            elif isinstance(data, dict):
                columns = self._extract_columns_from_dict(data, [data])
                
                table_info = TableInfo(
                    name=file_path.stem,
                    columns=columns,
                    row_count=1
                )
                
                schema_info = SchemaInfo(
                    name=file_path.stem,
                    tables=[table_info],
                    source_type="json"
                )
            else:
                raise ValueError("Unsupported JSON structure")
            
            logger.info(f"Successfully parsed JSON: {file_path}")
            return schema_info
            
        except Exception as e:
            logger.error(f"Error parsing JSON {file_path}: {e}")
            raise
    
    def _parse_sqlite(self, file_path: Path) -> SchemaInfo:
        try:
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_names = [row[0] for row in cursor.fetchall()]
            
            tables = []
            for table_name in table_names:
                cursor.execute(f"PRAGMA table_info({table_name});")
                table_info_rows = cursor.fetchall()
                
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                row_count = cursor.fetchone()[0]
                
                columns = []
                for col_info in table_info_rows:
                    col_name = col_info[1]
                    col_type = col_info[2]
                    not_null = col_info[3]
                    primary_key = col_info[5]
                    
                    data_type = self._map_sqlite_type(col_type)
                    
                    cursor.execute(f"SELECT DISTINCT {col_name} FROM {table_name} LIMIT 5;")
                    sample_values = [row[0] for row in cursor.fetchall() if row[0] is not None]
                    
                    column_info = ColumnInfo(
                        name=col_name,
                        data_type=data_type,
                        nullable=not not_null,
                        primary_key=bool(primary_key),
                        sample_values=sample_values
                    )
                    columns.append(column_info)
                
                table_info = TableInfo(
                    name=table_name,
                    columns=columns,
                    row_count=row_count
                )
                tables.append(table_info)
            
            conn.close()
            
            schema_info = SchemaInfo(
                name=file_path.stem,
                tables=tables,
                source_type="sqlite"
            )
            
            logger.info(f"Successfully parsed SQLite: {file_path}")
            return schema_info
            
        except Exception as e:
            logger.error(f"Error parsing SQLite {file_path}: {e}")
            raise
    
    def _infer_data_type(self, series: pd.Series) -> DataType:
        dtype = series.dtype
        
        if pd.api.types.is_integer_dtype(dtype):
            return DataType.INTEGER
        elif pd.api.types.is_float_dtype(dtype):
            return DataType.FLOAT
        elif pd.api.types.is_bool_dtype(dtype):
            return DataType.BOOLEAN
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return DataType.DATETIME
        else:
            sample_values = series.dropna().astype(str).head(10)
            
            date_patterns = 0
            for val in sample_values:
                try:
                    pd.to_datetime(val)
                    date_patterns += 1
                except:
                    pass
            
            if date_patterns > len(sample_values) * 0.7:
                return DataType.DATE
            
            return DataType.STRING
    
    def _extract_columns_from_dict(self, sample_dict: Dict[str, Any], 
                                 all_objects: List[Dict[str, Any]]) -> List[ColumnInfo]:
        columns = []
        
        for key, value in sample_dict.items():
            data_type = self._infer_data_type_from_value(value)
            
            nullable = any(obj.get(key) is None for obj in all_objects)
            
            sample_values = []
            for obj in all_objects[:5]:
                val = obj.get(key)
                if val is not None:
                    sample_values.append(val)
            
            column_info = ColumnInfo(
                name=key,
                data_type=data_type,
                nullable=nullable,
                sample_values=sample_values
            )
            columns.append(column_info)
        
        return columns
    
    def _infer_data_type_from_value(self, value: Any) -> DataType:
        if isinstance(value, bool):
            return DataType.BOOLEAN
        elif isinstance(value, int):
            return DataType.INTEGER
        elif isinstance(value, float):
            return DataType.FLOAT
        elif isinstance(value, (dict, list)):
            return DataType.JSON
        else:
            return DataType.STRING
    
    def _map_sqlite_type(self, sqlite_type: str) -> DataType:
        sqlite_type = sqlite_type.upper()
        
        if 'INT' in sqlite_type:
            return DataType.INTEGER
        elif 'REAL' in sqlite_type or 'FLOAT' in sqlite_type or 'DOUBLE' in sqlite_type:
            return DataType.FLOAT
        elif 'BOOL' in sqlite_type:
            return DataType.BOOLEAN
        elif 'DATE' in sqlite_type:
            return DataType.DATE
        elif 'DATETIME' in sqlite_type or 'TIMESTAMP' in sqlite_type:
            return DataType.DATETIME
        elif 'TEXT' in sqlite_type or 'CLOB' in sqlite_type:
            return DataType.TEXT
        elif 'BLOB' in sqlite_type:
            return DataType.BINARY
        else:
            return DataType.STRING
