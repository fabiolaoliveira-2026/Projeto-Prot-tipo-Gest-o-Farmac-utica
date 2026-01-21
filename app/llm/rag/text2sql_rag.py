"""Text2SQL with RAG enhancement."""

from typing import Optional, Dict, Any, List
from pathlib import Path
from .schema_indexer import SchemaIndexer
from .retriever import SchemaRetriever


class Text2SQLWithRAG:
    """Enhanced Text2SQL generator with RAG support."""

    def __init__(
        self,
        schema_path: str,
        model_name: str = "neuralmind/bert-large-portuguese-cased",
        similarity_threshold: float = 0.3,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize Text2SQL with RAG.

        Args:
            schema_path: Path to schema YAML file
            model_name: Sentence transformer model name
            similarity_threshold: Minimum similarity score
            cache_dir: Cache directory for embeddings
        """
        self.indexer = SchemaIndexer(
            schema_path=schema_path,
            model_name=model_name,
            cache_dir=cache_dir
        )
        self.retriever = SchemaRetriever(
            indexer=self.indexer,
            similarity_threshold=similarity_threshold
        )

        # Build index on initialization
        self.indexer.build_index()

    def _get_key_columns(self, table_name: str) -> set:
        """
        Extrai todas as colunas que são chaves primárias, estrangeiras ou índices.

        Args:
            table_name: Nome da tabela

        Returns:
            Set com nomes das colunas de chaves/índices
        """
        key_columns = set()
        
        try:
            schema = self.indexer.load_schema()
            if 'tabelas' not in schema or table_name not in schema['tabelas']:
                return key_columns
            
            table_info = schema['tabelas'][table_name]
            
            # Extrair colunas da chave primária
            if 'primary_key' in table_info and 'columns' in table_info['primary_key']:
                key_columns.update(table_info['primary_key']['columns'])
            
            # Extrair colunas de chaves estrangeiras
            if 'foreign_keys' in table_info:
                for fk in table_info['foreign_keys']:
                    if 'columns' in fk:
                        key_columns.update(fk['columns'])
            
            # Extrair colunas de índices
            if 'indexes' in table_info:
                for idx in table_info['indexes']:
                    if 'columns' in idx:
                        key_columns.update(idx['columns'])
        
        except Exception as e:
            print(f"Aviso: Erro ao extrair colunas de chaves da tabela {table_name}: {e}")
        
        return key_columns

    def _fetch_table_samples(
        self,
        db_config: Dict[str, str],
        table_name: str,
        rag_columns: List[str],
        sample_rows: int
    ) -> Optional['pd.DataFrame']:
        """
        Busca samples do banco de dados para uma tabela específica.

        Args:
            db_config: Configuração do banco (host, port, database, user, password)
            table_name: Nome da tabela
            rag_columns: Lista de colunas selecionadas pelo RAG
            sample_rows: Quantidade de linhas para buscar

        Returns:
            DataFrame com os dados ou None em caso de erro
        """
        try:
            import pandas as pd
            from sqlalchemy import create_engine
            
            # Obter colunas de chaves/índices
            key_columns = self._get_key_columns(table_name)
            
            # Mesclar colunas do RAG com colunas de chaves (sem duplicatas)
            all_columns = []
            seen = set()
            
            # Adicionar colunas do RAG primeiro (mantendo ordem)
            for col in rag_columns:
                if col not in seen:
                    all_columns.append(col)
                    seen.add(col)
            
            # Adicionar colunas de chaves que não estão nas colunas do RAG
            for col in sorted(key_columns):
                if col not in seen:
                    all_columns.append(col)
                    seen.add(col)
            
            # Se não houver colunas, retornar None
            if not all_columns:
                return None
            
            # Criar connection string
            connection_string = (
                f"postgresql://{db_config['user']}:{db_config['password']}"
                f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
            )
            
            # Criar engine
            engine = create_engine(connection_string)
            
            # Montar query com colunas específicas
            columns_str = ', '.join(all_columns)
            query = f"SELECT {columns_str} FROM {table_name} LIMIT {sample_rows}"
            
            # Executar query
            df = pd.read_sql_query(query, engine)
            
            # Fechar engine
            engine.dispose()
            
            return df
            
        except Exception as e:
            print(f"Aviso: Não foi possível buscar samples da tabela {table_name}: {e}")
            return None

    def _format_samples_for_prompt(self, samples: Dict[str, 'pd.DataFrame']) -> str:
        """
        Formata samples do banco de dados em formato TOON para inclusão no prompt.

        Args:
            samples: Dicionário com table_name -> DataFrame

        Returns:
            String formatada com todos os samples em formato TOON
        """
        if not samples:
            return ""
        
        try:
            from toon_py import encode
            
            formatted_parts = ["## Database Samples\n"]
            
            for table_name, df in samples.items():
                if df is not None and not df.empty:
                    # Converter DataFrame para lista de dicionários
                    data_dicts = df.to_dict('records')
                    
                    # Converter para formato TOON
                    toon_data = encode(data_dicts)
                    
                    # Adicionar ao prompt
                    formatted_parts.append(f"### {table_name}")
                    formatted_parts.append(toon_data)
                    formatted_parts.append("")  # Linha em branco
            
            return "\n".join(formatted_parts)
            
        except ImportError:
            print("Aviso: Biblioteca toon-py não está instalada. Samples não serão formatados.")
            return ""
        except Exception as e:
            print(f"Aviso: Erro ao formatar samples: {e}")
            return ""

    def get_enhanced_prompt(
        self,
        question: str,
        system_template: Optional[str] = None,
        max_tables: int = 5,
        max_columns_per_table: int = 10,
        max_context_length: int = 32768,
        include_scores: bool = False,
        db_config: Optional[Dict[str, str]] = None,
        sample_rows: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Generate an enhanced prompt with RAG context.

        Args:
            question: User's natural language question
            system_template: Optional system message template
            max_tables: Maximum number of tables to include in context
            max_columns_per_table: Maximum number of columns per table
            max_context_length: Maximum context length in characters
            include_scores: Whether to include similarity scores in context
            db_config: Optional database configuration (host, port, database, user, password)
            sample_rows: Optional number of sample rows to fetch from each table

        Returns:
            Dictionary with 'system' and 'user' messages
        """
        # Get relevant context
        context = self.retriever.get_context_for_query(
            question,
            max_context_length=max_context_length,
            max_tables=max_tables,
            max_columns_per_table=max_columns_per_table,
            include_scores=include_scores
        )

        # Get relevant tables
        tables = self.retriever.retrieve_tables(question, top_k=max_tables)

        # Fetch database samples if configuration provided
        samples_section = ""
        if db_config is not None and sample_rows is not None:
            # Get columns for each table
            samples = {}
            for table_name in tables:
                # Retrieve columns for this table
                columns = self.retriever.retrieve_columns(
                    question,
                    table_name=table_name,
                    top_k=max_columns_per_table
                )
                
                # Extract column names
                rag_columns = [col['column'] for col in columns]
                
                # Fetch samples
                df = self._fetch_table_samples(
                    db_config=db_config,
                    table_name=table_name,
                    rag_columns=rag_columns,
                    sample_rows=sample_rows
                )
                
                if df is not None:
                    samples[table_name] = df
            
            # Format samples
            if samples:
                samples_section = "\n\n" + self._format_samples_for_prompt(samples)

        # Build system message
        if system_template is None:
            raise ValueError("system_template is required")

        # Add samples to context if available
        full_context = context + samples_section
        system_message = system_template.format(context=full_context)

        # Build user message with question
        user_message = f"Question: {question}"

        return {
            'system': system_message,
            'user': user_message
        }

    def analyze_question(self, question: str, include_scores: bool = False) -> Dict[str, Any]:
        """
        Analyze a question and return relevant schema information.

        Args:
            question: Natural language question
            include_scores: Whether to include scores in the generated context

        Returns:
            Dictionary with analysis results
        """
        # Retrieve relevant information
        tables = self.retriever.retrieve_tables(question, top_k=5)
        columns = self.retriever.retrieve_columns(question, top_k=10)
        guidelines = self.retriever.retrieve(
            question,
            top_k=5,
            filter_type='guideline'
        )

        return {
            'question': question,
            'relevant_tables': tables,
            'relevant_columns': columns,
            'guidelines': [
                {
                    'content': g.content,
                    'score': g.score
                }
                for g in guidelines
            ],
            'context': self.retriever.get_context_for_query(question, include_scores=include_scores)
        }

    def get_table_details(self, table_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific table.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with table details
        """
        query = f"informações sobre a tabela {table_name}"
        columns = self.retriever.retrieve_columns(
            query,
            table_name=table_name,
            top_k=50
        )

        # Get table description
        table_results = self.retriever.retrieve(
            query,
            top_k=1,
            filter_type='table'
        )

        description = ""
        if table_results:
            for result in table_results:
                if result.document.table_name == table_name:
                    description = result.content
                    break

        return {
            'table_name': table_name,
            'description': description,
            'columns': columns
        }

    def search_schema(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search the schema for relevant information.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of search results
        """
        results = self.retriever.retrieve(query, top_k=top_k)
        
        return [
            {
                'content': r.content,
                'metadata': {
                    'type': r.document.type,
                    'table_name': r.document.table_name,
                    **r.document.metadata
                },
                'score': r.score
            }
            for r in results
        ]
