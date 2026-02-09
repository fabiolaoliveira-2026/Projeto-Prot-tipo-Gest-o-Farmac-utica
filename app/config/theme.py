"""
Configuração de tema visual da aplicação.

Define a paleta de cores, estilos CSS customizados e configurações
visuais para a interface Shiny.
"""

from shiny import ui


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
}

PLOTLY_COLORS = [
    COLORS["precision"],
    COLORS["recall"],
    COLORS["f1"],
    COLORS["success_rate"],
]

custom_css = ui.tags.style("""
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
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
    }
    
    body {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background-color: var(--color-background);
        color: var(--color-text);
    }
    
    .bslib-page-sidebar {
        background-color: var(--color-background);
    }
    
    .bslib-page-sidebar > .main {
        padding: 1.5rem 2rem;
        background-color: var(--color-background);
    }
    
    /* Sidebar Styling */
    .sidebar, .bslib-sidebar-layout > .sidebar {
        background-color: var(--color-card-bg) !important;
        border-right: 1px solid var(--color-border) !important;
        padding: 1.5rem;
    }
    
    .sidebar h4 {
        font-weight: 600;
        color: var(--color-text);
        margin-bottom: 1.5rem;
        font-size: 1.1rem;
    }
    
    .sidebar p {
        color: var(--color-text-muted);
        font-size: 0.875rem;
        line-height: 1.6;
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
    
    /* Value Box Styling */
    .bslib-value-box {
        border-radius: 12px !important;
        margin-bottom: 1rem;
        border: none !important;
        overflow: hidden;
    }
    
    .bslib-value-box .value-box-area {
        padding: 1.25rem 1.5rem;
    }
    
    .bslib-value-box .value-box-value {
        font-weight: 700;
        font-size: 2rem;
        letter-spacing: -0.02em;
    }
    
    .bslib-value-box .value-box-title {
        font-weight: 500;
        font-size: 0.875rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Custom Value Box Colors */
    .value-box-precision .bslib-value-box,
    .value-box-precision .value-box-area {
        background-color: var(--color-precision) !important;
        color: #FFFFFF !important;
    }
    
    .value-box-recall .bslib-value-box,
    .value-box-recall .value-box-area {
        background-color: var(--color-recall) !important;
        color: #FFFFFF !important;
    }
    
    .value-box-f1 .bslib-value-box,
    .value-box-f1 .value-box-area {
        background-color: var(--color-f1) !important;
        color: #FFFFFF !important;
    }
    
    .value-box-success-rate .bslib-value-box,
    .value-box-success-rate .value-box-area {
        background-color: var(--color-success-rate) !important;
        color: #FFFFFF !important;
    }
    
    .value-box-precision .value-box-title,
    .value-box-precision .value-box-value,
    .value-box-recall .value-box-title,
    .value-box-recall .value-box-value,
    .value-box-f1 .value-box-title,
    .value-box-f1 .value-box-value,
    .value-box-success-rate .value-box-title,
    .value-box-success-rate .value-box-value {
        color: #FFFFFF !important;
    }
    
    /* Navigation Tabs */
    .nav-tabs {
        border-bottom: 2px solid var(--color-border);
        gap: 0.5rem;
    }
    
    .nav-tabs .nav-link {
        border: none;
        border-bottom: 2px solid transparent;
        color: var(--color-text-muted);
        font-weight: 500;
        padding: 0.75rem 1.25rem;
        margin-bottom: -2px;
        border-radius: 0;
        transition: all 0.2s ease;
    }
    
    .nav-tabs .nav-link:hover {
        color: var(--color-text);
        border-bottom-color: var(--color-border);
        background: transparent;
    }
    
    .nav-tabs .nav-link.active {
        color: var(--color-precision);
        border-bottom-color: var(--color-precision);
        background: transparent;
        font-weight: 600;
    }
    
    .navset-card-tab > .card-body {
        padding: 0;
    }
    
    .navset-card-tab .tab-content > .tab-pane {
        padding: 1.5rem;
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
    
    .form-label, .shiny-input-container > label {
        font-weight: 500;
        font-size: 0.875rem;
        color: var(--color-text);
        margin-bottom: 0.5rem;
    }
    
    .shiny-input-container {
        margin-bottom: 1.25rem;
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
    
    /* Question Title Box */
    .question-title-box {
        margin: 0 0 1.5rem 0;
        padding: 1rem 1.25rem;
        background-color: var(--color-background);
        border-radius: 8px;
        color: var(--color-text);
        border-left: 4px solid var(--color-precision);
        font-weight: 500;
    }
    
    /* Misc */
    .bslib-grid {
        gap: 1.5rem !important;
    }
    
    pre {
        margin: 0.75rem 0;
    }
    
    h4, h5 {
        margin-bottom: 1.25rem;
        font-weight: 600;
        color: var(--color-text);
    }
    
    hr {
        margin: 1.25rem 0;
        border-color: var(--color-border);
        opacity: 1;
    }
    
    /* DataGrid styling */
    .shiny-data-grid {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--color-border);
    }
    
    /* Custom Scrollbar - Clean White Style */
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
    
    ::-webkit-scrollbar-corner {
        background: var(--color-background);
    }
    
    /* Firefox scrollbar */
    * {
        scrollbar-width: thin;
        scrollbar-color: var(--color-border) var(--color-background);
    }
""")

