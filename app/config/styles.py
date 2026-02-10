"""
Configuração de estilos CSS unificados da aplicação.

Este módulo centraliza a paleta de cores e variáveis CSS utilizadas
tanto na interface Shiny quanto nos relatórios HTML estáticos.
"""

# Paleta de cores compartilhada
COLORS = {
    "precision": "#1E40AF",
    "recall": "#047857",
    "f1": "#0E7490",
    "success_rate": "#B45309",
    "accuracy": "#7C3AED",
    "background": "#F8FAFC",
    "card_bg": "#FFFFFF",
    "text": "#1E293B",
    "text_muted": "#64748B",
    "border": "#E2E8F0",
    "success": "#059669",
    "error": "#DC2626",
    "warning": "#D97706",
}

# Cores para gráficos Plotly
PLOTLY_COLORS = [
    COLORS["precision"],
    COLORS["recall"],
    COLORS["f1"],
    COLORS["success_rate"],
]

# CSS Variables
CSS_VARIABLES = """
    :root {
        --color-precision: #1E40AF;
        --color-recall: #047857;
        --color-f1: #0E7490;
        --color-success-rate: #B45309;
        --color-accuracy: #7C3AED;
        --color-background: #F8FAFC;
        --color-card-bg: #FFFFFF;
        --color-text: #1E293B;
        --color-text-muted: #64748B;
        --color-border: #E2E8F0;
        --color-success: #059669;
        --color-error: #DC2626;
        --color-warning: #D97706;
    }
"""

# Font imports
FONT_IMPORTS = """
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
"""

# Base styles for both Shiny and HTML
BASE_STYLES = """
    body {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background-color: var(--color-background);
        color: var(--color-text);
    }
    
    /* Card Styling */
    .card {
        background-color: var(--color-card-bg);
        border: 1px solid var(--color-border);
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        margin-bottom: 1.5rem;
        overflow: hidden;
    }
    
    .card-header {
        background-color: var(--color-card-bg);
        border-bottom: 1px solid var(--color-border);
        padding: 1rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        color: var(--color-text);
    }
    
    .card-body {
        padding: 1.5rem;
    }
    
    /* Tables */
    .table {
        font-size: 0.875rem;
    }
    
    .table thead th {
        background-color: var(--color-background) !important;
        color: var(--color-text);
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        border-bottom: 2px solid var(--color-border) !important;
        padding: 0.875rem 1rem !important;
    }
    
    .table tbody td {
        padding: 0.75rem 1rem !important;
        border-bottom: 1px solid var(--color-border);
        color: var(--color-text);
    }
    
    .table-striped tbody tr:nth-of-type(odd) {
        background-color: rgba(248, 250, 252, 0.5);
    }
    
    .table-hover tbody tr:hover {
        background-color: rgba(30, 64, 175, 0.04);
    }
    
    /* SQL Code Block Styling */
    .sql-code {
        font-family: 'JetBrains Mono', 'SF Mono', 'Monaco', monospace;
        font-size: 13px;
        line-height: 1.6;
        background-color: var(--color-background);
        border: 1px solid var(--color-border);
        border-radius: 8px;
        padding: 1rem 1.25rem;
        overflow-x: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        color: var(--color-text);
    }
    
    /* Form Controls */
    .form-select, .form-control {
        border: 1px solid var(--color-border);
        border-radius: 8px;
        padding: 0.625rem 1rem;
        font-size: 0.875rem;
        color: var(--color-text);
        background-color: var(--color-card-bg);
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    
    .form-select:focus, .form-control:focus {
        border-color: var(--color-precision);
        box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1);
        outline: none;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--color-background);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--color-border);
        border-radius: 5px;
        border: 2px solid var(--color-background);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #CBD5E1;
    }
    
    * {
        scrollbar-width: thin;
        scrollbar-color: var(--color-border) var(--color-background);
    }
"""

