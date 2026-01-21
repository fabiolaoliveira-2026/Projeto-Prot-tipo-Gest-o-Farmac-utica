"""Schema retriever for finding relevant context."""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import numpy as np
from sentence_transformers import util


from .schema_indexer import SchemaIndexer, SchemaDocument


@dataclass
class SearchResult:
    """Result from schema retrieval."""
    content: str
    document: SchemaDocument
    score: float


class SchemaRetriever:
    """Retrieves relevant schema information for queries."""

    def __init__(
        self,
        indexer: SchemaIndexer,
        similarity_threshold: float = 0.3
    ):
        """
        Initialize the retriever.

        Args:
            indexer: SchemaIndexer instance
            similarity_threshold: Minimum similarity score (0-1)
        """
        self.indexer = indexer
        self.similarity_threshold = similarity_threshold

    def _compute_similarity(
        self,
        query_embedding: np.ndarray,
        doc_embeddings: np.ndarray
    ) -> np.ndarray:
        """Compute cosine similarity using sentence_transformers util."""
        # util.cos_sim returns a tensor, convert to numpy
        sims = util.cos_sim(query_embedding, doc_embeddings)
        return sims.numpy()[0]
    

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_type: Optional[str] = None,
        table_name: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Retrieve relevant schema information for a query.

        Args:
            query: Natural language query
            top_k: Number of results to return
            filter_type: Filter by metadata type (e.g., 'table', 'column')
            table_name: Filter by specific table name

        Returns:
            List of SearchResult objects
        """
        k = top_k

        # Encode query
        query_embedding = self.indexer.model.encode(
            query,
            convert_to_numpy=True
        )

        # Get all data
        all_embeddings = self.indexer.get_embeddings()
        all_documents = self.indexer.get_documents()
        all_metas = self.indexer.get_metadata()

        # Filter indices
        indices = []
        for i, doc in enumerate(all_metas):
            # Check type filter
            if filter_type and doc.type != filter_type:
                continue
            
            # Check table name filter
            if table_name and doc.table_name != table_name:
                continue
                
            indices.append(i)

        if not indices:
            return []
        
        target_embeddings = all_embeddings[indices]
        target_documents = [all_documents[i] for i in indices]
        target_metas = [all_metas[i] for i in indices]

        # Compute similarities
        similarities = self._compute_similarity(query_embedding, target_embeddings)

        # Get top-k results
        # usage of argpartition for efficiency if array is large, but argsort is fine for schema sizes
        top_indices = np.argsort(similarities)[::-1]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score < self.similarity_threshold:
                break

            results.append(SearchResult(
                content=target_documents[idx],
                document=target_metas[idx],
                score=score
            ))

            if len(results) >= k:
                break

        return results

    def retrieve_tables(self, query: str, top_k: Optional[int] = None) -> List[str]:
        """Retrieve relevant table names."""
        results = self.retrieve(query, top_k=top_k, filter_type='table')
        # Preserve order, remove duplicates
        tables = []
        seen = set()
        for res in results:
            name = res.document.table_name
            if name and name not in seen:
                tables.append(name)
                seen.add(name)
        return tables

    def retrieve_columns(
        self,
        query: str,
        table_name: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant columns."""
        retrieval_k = top_k
        results = self.retrieve(
            query, 
            top_k=retrieval_k, 
            filter_type='column',
            table_name=table_name
        )

        columns = []
        seen = set()

        for res in results:
            doc = res.document
            
            # Check table name again (redundant if retrieve works, but safe)
            if table_name and doc.table_name != table_name:
                continue

            col_key = (doc.table_name, doc.metadata.get('column_name'))
            if col_key not in seen:
                seen.add(col_key)
                columns.append({
                    'table': doc.table_name,
                    'column': doc.metadata.get('column_name'),
                    'type': doc.metadata.get('data_type', ''),
                    'description': doc.metadata.get('description', ''),
                    'score': res.score
                })

                if top_k and len(columns) >= top_k:
                    break
        return columns

    def _format_constraints(self, tables_mentioned: Set[str]) -> List[str]:
        """Extract and format constraints for mentioned tables."""
        schema = self.indexer.load_schema()
        constraints = []

        if 'tabelas' not in schema:
            return []

        # Helper to format a single constraint
        def add_constraint(msg: str):
            if msg not in constraints:
                constraints.append(msg)

        for table_name in tables_mentioned:
            if table_name not in schema['tabelas']:
                continue
            
            table_info = schema['tabelas'][table_name]

            # Primary key
            if 'primary_key' in table_info:
                pk = table_info['primary_key']
                pk_cols = ', '.join(pk.get('columns', []))
                add_constraint(f"Chave primária da tabela {table_name}: {pk_cols}")

            # Indexes
            if 'indexes' in table_info:
                for idx in table_info['indexes']:
                    idx_name = idx.get('name', '')
                    idx_cols = ', '.join(idx.get('columns', []))
                    add_constraint(f"Índice {idx_name} na tabela {table_name}: {idx_cols}")

            # Foreign keys (source)
            if 'foreign_keys' in table_info:
                for fk in table_info['foreign_keys']:
                    fk_name = fk.get('name', '')
                    fk_cols = ', '.join(fk.get('columns', []))
                    ref_table = fk.get('references', {}).get('table', '')
                    ref_cols = ', '.join(fk.get('references', {}).get('columns', []))
                    add_constraint(f"Chave estrangeira {fk_name} em {table_name}({fk_cols}) referencia {ref_table}({ref_cols})")

        # Foreign keys referencing these tables (incoming)
        for t_name, t_info in schema['tabelas'].items():
            if t_name in tables_mentioned: 
                continue # Already handled above
            
            if 'foreign_keys' in t_info:
                for fk in t_info['foreign_keys']:
                    ref_table = fk.get('references', {}).get('table', '')
                    if ref_table in tables_mentioned:
                        fk_name = fk.get('name', '')
                        fk_cols = ', '.join(fk.get('columns', []))
                        ref_cols = ', '.join(fk.get('references', {}).get('columns', []))
                        add_constraint(f"Chave estrangeira {fk_name} em {t_name}({fk_cols}) referencia {ref_table}({ref_cols})")

        return constraints

    def get_context_for_query(
        self,
        query: str,
        max_context_length: int = 32768,
        max_tables: int = 5,
        max_columns_per_table: int = 10,
        include_scores: bool = False
    ) -> str:
        """Get formatted context for a SQL generation query."""
        
        # 1. Identify relevant tables
        table_results = self.retrieve(
            query, 
            top_k=max_tables, 
            filter_type='table'
        )
        
        tables_mentioned = set()
        table_context_lines = []
        
        for res in table_results:
            name = res.document.table_name
            if name and name not in tables_mentioned:
                tables_mentioned.add(name)
                line = f"- {res.content}"
                if include_scores:
                    line += f" (Score: {res.score:.3f})"
                table_context_lines.append(line)
        
        # 2. Identify relevant columns per table
        columns_by_table = {}
        if tables_mentioned:
            for table in tables_mentioned:
                table_columns = self.retrieve_columns(
                    query,
                    table_name=table,
                    top_k=max_columns_per_table
                )
                
                if table_columns:
                    columns_list = []
                    for c in table_columns:
                        col_str = f"Tabela {c['table']}, Coluna {c['column']}"
                        if c['type']:
                            col_str += f", Tipo: {c['type']}"
                        if c['description']:
                            col_str += f", Descrição: {c['description']}"
                        if include_scores:
                            col_str += f" (Score: {c['score']:.3f})"
                        columns_list.append(col_str)
                    columns_by_table[table] = columns_list

        # 3. Get constraints
        constraints = self._format_constraints(tables_mentioned)

        # 4. Build Final Context
        context_sections = []
        
        if tables_mentioned:
            context_sections.append("## Tabelas Relevantes:")
            context_sections.extend(table_context_lines)
            context_sections.append("")

        if columns_by_table:
            context_sections.append("## Colunas Relevantes:")
            # Sort tables by relevance (approximation: order in tables_mentioned)
            # We use the order they appeared in table results
            
            for table in tables_mentioned:
                cols = columns_by_table.get(table)
                if cols:
                    context_sections.append(f"\n### Tabela {table}:")
                    for c in cols:
                        # Remove redundant "Tabela {table}, " prefix from the column string if present
                        prefix = f"Tabela {table}, "
                        if c.startswith(prefix):
                            c = c[len(prefix):]
                        context_sections.append(f"- {c}")
            context_sections.append("")

        if constraints:
            context_sections.append("## Relacionamentos e Restrições (Obrigatório):")
            for c in constraints:
                context_sections.append(f"- {c}")
            context_sections.append("")

        context = "\n".join(context_sections)
        
        if len(context) > max_context_length:
            context = context[:max_context_length] + "\n... (contexto truncado)"

        return context
