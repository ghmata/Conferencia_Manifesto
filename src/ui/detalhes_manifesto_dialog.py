"""
Sistema de Conferência de Manifestos - Diálogo de Detalhes
Arquivo: src/ui/detalhes_manifesto_dialog.py
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QGroupBox, QHeaderView, QTextEdit, QTabWidget,
                             QWidget, QMessageBox, QFileDialog, QToolTip)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
import csv

from src.database import (obter_manifesto, listar_volumes, obter_caixas,
                          obter_estatisticas_manifesto, obter_logs)


class DetalhesManifestoDialog(QDialog):
    """Diálogo para exibir detalhes completos de um manifesto"""
    
    def __init__(self, manifesto_id: int, parent=None):
        super().__init__(parent)
        self.manifesto_id = manifesto_id
        self.manifesto = obter_manifesto(manifesto_id)
        self.volume_ids = []  # Para armazenar os IDs dos volumes na ordem da tabela
        self.init_ui()
        self.carregar_dados()
        
    def init_ui(self):
        """Inicializa a interface"""
        self.setWindowTitle("Detalhes do Manifesto")
        self.setModal(True)
        self.setMinimumSize(1000, 600)  # Aumentado para acomodar nova coluna
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Cabeçalho
        self.criar_cabecalho(layout)
        
        # Tabs
        tabs = QTabWidget()
        
        # Tab 1: Volumes
        tab_volumes = QWidget()
        self.criar_tab_volumes(tab_volumes)
        tabs.addTab(tab_volumes, "📦 Volumes")
        
        # Tab 2: Estatísticas
        tab_stats = QWidget()
        self.criar_tab_estatisticas(tab_stats)
        tabs.addTab(tab_stats, "📊 Estatísticas")
        
        # Tab 3: Logs
        tab_logs = QWidget()
        self.criar_tab_logs(tab_logs)
        tabs.addTab(tab_logs, "📝 Histórico")
        
        layout.addWidget(tabs)
        
        # Botões
        btn_layout = QHBoxLayout()
        
        btn_exportar = QPushButton("📄 Exportar Excel")
        btn_exportar.clicked.connect(self.exportar_excel)
        btn_layout.addWidget(btn_exportar)
        
        btn_layout.addStretch()
        
        btn_fechar = QPushButton("Fechar")
        btn_fechar.clicked.connect(self.accept)
        btn_layout.addWidget(btn_fechar)
        
        layout.addLayout(btn_layout)
        
    def criar_cabecalho(self, layout):
        """Cria o cabeçalho com informações do manifesto"""
        group = QGroupBox("📋 Informações do Manifesto")
        group_layout = QVBoxLayout()
        
        # Linha 1
        linha1 = QHBoxLayout()
        
        lbl_numero = QLabel(f"<b>Nº:</b> {self.manifesto['numero_manifesto']}")
        lbl_numero.setStyleSheet("font-size: 14px;")
        lbl_numero.setTextInteractionFlags(Qt.TextSelectableByMouse)
        linha1.addWidget(lbl_numero)
        
        linha1.addStretch()
        
        lbl_data = QLabel(f"<b>Data:</b> {self.manifesto['data_manifesto']}")
        lbl_data.setStyleSheet("font-size: 14px;")
        lbl_data.setTextInteractionFlags(Qt.TextSelectableByMouse)
        linha1.addWidget(lbl_data)
        
        group_layout.addLayout(linha1)
        
        # Linha 2
        linha2 = QHBoxLayout()
        
        lbl_rota = QLabel(
            f"<b>Rota:</b> {self.manifesto['terminal_origem']} → "
            f"{self.manifesto['terminal_destino']}"
        )
        lbl_rota.setTextInteractionFlags(Qt.TextSelectableByMouse)
        linha2.addWidget(lbl_rota)
        
        linha2.addStretch()
        
        # Ajuste para não mostrar Missão e Aeronave quando forem None
        missao = self.manifesto.get('missao')
        aeronave = self.manifesto.get('aeronave')
        texto_missao = []
        
        if missao and missao != 'None':
            texto_missao.append(f"<b>Missão:</b> {missao}")
        if aeronave and aeronave != 'None':
            texto_missao.append(f"<b>Aeronave:</b> {aeronave}")
            
        if texto_missao:
            lbl_missao = QLabel(" | ".join(texto_missao))
            lbl_missao.setTextInteractionFlags(Qt.TextSelectableByMouse)
            linha2.addWidget(lbl_missao)
        
        group_layout.addLayout(linha2)
        
        # Linha 3 - Status
        linha3 = QHBoxLayout()
        
        status = self.manifesto['status']
        cor_status = {
            'TOTALMENTE RECEBIDO': '#4CAF50',
            'PARCIALMENTE RECEBIDO': '#FF9800',
            'NÃO RECEBIDO': '#f44336'
        }.get(status, '#999')
        
        lbl_status = QLabel(f"<b>Status:</b> {self._formatar_status(status)}")
        lbl_status.setStyleSheet(f"color: {cor_status}; font-size: 14px; font-weight: bold;")
        lbl_status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        linha3.addWidget(lbl_status)
        
        linha3.addStretch()
        
        if self.manifesto['data_conferencia_inicio']:
            tempo = self._calcular_tempo_conferencia()
            lbl_tempo = QLabel(f"<b>Tempo de conferência:</b> {tempo}")
            lbl_tempo.setTextInteractionFlags(Qt.TextSelectableByMouse)
            linha3.addWidget(lbl_tempo)
        
        group_layout.addLayout(linha3)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def criar_tab_volumes(self, tab):
        """Cria a tab de volumes"""
        layout = QVBoxLayout(tab)
        
        # Tabela
        self.tabela_volumes = QTableWidget()
        self.tabela_volumes.setColumnCount(9)  # Aumentado para 9 colunas
        self.tabela_volumes.setHorizontalHeaderLabels([
            "Status", "Remetente", "Destinatário", "N° Volume",
            "Caixas", "Peso", "Cubagem", "Recebido em", "Recebido por"
        ])
        
        # Configurar larguras das colunas
        header = self.tabela_volumes.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Status - reduzida
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # Remetente - reduzida
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # Destinatário - reduzida
        header.setSectionResizeMode(3, QHeaderView.Interactive)  # N° Volume - reduzida
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Caixas - reduzida
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Peso - aumentada
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Cubagem - aumentada
        header.setSectionResizeMode(7, QHeaderView.Interactive)  # Recebido em
        header.setSectionResizeMode(8, QHeaderView.Interactive)  # Recebido por - nova coluna
        
        # Definir larguras iniciais - AJUSTES AQUI
        self.tabela_volumes.setColumnWidth(0, 50)   # Status
        self.tabela_volumes.setColumnWidth(1, 140)  # Remetente (REDUZIDA: 170 - 15 = 155px)
        self.tabela_volumes.setColumnWidth(2, 95)  # Destinatário
        self.tabela_volumes.setColumnWidth(3, 150)  # N° Volume
        self.tabela_volumes.setColumnWidth(4, 80)   # Caixas
        self.tabela_volumes.setColumnWidth(5, 100)  # Peso (AUMENTADA: 90 + 10 = 100px)
        self.tabela_volumes.setColumnWidth(6, 90)   # Cubagem
        self.tabela_volumes.setColumnWidth(7, 105)  # Recebido em
        self.tabela_volumes.setColumnWidth(8, 140)  # Recebido por
        
        # Permitir seleção de texto nas células
        self.tabela_volumes.setSelectionBehavior(QTableWidget.SelectItems)
        self.tabela_volumes.setSelectionMode(QTableWidget.ContiguousSelection)
        self.tabela_volumes.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela_volumes.setAlternatingRowColors(True)
        
        self.tabela_volumes.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                selection-background-color: #b3d9ff;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Conectar o clique na tabela
        self.tabela_volumes.cellClicked.connect(self.on_volume_clicked)
        
        layout.addWidget(self.tabela_volumes)
        
    def criar_tab_estatisticas(self, tab):
        """Cria a tab de estatísticas"""
        layout = QVBoxLayout(tab)
        
        self.lbl_estatisticas = QLabel()
        self.lbl_estatisticas.setStyleSheet("""
            padding: 20px;
            background-color: #f5f5f5;
            border-radius: 5px;
            font-size: 13px;
        """)
        self.lbl_estatisticas.setAlignment(Qt.AlignTop)
        self.lbl_estatisticas.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        layout.addWidget(self.lbl_estatisticas)
        
    def criar_tab_logs(self, tab):
        """Cria a tab de logs"""
        layout = QVBoxLayout(tab)
        
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setStyleSheet("""
            font-family: 'Courier New', monospace;
            font-size: 11px;
        """)
        # Permitir seleção e cópia
        self.txt_logs.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        
        layout.addWidget(self.txt_logs)
        
    def carregar_dados(self):
        """Carrega todos os dados do manifesto"""
        self.carregar_volumes()
        self.carregar_estatisticas()
        self.carregar_logs()
        
    def carregar_volumes(self):
        """Carrega a lista de volumes"""
        volumes = listar_volumes(self.manifesto_id)
        self.volume_ids = []  # Resetar a lista de IDs
        
        self.tabela_volumes.setRowCount(len(volumes))
        
        for i, volume in enumerate(volumes):
            # Armazenar o ID do volume para referência
            self.volume_ids.append(volume['id'])
            
            # Status
            status = volume['status']
            emoji = {
                'COMPLETO': '✅',
                'PARCIAL': '⚠️',
                'NÃO RECEBIDO': '❌',
                'VOLUME EXTRA': '➕'
            }.get(status, '❓')
            
            item_status = QTableWidgetItem(emoji)
            item_status.setTextAlignment(Qt.AlignCenter)
            
            # Cores PARA TODA A LINHA
            if status == 'COMPLETO':
                cor = QColor(144, 238, 144)  # Verde claro
            elif status == 'PARCIAL':
                cor = QColor(255, 255, 153)  # Amarelo claro
            elif status == 'VOLUME EXTRA':
                cor = QColor(255, 223, 186)  # Laranja claro
            else:
                cor = QColor(255, 182, 193)  # Vermelho claro
            
            item_status.setBackground(cor)
            self.tabela_volumes.setItem(i, 0, item_status)
            
            # Remetente
            item_remetente = QTableWidgetItem(volume['remetente'])
            item_remetente.setTextAlignment(Qt.AlignCenter)
            item_remetente.setBackground(cor)
            self.tabela_volumes.setItem(i, 1, item_remetente)
            
            # Destinatário
            item_destinatario = QTableWidgetItem(volume['destinatario'])
            item_destinatario.setTextAlignment(Qt.AlignCenter)
            item_destinatario.setBackground(cor)
            self.tabela_volumes.setItem(i, 2, item_destinatario)
            
            # N° Volume (COMPLETO - sem truncar)
            num_vol = volume['numero_volume']
            item_vol = QTableWidgetItem(num_vol)
            item_vol.setTextAlignment(Qt.AlignCenter)
            item_vol.setBackground(cor)
            self.tabela_volumes.setItem(i, 3, item_vol)
            
            # Caixas (sem os 3 pontos e sem indicador visual)
            caixas_texto = f"{volume['quantidade_recebida']}/{volume['quantidade_expedida']}"
            
            item_caixas = QTableWidgetItem(caixas_texto)
            item_caixas.setTextAlignment(Qt.AlignCenter)
            item_caixas.setBackground(cor)
            
            # Adicionar tooltip para mostrar números das caixas quando houver mais de uma
            if volume['quantidade_expedida'] > 1:
                caixas = obter_caixas(volume['id'])
                if caixas:
                    # CORREÇÃO: Converter números para string antes do join
                    caixas_recebidas = [str(c['numero_caixa']) for c in caixas if c.get('status') == 'RECEBIDA']
                    if caixas_recebidas:
                        tooltip_text = f"Caixas recebidas: {', '.join(caixas_recebidas)}"
                        item_caixas.setToolTip(tooltip_text)
            
            self.tabela_volumes.setItem(i, 4, item_caixas)
            
            # Peso
            peso = f"{volume['peso_total']} kg" if volume['peso_total'] else "N/A"
            item_peso = QTableWidgetItem(peso)
            item_peso.setTextAlignment(Qt.AlignCenter)
            item_peso.setBackground(cor)
            self.tabela_volumes.setItem(i, 5, item_peso)
            
            # Cubagem
            cubagem = f"{volume['cubagem']} m³" if volume['cubagem'] else "N/A"
            item_cubagem = QTableWidgetItem(cubagem)
            item_cubagem.setTextAlignment(Qt.AlignCenter)
            item_cubagem.setBackground(cor)
            self.tabela_volumes.setItem(i, 6, item_cubagem)
            
            # Recebido em - formato dd/mm/aa
            if volume['data_hora_primeira_recepcao']:
                try:
                    data_obj = datetime.fromisoformat(volume['data_hora_primeira_recepcao'].replace('Z', '+00:00'))
                    data_rec = data_obj.strftime('%d/%m/%y')
                    
                    if volume['data_hora_ultima_recepcao'] != volume['data_hora_primeira_recepcao']:
                        data_ultima = datetime.fromisoformat(volume['data_hora_ultima_recepcao'].replace('Z', '+00:00'))
                        data_rec += f"\n(última: {data_ultima.strftime('%d/%m/%y')})"
                except:
                    data_rec = volume['data_hora_primeira_recepcao'][:10]
            else:
                data_rec = "Não recebido"
            
            item_recebido = QTableWidgetItem(data_rec)
            item_recebido.setTextAlignment(Qt.AlignCenter)
            item_recebido.setBackground(cor)
            self.tabela_volumes.setItem(i, 7, item_recebido)
            
            # Recebido por - Nova coluna
            recebido_por = volume.get('usuario_recepcao', 'N/A')
            item_recebido_por = QTableWidgetItem(recebido_por)
            item_recebido_por.setTextAlignment(Qt.AlignCenter)
            item_recebido_por.setBackground(cor)
            self.tabela_volumes.setItem(i, 8, item_recebido_por)
        
    def on_volume_clicked(self, row, column):
        """Trata o clique em uma linha da tabela de volumes"""
        if row < 0 or row >= len(self.volume_ids):
            return
            
        volume_id = self.volume_ids[row]
        volume = listar_volumes(self.manifesto_id)[row]
        
        # Verificar se o volume tem mais de uma caixa
        if volume['quantidade_expedida'] > 1:
            caixas = obter_caixas(volume_id)
            if caixas:
                # CORREÇÃO: Converter números para string antes do join
                caixas_recebidas = [str(c['numero_caixa']) for c in caixas if c.get('status') == 'RECEBIDA']
                caixas_faltantes = [str(c['numero_caixa']) for c in caixas if c.get('status') != 'RECEBIDA']
                
                mensagem = f"Volume: {volume['numero_volume']}\n\n"
                
                if caixas_recebidas:
                    mensagem += f"✅ Caixas recebidas ({len(caixas_recebidas)}):\n{', '.join(caixas_recebidas)}\n\n"
                else:
                    mensagem += "❌ Nenhuma caixa recebida\n\n"
                    
                if caixas_faltantes:
                    mensagem += f"❌ Caixas faltantes ({len(caixas_faltantes)}):\n{', '.join(caixas_faltantes)}"
                else:
                    mensagem += "✅ Todas as caixas recebidas"
                
                QMessageBox.information(self, "Detalhes das Caixas", mensagem)
        
    def carregar_estatisticas(self):
        """Carrega as estatísticas do manifesto"""
        stats = obter_estatisticas_manifesto(self.manifesto_id)
        
        total_vol = stats['total_volumes'] or 0
        exp = stats['total_caixas_expedidas'] or 0
        rec = stats['total_caixas_recebidas'] or 0
        perc = stats['percentual_recebido']
        
        completos = stats['volumes_completos'] or 0
        parciais = stats['volumes_parciais'] or 0
        nao_rec = stats['volumes_nao_recebidos'] or 0
        
        peso_total = stats['peso_total'] or 0
        
        texto = f"""
