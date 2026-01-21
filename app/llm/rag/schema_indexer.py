"""Schema indexer for RAG system using sentence transformers."""

import os
import pickle
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import yaml
import numpy as np
from pathlib import Path


@dataclass
class SchemaDocument:
    """Represents a document in the schema index."""
    content: str
    type: str
    table_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class SchemaIndexer:
    """Indexes database schema for efficient retrieval."""

    def __init__(
        self,
        schema_path: str,
        model_name: str = "neuralmind/bert-large-portuguese-cased",
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the schema indexer.

        Args:
            schema_path: Path to the schema YAML file
            model_name: Name of the sentence transformer model
            cache_dir: Directory to cache embeddings
        """
        self.schema_path = schema_path
        self.model_name = model_name
        self.cache_dir = cache_dir or ".cache/embeddings"

        # Lazy loading
        self._model = None
        self._schema_data = None
        self._documents: Optional[List[str]] = None
        self._embeddings: Optional[np.ndarray] = None
        self._metadata: Optional[List[SchemaDocument]] = None

    @property
    def model(self):
        """Lazy load the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for RAG. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    def load_schema(self) -> Dict[str, Any]:
        """Load schema from YAML file."""
        if self._schema_data is None:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                self._schema_data = yaml.safe_load(f)
        return self._schema_data

    def _index_table_description(self, table_name: str, table_info: Dict[str, Any]) -> Optional[Tuple[str, SchemaDocument]]:
        """Index table description."""
        if 'descricao_tabela' not in table_info:
            return None
            
        content = f"Tabela {table_name}: {table_info['descricao_tabela']}"
        metadata = SchemaDocument(
            content=content,
            type='table',
            table_name=table_name,
            metadata={'section': 'description'}
        )
        return content, metadata

    def _index_columns(self, table_name: str, columns: List[Any]) -> Tuple[List[str], List[SchemaDocument]]:
        """Index columns for a table."""
        docs = []
        metas = []
        
        for column in columns:
            if isinstance(column, dict):
                for col_name, col_info in column.items():
                    # Handle both detailed columns (dict) and simple columns (string/other)
                    if isinstance(col_info, dict):
                        tipo = col_info.get('tipo', '')
                        desc = col_info.get('descricao', '')
                        content = f"Tabela {table_name}, Coluna {col_name}"
                        if tipo:
                            content += f", Tipo: {tipo}"
                        if desc:
                            content += f", Descrição: {desc}"
                            
                        metas.append(SchemaDocument(
                            content=content,
                            type='column',
                            table_name=table_name,
                            metadata={
                                'column_name': col_name,
                                'data_type': tipo,
                                'description': desc
                            }
                        ))
                        docs.append(content)
                    else:
                        tipo = str(col_info) if col_info else ''
                        content = f"Tabela {table_name}, Coluna {col_name}"
                        if tipo:
                            content += f", Tipo: {tipo}"
                            
                        metas.append(SchemaDocument(
                            content=content,
                            type='column',
                            table_name=table_name,
                            metadata={
                                'column_name': col_name,
                                'data_type': tipo,
                                'description': ''
                            }
                        ))
                        docs.append(content)
        return docs, metas

    def _index_relationships(self, table_name: str, table_info: Dict[str, Any]) -> Tuple[List[str], List[SchemaDocument]]:
        """Index keys and indexes."""
        docs = []
        metas = []

        # Primary key
        if 'primary_key' in table_info:
            pk = table_info['primary_key']
            pk_name = pk.get('name', '')
            pk_cols = ', '.join(pk.get('columns', []))
            content = f"Chave primária da tabela {table_name}: {pk_cols}"
            
            docs.append(content)
            metas.append(SchemaDocument(
                content=content,
                type='primary_key',
                table_name=table_name,
                metadata={
                    'pk_name': pk_name,
                    'columns': pk.get('columns', [])
                }
            ))

        # Indexes
        if 'indexes' in table_info:
            for idx in table_info['indexes']:
                idx_name = idx.get('name', '')
                idx_cols = ', '.join(idx.get('columns', []))
                content = f"Índice {idx_name} na tabela {table_name}: {idx_cols}"
                
                docs.append(content)
                metas.append(SchemaDocument(
                    content=content,
                    type='index',
                    table_name=table_name,
                    metadata={
                        'index_name': idx_name,
                        'columns': idx.get('columns', [])
                    }
                ))

        # Foreign keys
        if 'foreign_keys' in table_info:
            for fk in table_info['foreign_keys']:
                fk_name = fk.get('name', '')
                fk_cols = ', '.join(fk.get('columns', []))
                ref_table = fk.get('references', {}).get('table', '')
                ref_cols = ', '.join(fk.get('references', {}).get('columns', []))
                content = f"Chave estrangeira {fk_name} em {table_name}({fk_cols}) referencia {ref_table}({ref_cols})"
                
                docs.append(content)
                metas.append(SchemaDocument(
                    content=content,
                    type='foreign_key',
                    table_name=table_name,
                    metadata={
                        'fk_name': fk_name,
                        'columns': fk.get('columns', []),
                        'references_table': ref_table,
                        'references_columns': fk.get('references', {}).get('columns', [])
                    }
                ))
                
        return docs, metas

    def _create_documents(self) -> Tuple[List[str], List[SchemaDocument]]:
        """
        Create searchable documents from schema.

        Returns:
            Tuple of (documents, metadata)
        """
        schema = self.load_schema()
        documents = []
        metadata = []

        if 'tabelas' in schema:
            for table_name, table_info in schema['tabelas'].items():
                # 1. Table Description
                table_doc = self._index_table_description(table_name, table_info)
                if table_doc:
                    documents.append(table_doc[0])
                    metadata.append(table_doc[1])

                # 2. Columns
                if 'columns' in table_info:
                    col_docs, col_metas = self._index_columns(table_name, table_info['columns'])
                    documents.extend(col_docs)
                    metadata.extend(col_metas)

                # 3. Relationships (PK, FK, Indexes)
                rel_docs, rel_metas = self._index_relationships(table_name, table_info)
                documents.extend(rel_docs)
                metadata.extend(rel_metas)

        return documents, metadata

    def build_index(self, force_rebuild: bool = False) -> None:
        """
        Build the search index with embeddings.

        Args:
            force_rebuild: Force rebuild even if cache exists
        """
        cache_path = Path(self.cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)

        # Use v2 to avoid conflicts with old cache format (dicts vs dataclasses)
        cache_file = cache_path / "schema_embeddings_v2.pkl"

        # Try to load from cache
        if not force_rebuild and cache_file.exists():
            print(f"Loading embeddings from cache: {cache_file}")
            try:
                with open(cache_file, 'rb') as f:
                    cached = pickle.load(f)
                    self._documents = cached['documents']
                    self._embeddings = cached['embeddings']
                    self._metadata = cached['metadata']
                    print(f"Loaded {len(self._documents)} documents from cache")
                    return
            except Exception as e:
                print(f"Failed to load cache: {e}. Rebuilding...")

        # Build index
        print("Building schema index...")
        self._documents, self._metadata = self._create_documents()

        print(f"Encoding {len(self._documents)} documents...")
        self._embeddings = self.model.encode(
            self._documents,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # Cache embeddings
        print(f"Caching embeddings to: {cache_file}")
        with open(cache_file, 'wb') as f:
            pickle.dump({
                'documents': self._documents,
                'embeddings': self._embeddings,
                'metadata': self._metadata
            }, f)

        print(f"Index built with {len(self._documents)} documents")

    def get_embeddings(self) -> np.ndarray:
        """Get the embeddings array."""
        if self._embeddings is None:
            self.build_index()
        return self._embeddings

    def get_documents(self) -> List[str]:
        """Get the documents list."""
        if self._documents is None:
            self.build_index()
        return self._documents

    def get_metadata(self) -> List[SchemaDocument]:
        """Get the metadata list."""
        if self._metadata is None:
            self.build_index()
        return self._metadata
