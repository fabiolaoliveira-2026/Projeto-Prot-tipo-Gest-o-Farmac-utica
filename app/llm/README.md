# Módulo LLM

Este módulo fornece um conjunto abrangente de ferramentas para trabalhar com Grandes Modelos de Linguagem (LLMs), focando especificamente em tarefas de Text-to-SQL. Ele abrange desde o processamento de dados e geração de prompts até o treinamento (fine-tuning), avaliação e inferência com suporte a RAG (Retrieval-Augmented Generation).

## Estrutura do Módulo

O módulo está organizado nas seguintes subpastas, cada uma com responsabilidades específicas:

- `data/`: Manipulação e preparação de dados.
- `evaluate/`: Ferramentas para cálculo de métricas e visualização de resultados.
- `model/`: Wrappers para carregar e interagir com modelos de linguagem.
- `prompt/`: Utilitários para construção e formatação de prompts.
- `rag/`: Implementação de técnicas de RAG para enriquecer o contexto do modelo com informações do esquema do banco de dados.
- `training/`: Funcionalidades para treinamento e fine-tuning de modelos.
- `utils/`: Utilitários gerais, como logging.

## Detalhamento dos Componentes

### 1. Data (`llm/data`)

Responsável pela gestão dos dados de entrada para treinamento e avaliação.

- **Splitter (`splitter.py`)**:
  - Realiza a divisão de datasets em dobras (folds) para validação cruzada (K-Fold Cross Validation).
  - Suporta múltiplos formatos de arquivo: CSV, JSON, Excel e Parquet.
  - Salva os conjuntos de treino e teste separadamente para cada fold.

### 2. Evaluate (`llm/evaluate`)

Fornece classes para avaliar a performance dos modelos gerados.

- **Evaluate (`evaluate.py`)**:
  - Calcula métricas de classificação: Acurácia, Precisão, Recall e F1-Score.
  - Gera e plota Matrizes de Confusão (Confusion Matrix).
  - Suporta a criação de painéis com múltiplas matrizes de confusão e gráficos de métricas comparativas.
  - Integração com Plotly para visualizações interativas e estáticas.

### 3. Model (`llm/model`)

Abstrai a complexidade de carregar e interagir com diferentes arquiteturas de modelos.

- **TransformerModel (`transformer.py`)**:
  - Wrapper para a biblioteca `transformers` do Hugging Face.
  - Gerencia carregamento de tokenizers e modelos (Causal LM).
  - Suporta geração de texto com templates de chat.
  - **Recurso de "Thinking Mode"**: Capaz de analisar saídas de modelos que geram cadeias de pensamento (tags `<think>`), separando o raciocínio da resposta final.

- **UnslothModel (`unsloth.py`)**:
  - (Inferido) Wrapper otimizado para modelos utilizando a biblioteca Unsloth, focado em eficiência de memória e velocidade.

### 4. Prompt (`llm/prompt`)

Padroniza a criação de prompts para diferentes famílias de modelos.

- **PromptGenerator (`generator.py`)**:
  - Factory para criar prompts formatados corretamente.
  - Suporta templates estilo **Llama** (usando tokens especiais como `<|begin_of_text|>`, `<|start_header_id|>`) e estilo **Unsloth** (formato `### Input: ... ### Response:`).

### 5. RAG (`llm/rag`)

Implementa a lógica de Recuperação Aumentada para Geração, essencial para fornecer contexto de esquema de banco de dados ao LLM.

- **Text2SQLWithRAG (`text2sql_rag.py`)**:
  - Classe principal que orquestra o processo de RAG para Text2SQL.
  - Utiliza `SchemaIndexer` para indexar metadados de tabelas e colunas.
  - Utiliza `SchemaRetriever` para buscar tabelas, colunas e diretrizes relevantes baseadas na pergunta do usuário.
  - Gera prompts enriquecidos com o contexto recuperado (DDL, descrições, exemplos similares).
  - Métodos para análise de perguntas e busca de detalhes de tabelas.

### 6. Training (`llm/training`)

Facilita o processo de fine-tuning de modelos.

- **UnslothFT (`unsloth.py`)**:
  - Gerencia o ciclo de vida do fine-tuning usando Unsloth e TRL (Transformer Reinforcement Learning).
  - Configura o modelo para PEFT (Parameter-Efficient Fine-Tuning).
  - Prepara datasets para o formato de instrução.
  - Executa o treinamento com `SFTTrainer` (Supervised Fine-Tuning Trainer).
  - Gerencia salvamento do modelo e tokenizador após o treinamento.

## Utilização Básica

### Geração de Texto

```python
from llm.model.transformer import TransformerModel

model = TransformerModel()
model.load_transformer_model("nome-do-modelo")
prompt = model.generate_prompt("Sua pergunta aqui")
resposta = model.generate(prompt, model_config={"max_new_tokens": 100})
```

### RAG para Text2SQL

```python
from llm.rag.text2sql_rag import Text2SQLWithRAG

rag = Text2SQLWithRAG(schema_path="caminho/para/schema.yaml")
prompt_context = rag.get_enhanced_prompt("Quantos usuários existem?")
# prompt_context['user'] contém a pergunta com contexto do esquema
```

### Avaliação

```python
from llm.evaluate.evaluate import Evaluate

evaluator = Evaluate(y_true=labels_reais, y_pred=labels_preditos)
metrics = evaluator.calculate_metrics()
evaluator.plot_confusion_matrix("Matriz de Confusão")
```







