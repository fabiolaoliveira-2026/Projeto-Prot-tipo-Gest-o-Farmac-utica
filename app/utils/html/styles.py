"""
Estilos CSS para relatórios HTML estáticos.

Este módulo contém os estilos CSS utilizados na geração de relatórios
HTML auto-contidos para visualização offline.
"""

HTML_STYLES = """
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    :root {
        --color-precision: #1E40AF;
        --color-recall: #047857;
        --color-f1: #0E7490;
        --color-success-rate: #B45309;
        --color-background: #F8FAFC;
        --color-card-bg: #FFFFFF;
        --color-text: #1E293B;
        --color-text-muted: #64748B;
        --color-border: #E2E8F0;
        --color-success: #059669;
        --color-error: #DC2626;
        --color-warning: #D97706;
    }
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background-color: var(--color-background);
        color: var(--color-text);
        line-height: 1.6;
        padding: 2rem;
    }
    
    .container {
        max-width: 1400px;
        margin: 0 auto;
    }
    
    header {
        background: linear-gradient(135deg, var(--color-precision) 0%, #3B82F6 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    header h1 {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    header p {
        opacity: 0.9;
        font-size: 0.95rem;
    }
    
    nav.toc {
        background: var(--color-card-bg);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid var(--color-border);
    }
    
    nav.toc h3 {
        margin-bottom: 1rem;
        font-size: 1rem;
    }
    
    nav.toc ul {
        list-style: none;
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
    }
    
    nav.toc a {
        color: var(--color-precision);
        text-decoration: none;
        padding: 0.5rem 1rem;
        background: var(--color-background);
        border-radius: 8px;
        transition: all 0.2s;
    }
    
    nav.toc a:hover {
        background: var(--color-precision);
        color: white;
    }
    
    .summary-section {
        background: var(--color-card-bg);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        border: 1px solid var(--color-border);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    
    .summary-section h2 {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: var(--color-text);
    }
    
    .summary-section p {
        margin-bottom: 0.5rem;
        color: var(--color-text-muted);
    }
    
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin-top: 1.5rem;
    }
    
    .metric-card {
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
    }
    
    .metric-card.precision { background: var(--color-precision); }
    .metric-card.recall { background: var(--color-recall); }
    .metric-card.f1 { background: var(--color-f1); }
    .metric-card.success-rate { background: var(--color-success-rate); }
    
    .metric-title {
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        opacity: 0.9;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    .charts-grid {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 2rem;
        margin-bottom: 2rem;
    }
    
    @media (max-width: 900px) {
        .charts-grid { grid-template-columns: 1fr; }
    }
    
    /* Bar Chart Styles */
    .bar-chart {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        padding: 1rem 0;
    }
    
    .bar-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .bar-label {
        width: 40px;
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--color-text-muted);
        text-align: right;
    }
    
    .bar-container {
        flex: 1;
        height: 24px;
        background: var(--color-background);
        border-radius: 4px;
        position: relative;
        overflow: hidden;
    }
    
    .bar-fill {
        height: 100%;
        background: var(--color-precision);
        border-radius: 4px;
        transition: width 0.3s ease;
        min-width: 2px;
    }
    
    .bar-value {
        position: absolute;
        right: 8px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--color-text);
    }
    
    /* Status Chart Styles */
    .status-chart {
        padding: 1rem;
    }
    
    .status-bar {
        display: flex;
        height: 40px;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 1rem;
    }
    
    .status-fill {
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 0.9rem;
        transition: width 0.3s ease;
    }
    
    .status-fill.success {
        background: var(--color-success);
    }
    
    .status-fill.error {
        background: var(--color-error);
    }
    
    .status-legend {
        display: flex;
        gap: 2rem;
        justify-content: center;
    }
    
    .status-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.9rem;
    }
    
    .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }
    
    .status-dot.success {
        background: var(--color-success);
    }
    
    .status-dot.error {
        background: var(--color-error);
    }
    
    .card {
        background: var(--color-card-bg);
        border-radius: 16px;
        border: 1px solid var(--color-border);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        margin-bottom: 2rem;
        overflow: hidden;
    }
    
    .card-header {
        background: var(--color-background);
        padding: 1rem 1.5rem;
        font-weight: 600;
        border-bottom: 1px solid var(--color-border);
    }
    
    .card-body {
        padding: 1.5rem;
    }
    
    .page-section {
        background: var(--color-card-bg);
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid var(--color-border);
        margin-bottom: 2rem;
        page-break-inside: avoid;
    }
    
    .page-section h2 {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid var(--color-border);
    }
    
    .table-container {
        overflow-x: auto;
    }
    
    .data-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.875rem;
    }
    
    .data-table th {
        background: var(--color-background);
        color: var(--color-text);
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        padding: 0.875rem 0.75rem;
        text-align: left;
        border-bottom: 2px solid var(--color-border);
        white-space: nowrap;
    }
    
    .data-table td {
        padding: 0.75rem;
        border-bottom: 1px solid var(--color-border);
        color: var(--color-text);
    }
    
    .data-table tr:nth-child(odd) {
        background: rgba(248, 250, 252, 0.5);
    }
    
    .data-table tr:hover {
        background: rgba(30, 64, 175, 0.04);
    }
    
    .center { text-align: center; }
    .success { color: var(--color-success); font-weight: 600; }
    .error { color: var(--color-error); font-weight: 600; }
    .warning { color: var(--color-warning); font-weight: 600; }
    
    .question-detail {
        background: var(--color-background);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid var(--color-border);
        page-break-inside: avoid;
    }
    
    .question-detail h3 {
        font-size: 1.1rem;
        color: var(--color-precision);
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--color-border);
    }
    
    .question-detail .intencao,
    .question-detail .tipo-dado {
        color: var(--color-text-muted);
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    
    .params-box {
        background: var(--color-card-bg);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 1px solid var(--color-border);
    }
    
    .params-box ul {
        list-style: none;
        margin-top: 0.5rem;
    }
    
    .params-box li {
        margin: 0.25rem 0;
    }
    
    .params-box code {
        background: var(--color-background);
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85em;
    }
    
    .metrics-box {
        background: var(--color-card-bg);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 1px solid var(--color-border);
    }
    
    .metrics-box h4 {
        margin-bottom: 0.75rem;
        font-size: 0.95rem;
    }
    
    .metrics-list {
        list-style: none;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 0.5rem;
    }
    
    .metrics-list li {
        font-size: 0.9rem;
    }
    
    .sql-comparison {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin: 1rem 0;
    }
    
    @media (max-width: 900px) {
        .sql-comparison { grid-template-columns: 1fr; }
    }
    
    .sql-box {
        background: var(--color-card-bg);
        border-radius: 8px;
        border: 1px solid var(--color-border);
        overflow: hidden;
    }
    
    .sql-box h4 {
        background: var(--color-background);
        padding: 0.75rem 1rem;
        font-size: 0.9rem;
        border-bottom: 1px solid var(--color-border);
    }
    
    .sql-code {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        line-height: 1.5;
        padding: 1rem;
        margin: 0;
        overflow-x: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        background: var(--color-card-bg);
    }
    
    .preview-comparison {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-top: 1rem;
    }
    
    @media (max-width: 900px) {
        .preview-comparison { grid-template-columns: 1fr; }
    }
    
    .preview-box {
        background: var(--color-card-bg);
        border-radius: 8px;
        border: 1px solid var(--color-border);
        overflow: hidden;
    }
    
    .preview-box h4 {
        background: var(--color-background);
        padding: 0.75rem 1rem;
        font-size: 0.85rem;
        border-bottom: 1px solid var(--color-border);
    }
    
    .preview-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.8rem;
    }
    
    .preview-table th {
        background: var(--color-background);
        padding: 0.5rem;
        text-align: left;
        font-weight: 600;
        font-size: 0.75rem;
        border-bottom: 1px solid var(--color-border);
    }
    
    .preview-table td {
        padding: 0.5rem;
        border-bottom: 1px solid var(--color-border);
        max-width: 200px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    footer {
        text-align: center;
        color: var(--color-text-muted);
        font-size: 0.875rem;
        padding: 2rem 0;
        border-top: 1px solid var(--color-border);
        margin-top: 2rem;
    }
    
    @media print {
        body { padding: 0; }
        .page-section, .question-detail { break-inside: avoid; }
        nav.toc { display: none; }
    }
"""

