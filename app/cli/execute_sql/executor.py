"""
Módulo de execução de queries SQL em banco PostgreSQL.

Fornece funções para conexão com banco de dados e execução segura
de queries SQL com tratamento de erros.
"""

import os
from typing import Optional
from urllib.parse import quote

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def get_db_config(yaml_config: Optional[dict] = None) -> dict[str, str]:
    """
    Carrega configuração de conexão do banco.

    Prioridade: variáveis de ambiente > YAML > valores padrão.

    Args:
        yaml_config: Configuração YAML opcional com seção 'database'.

    Returns:
        Dicionário com configurações de conexão (host, port, database, user, password).
    """
    yaml_db = {}
    if yaml_config and "database" in yaml_config:
        yaml_db = yaml_config["database"]

    return {
        "host": os.getenv("DB_HOST") or yaml_db.get("host", "localhost"),
        "port": os.getenv("DB_PORT") or yaml_db.get("port", "5432"),
        "database": os.getenv("DB_NAME") or yaml_db.get("name", ""),
        "user": os.getenv("DB_USER") or yaml_db.get("user", "postgres"),
        "password": os.getenv("DB_PASSWORD") or yaml_db.get("password", ""),
    }


def create_connection_string(config: dict[str, str]) -> str:
    """
    Cria string de conexão PostgreSQL a partir de configuração.

    Args:
        config: Dicionário com host, port, database, user, password.

    Returns:
        String de conexão no formato postgresql://user:password@host:port/database.
    """
    return (
        f"postgresql://{config['user']}:{quote(config['password'])}"
        f"@{config['host']}:{config['port']}/{config['database']}"
    )


def execute_query(
    query: str,
    db_config: Optional[dict[str, str]] = None,
    timeout: Optional[int] = None,
) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Executa uma query SQL no banco de dados PostgreSQL.

    Args:
        query: Query SQL a ser executada.
        db_config: Configuração de conexão (usa env vars se None).
        timeout: Timeout em segundos para execução da query (None = sem limite).

    Returns:
        Tupla (DataFrame com resultados, None) em sucesso ou (None, mensagem de erro) em falha.
    """
    if db_config is None:
        db_config = get_db_config()

    engine: Optional[Engine] = None

    try:
        connection_string = create_connection_string(db_config)

        connect_args = {}
        if timeout:
            connect_args["options"] = f"-c statement_timeout={timeout * 1000}"

        engine = create_engine(connection_string, connect_args=connect_args)

        safe_query = query.replace("%", "%%") if "%" in query else query

        df_result = pd.read_sql_query(safe_query, engine)

        return df_result, None

    except Exception as e:
        return None, str(e)

    finally:
        if engine:
            engine.dispose()


def test_connection(db_config: dict[str, str]) -> tuple[bool, str]:
    """
    Testa a conexão com o banco de dados.

    Args:
        db_config: Configuração de conexão.

    Returns:
        Tupla (True, mensagem de sucesso) ou (False, mensagem de erro).
    """
    engine: Optional[Engine] = None

    try:
        connection_string = create_connection_string(db_config)
        engine = create_engine(connection_string)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return True, "Conexão estabelecida com sucesso"

    except Exception as e:
        return False, str(e)

    finally:
        if engine:
            engine.dispose()

