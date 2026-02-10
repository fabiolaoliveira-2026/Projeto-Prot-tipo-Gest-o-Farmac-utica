"""
Utilitários para formatação e comparação de queries SQL.

Este módulo contém funções para formatar queries SQL para melhor legibilidade
e gerar visualizações de diff entre duas queries.
"""

import difflib

import pandas as pd
import sqlparse


def format_sql(sql: str) -> str:
    """
    Formata uma query SQL para melhor legibilidade.

    Aplica formatação padrão com indentação e palavras-chave em maiúsculo.

    Args:
        sql: Query SQL a ser formatada.

    Returns:
        Query SQL formatada.
    """
    if not sql or pd.isna(sql):
        return ""

    try:
        formatted = sqlparse.format(
            sql,
            reindent=True,
            keyword_case='upper',
            indent_width=2
        )
        return formatted.strip()
    except Exception:
        return sql.strip()


def generate_sql_diff_html(sql_gt: str, sql_model: str) -> str:
    """
    Gera HTML com diff estilo GitHub entre dois SQLs.
    
    Compara duas queries SQL e gera HTML formatado mostrando as diferenças
    com cores para adições, remoções e contexto.
    
    Args:
        sql_gt: SQL do ground truth.
        sql_model: SQL do modelo.
        
    Returns:
        HTML com o diff formatado.
    """
    gt_lines = sql_gt.splitlines(keepends=True)
    model_lines = sql_model.splitlines(keepends=True)
    
    differ = difflib.unified_diff(
        gt_lines,
        model_lines,
        fromfile='Ground Truth',
        tofile='Modelo',
        lineterm=''
    )
    
    diff_lines = list(differ)
    
    if not diff_lines:
        return '<div class="diff-identical">✅ Os SQLs são idênticos (após formatação)</div>'
    
    html_parts = ['<div class="diff-container">']
    
    for line in diff_lines:
        line_escaped = (
            line.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('\n', '')
        )
        
        if line.startswith('+++'):
            html_parts.append(f'<div class="diff-header diff-header-new">{line_escaped}</div>')
        elif line.startswith('---'):
            html_parts.append(f'<div class="diff-header diff-header-old">{line_escaped}</div>')
        elif line.startswith('@@'):
            html_parts.append(f'<div class="diff-hunk">{line_escaped}</div>')
        elif line.startswith('+'):
            html_parts.append(f'<div class="diff-add">{line_escaped}</div>')
        elif line.startswith('-'):
            html_parts.append(f'<div class="diff-remove">{line_escaped}</div>')
        else:
            html_parts.append(f'<div class="diff-context">{line_escaped}</div>')
    
    html_parts.append('</div>')
    return '\n'.join(html_parts)

