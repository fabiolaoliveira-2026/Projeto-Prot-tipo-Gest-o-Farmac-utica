"""
Configurações e constantes para geração de queries SQL.

Define os templates de prompt, regras de negócio padrão, modelos disponíveis
e parâmetros de configuração do RAG e geração.
"""

DEFAULT_RAG_MODEL = "neuralmind/bert-large-portuguese-cased"
DEFAULT_SIMILARITY_THRESHOLD = 0.3
DEFAULT_MAX_TABLES = 5
DEFAULT_MAX_COLUMNS_PER_TABLE = 20
DEFAULT_MAX_CONTEXT_LENGTH = 32768

DEFAULT_MODEL = "Qwen/Qwen3-32B-AWQ"
DEFAULT_MAX_NEW_TOKENS = 32768
DEFAULT_TEMPERATURE = 0.0001
DEFAULT_TOP_P = 0.95

AVAILABLE_MODELS = [
    "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "Qwen/Qwen3-4B-Thinking-2507",
    "Qwen/Qwen3-14B-FP8",
    "Qwen/Qwen3-32B-AWQ",
    "Qwen/Qwen3-8B",
    "deepseek-ai/deepseek-coder-7b-instruct-v1.5",
    "Snowflake/Arctic-Text2SQL-R1-7B",
]

DEFAULT_SYSTEM_TEMPLATE = """Você é um conversor de linguagem natural para SQL.
Sua tarefa é converter perguntas em linguagem natural em consultas SQL precisas.

Contexto do Banco de Dados:
{context}

Regras de negócio:
{business_rules}

Diretrizes Importantes:
- Sempre utilize os nomes de tabelas e colunas corretos, conforme mostrado no contexto.
- Utilize JOINs explícitos ao acessar múltiplas tabelas.
- Utilize cláusulas WHERE apropriadas para filtragem.
- Considere valores NULL em suas consultas.
- Utilize funções de agregação (SUM, COUNT, AVG) quando apropriado.
- Sempre utilize aliases para as tabelas para maior clareza.
- Quando existir operações de única coluna no select, nomeie a coluna com o nome de antes da operação.

Regras de Resposta:
1. NÃO inicie com "Aqui está o SQL" ou explicações.
2. NÃO utilize blocos de código markdown (```sql). Retorne apenas o texto cru da query.
3. NÃO inclua comentários ou notas finais.

Output esperado: Apenas a string SQL válida iniciada por SELECT.
"""

DEFAULT_BUSINESS_RULES = """## Valores não informados:
Ao ser solicitado um valor não informado, considere como 'X' para o valor.

## Definição de estoque crítico:
Estoque crítico é o nível mínimo de estoque abaixo do qual existe risco de desabastecimento.
Considera-se estoque crítico quando a cobertura é igual ou menor que 15 dias de consumo médio.

## Consumo médio mensal:
O consumo médio mensal é calculado considerando os últimos 3 meses.
"""

