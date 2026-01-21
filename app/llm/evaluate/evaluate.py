import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.metrics import precision_score, recall_score, f1_score

class Evaluate:
    def __init__(self, y_true, y_pred):
        self.y_true = y_true
        self.y_pred = y_pred

    def _calculate_cm(self):
        cm = confusion_matrix(self.y_true, self.y_pred)
        return cm


    def calculate_metrics(self):
        precision = precision_score(self.y_true, self.y_pred)
        recall = recall_score(self.y_true, self.y_pred)
        f1 = f1_score(self.y_true, self.y_pred,)
        accuracy = (self.y_true == self.y_pred).mean()
        return {"precision": precision, "recall": recall, "f1": f1, "accuracy": accuracy}

    def plot_confusion_matrix(self, title, **kwargs):
        cm = self._calculate_cm()
        total = cm.sum()

        # Criar anotações para as células da cm com valor absoluto e percentual
        annotations = []
        for i in range(len(cm)):
            for j in range(len(cm[0])):
                valor_absoluto = cm[i][j]
                percentual = (valor_absoluto / total) * 100 if total > 0 else 0

                # Texto com valor absoluto e percentual
                texto = f"{valor_absoluto}<br>({percentual:.1f}%)"

                annotations.append(
                    dict(
                        x=j, y=i,
                        text=texto,
                        showarrow=False,
                        font=dict(color="white" if cm[i][j] > cm.max() / 2 else "black", size=16)
                    )
                )

        # Criar cm de percentuais para o hover
        cm_percentual = (cm / total * 100) if total > 0 else cm

        # Criar o heatmap
        fig = go.Figure(data=go.Heatmap(
            z=cm,
            x=['Pred: Não', 'Pred: Sim'],
            y=['GT: Não', 'GT: Sim'],
            colorscale='Blues',
            showscale=False,
            customdata=cm_percentual,
            hovertemplate='GT: %{y}<br>Pred: %{x}<br>Valor: %{z} (%{customdata:.1f}%)<extra></extra>'
        ))

        # Adicionar anotações
        fig.update_layout(
            annotations=annotations,
            title=f"{title.upper()}<br>",
            xaxis_title="Valores Preditos (Pred)",
            yaxis_title="Valores Reais (GT)",
            width=kwargs.get("width", 600),
            height=kwargs.get("height", 600)
        )

        filepath = kwargs.get("filepath")
        if filepath:
            with open(filepath, "wb") as f:
                f.write(fig.to_image(format="png"))

            with open(filepath[:-4] + ".json", "w") as f:
                cm_json = cm.tolist()
                json.dump(cm_json, f)

        return fig

    @staticmethod
    def plot_multiple_cm(cms, titles, **kwargs):
        n_categorias = len(cms)
        cols = kwargs.get("n_cols", 3)  # 3 colunas
        rows = (n_categorias + cols - 1) // cols  # Calcular número de linhas necessárias

        # Criar subplots
        fig_painel = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=[f"{cat.replace('_', ' ').title()}" for cat in titles],
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )

        # Adicionar cada matriz como um subplot
        for idx, cm in enumerate(cms):
            row = (idx // cols) + 1
            col = (idx % cols) + 1

            # Adicionar heatmap
            total_casos = cm.sum()
            # Criar matriz de percentuais para o hover
            matriz_percentual = (cm / total_casos * 100) if total_casos > 0 else cm

            fig_painel.add_trace(
                go.Heatmap(
                    z=cm,
                    x=['Pred: Não', 'Pred: Sim'],
                    y=['GT: Não', 'GT: Sim'],
                    colorscale='Blues',
                    showscale=False,
                    customdata=matriz_percentual,
                    hovertemplate='GT: %{y}<br>Pred: %{x}<br>Valor: %{z} (%{customdata:.1f}%)<extra></extra>'
                ),
                row=row, col=col
            )

            # Adicionar anotações de texto nas células com valor absoluto e percentual
            total_casos = cm.sum()
            for i in range(len(cm)):
                for j in range(len(cm[0])):
                    valor_absoluto = cm[i][j]
                    percentual = (valor_absoluto / total_casos) * 100 if total_casos > 0 else 0

                    # Texto com valor absoluto e percentual
                    texto = f"{valor_absoluto}<br>({percentual:.1f}%)"

                    fig_painel.add_annotation(
                        x=j, y=i,
                        text=texto,
                        showarrow=False,
                        font=dict(color="white" if cm[i][j] > cm.max() / 2 else "black", size=14),
                        row=row, col=col
                    )

        # Configurar layout do painel
        fig_painel.update_layout(
            title_text="Painel de Matrizes de Confusão - Todas as Categorias",
            height=1080,
            width=1920,
            showlegend=False
        )

        # Configurar eixos
        for i in range(1, rows + 1):
            for j in range(1, cols + 1):
                fig_painel.update_xaxes(showticklabels=True, row=i, col=j)
                fig_painel.update_yaxes(showticklabels=True, row=i, col=j)

        filepath = kwargs.get("filepath")
        if filepath:
            with open(filepath, "wb") as f:
                f.write(fig_painel.to_image(format="png", width=1920, height=1080))

        return fig_painel

    def plot_metrics(self, title, **kwargs):
        metrics = self.calculate_metrics()
        metricas_nomes = ['Precisão', 'Recall', 'F1-Score', 'Acurácia']
        metricas_valores = [metrics["precision"], metrics["recall"], metrics["f1"], metrics["accuracy"]]

        fig = go.Figure([go.Bar(x=metricas_nomes, y=metricas_valores, text=[f'{v:.3f}' for v in metricas_valores], textposition='auto')])

        fig.update_layout(
            title=title,
            yaxis_title='Valor da Métrica',
            width=kwargs.get("width", 800),
            height=kwargs.get("height", 500),
            template="simple_white"
        )

        filepath = kwargs.get("filepath")
        if filepath:
            with open(filepath, "wb") as f:
                f.write(fig.to_image(format="png"))

        return fig

    @staticmethod
    def plot_multiple_metrics(metrics_results, categories, title, **kwargs):
        categorias_nome = [cat.replace('_', ' ').title() for cat in categories]
        metricas_nomes = ['Acurácia', 'Precisão', 'Recall', 'F1-Score']

        dados_metricas = {
            'Acurácia': [resultado['accuracy'] for resultado in metrics_results],
            'Precisão': [resultado['precision'] for resultado in metrics_results],
            'Recall': [resultado['recall'] for resultado in metrics_results],
            'F1-Score': [resultado['f1'] for resultado in metrics_results]
        }

        fig_metricas = go.Figure()
        cores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

        for i, metrica in enumerate(metricas_nomes):
            fig_metricas.add_trace(go.Bar(
                name=metrica,
                x=categorias_nome,
                y=dados_metricas[metrica],
                marker_color=cores[i],
                text=[f'{v:.3f}' for v in dados_metricas[metrica]],
                textposition='auto',
            ))

        fig_metricas.update_layout(
            title=title,
            xaxis_title='Categoria',
            yaxis_title='Valor da Métrica',
            barmode='group',
            height=kwargs.get("height", 600),
            width=kwargs.get("width", 1200),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            template="simple_white"
        )

        if kwargs.get("add_hline"):
            fig_metricas.add_hline(
                y=0.9,
                line_dash="dash",
                line_color="red",
                annotation_text="Meta: 80%",
                annotation_position="bottom right"
            )

        filepath = kwargs.get("filepath")
        if filepath:
            with open(filepath, "wb") as f:
                f.write(fig_metricas.to_image(format="png", width=1920, height=1080))

        return fig_metricas