<h2>📊 RESUMO GERAL</h2>

<b>Total de volumes únicos:</b> {total_vol}<br>
<b>Total de caixas esperadas:</b> {exp}<br>
<b>Caixas recebidas:</b> {rec} ({perc:.1f}%)<br>
<b>Caixas faltantes:</b> {exp - rec}<br>
<b>Peso total:</b> {peso_total:.2f} kg<br>

<hr>

<h3>📦 DETALHAMENTO POR STATUS</h3>

<b style="color: #4CAF50;">✅ Volumes Completos:</b> {completos} ({completos/total_vol*100:.1f}% dos volumes)<br>
<b style="color: #FF9800;">⚠️ Volumes Parciais:</b> {parciais} ({parciais/total_vol*100:.1f}% dos volumes)<br>
<b style="color: #f44336;">❌ Volumes Não Recebidos:</b> {nao_rec} ({nao_rec/total_vol*100:.1f}% dos volumes)<br>

<hr>

<h3>⏱️ INFORMAÇÕES DE CONFERÊNCIA</h3>

<b>Responsável:</b> {self.manifesto.get('usuario_responsavel', 'N/A')}<br>
"""
        
        if self.manifesto['data_conferencia_inicio']:
            texto += f"<b>Início:</b> {self.manifesto['data_conferencia_inicio'][:16]}<br>"
        
        if self.manifesto['data_conferencia_fim']:
            texto += f"<b>Fim:</b> {self.manifesto['data_conferencia_fim'][:16]}<br>"
            texto += f"<b>Duração:</b> {self._calcular_tempo_conferencia()}<br>"
        
        self.lbl_estatisticas.setText(texto)
        
    def carregar_logs(self):
        """Carrega o histórico de logs"""
        logs = obter_logs(self.manifesto_id)
        
        if not logs:
            self.txt_logs.setText("Nenhum log registrado.")
            return
        
        texto = "=" * 80 + "\n"
        texto += "HISTÓRICO DE AÇÕES DO MANIFESTO\n"
        texto += "=" * 80 + "\n\n"
        
        for log in logs:
            timestamp = log['timestamp'][:19]
            acao = log['acao']
            usuario = log['usuario'] or 'Sistema'
            detalhes = log['detalhes'] or ''
            
            texto += f"[{timestamp}] {usuario}\n"
            texto += f"  AÇÃO: {acao}\n"
            if detalhes:
                texto += f"  DETALHES: {detalhes}\n"
            texto += "\n" + "-" * 80 + "\n\n"
        
        self.txt_logs.setText(texto)
        
    def exportar_excel(self):
        """Exporta os dados para CSV (Excel)"""
        arquivo, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Relatório",
            f"manifesto_{self.manifesto['numero_manifesto']}.csv",
            "CSV Files (*.csv)"
        )
        
        if not arquivo:
            return
        
        try:
            volumes = listar_volumes(self.manifesto_id)
            
            with open(arquivo, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                
                # Cabeçalho do manifesto
                writer.writerow(['MANIFESTO', self.manifesto['numero_manifesto']])
                writer.writerow(['Data', self.manifesto['data_manifesto']])
                writer.writerow(['Origem', self.manifesto['terminal_origem']])
                writer.writerow(['Destino', self.manifesto['terminal_destino']])
                writer.writerow(['Status', self.manifesto['status']])
                writer.writerow([])
                
                # Cabeçalho dos volumes
                writer.writerow([
                    'Status', 'Remetente', 'Destinatário', 'N° Volume',
                    'Qtd Expedida', 'Qtd Recebida', 'Peso (kg)', 'Cubagem (m³)',
                    'Prioridade', 'Data Recebimento', 'Recebido por'  # Adicionado Recebido por
                ])
                
                # Dados dos volumes
                for volume in volumes:
                    writer.writerow([
                        volume['status'],
                        volume['remetente'],
                        volume['destinatario'],
                        volume['numero_volume'],
                        volume['quantidade_expedida'],
                        volume['quantidade_recebida'],
                        volume['peso_total'] or '',
                        volume['cubagem'] or '',
                        volume['prioridade'] or '',
                        volume['data_hora_primeira_recepcao'] or '',
                        volume.get('usuario_recepcao', '')  # Adicionado Recebido por
                    ])
            
            QMessageBox.information(
                self,
                "Sucesso",
                f"Relatório exportado com sucesso!\n{arquivo}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao exportar relatório:\n{str(e)}"
            )
    
    def _formatar_status(self, status: str) -> str:
        """Formata o status para exibição"""
        emojis = {
            'TOTALMENTE RECEBIDO': '✅',
            'PARCIALMENTE RECEBIDO': '⚠️',
            'NÃO RECEBIDO': '❌'
        }
        emoji = emojis.get(status, '❓')
        return f"{emoji} {status}"
    
    def _calcular_tempo_conferencia(self) -> str:
        """Calcula o tempo de duração da conferência"""
        if not self.manifesto['data_conferencia_inicio']:
            return "N/A"
        
        inicio = datetime.fromisoformat(self.manifesto['data_conferencia_inicio'])
        
        if self.manifesto['data_conferencia_fim']:
            fim = datetime.fromisoformat(self.manifesto['data_conferencia_fim'])
        else:
            fim = datetime.now()
        
        duracao = fim - inicio
        
        horas = int(duracao.total_seconds() // 3600)
        minutos = int((duracao.total_seconds() % 3600) // 60)
        segundos = int(duracao.total_seconds() % 60)
        
        if horas > 0:
            return f"{horas}h {minutos}min {segundos}s"
        elif minutos > 0:
            return f"{minutos}min {segundos}s"
        else:
            return f"{segundos}s"