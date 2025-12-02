"""
Sistema de Conferência de Manifestos - Janela de Busca Avançada
Arquivo: src/ui/busca_window.py
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QTabWidget, QHeaderView,
                             QMessageBox, QDateEdit, QComboBox, QFormLayout,
                             QGroupBox, QCheckBox, QDialog, QDialogButtonBox, QSpinBox, QApplication)
from PyQt5.QtCore import QDate, Qt, pyqtSignal  # ADICIONADO: pyqtSignal
from PyQt5.QtGui import QFont, QColor
import sys
import os

# Adiciona o diretório pai ao path para importações
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import (listar_manifestos, listar_volumes, obter_manifesto, 
                       marcar_volume_recebido, obter_caixas, marcar_caixa_recebida,
                       iniciar_conferencia, finalizar_conferencia, obter_volume)


class BuscaWindow(QMainWindow):
    """Janela para busca avançada de manifestos e volumes"""
    
    # ADICIONADO: Sinal para notificar quando volumes são recebidos
    volume_recebido = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.conferencia_windows = {}  # Dicionário para controlar janelas abertas
        self.init_ui()
        
    def init_ui(self):
        """Inicializa a interface"""
        self.setWindowTitle("🔍 Busca Avançada - Sistema de Manifestos")
        self.setGeometry(200, 200, 1200, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        titulo = QLabel("🔍 Busca Avançada")
        titulo_font = QFont()
        titulo_font.setPointSize(16)
        titulo_font.setBold(True)
        titulo.setFont(titulo_font)
        layout.addWidget(titulo)
        
        # Tabs
        tabs = QTabWidget()
        
        # Tab 1: Busca de Manifestos
        tab_manifestos = QWidget()
        self.criar_tab_manifestos(tab_manifestos)
        tabs.addTab(tab_manifestos, "📋 Buscar Manifestos")
        
        # Tab 2: Busca de Volumes
        tab_volumes = QWidget()
        self.criar_tab_volumes(tab_volumes)
        tabs.addTab(tab_volumes, "📦 Buscar Volumes")
        
        layout.addWidget(tabs)
        
    def criar_tab_manifestos(self, tab):
        """Cria a tab de busca de manifestos"""
        layout = QVBoxLayout(tab)
        
        # Grupo de filtros
        group_filtros = QGroupBox("Filtros de Busca")
        form_layout = QFormLayout()
        
        # Número do manifesto
        self.txt_numero_manifesto = QLineEdit()
        self.txt_numero_manifesto.setPlaceholderText("Ex: 202531000635")
        form_layout.addRow("Número do Manifesto:", self.txt_numero_manifesto)
        
        # Período de datas
        datas_layout = QHBoxLayout()
        
        self.date_inicio = QDateEdit()
        self.date_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.date_inicio.setCalendarPopup(True)
        datas_layout.addWidget(QLabel("De:"))
        datas_layout.addWidget(self.date_inicio)
        
        self.date_fim = QDateEdit()
        self.date_fim.setDate(QDate.currentDate())
        self.date_fim.setCalendarPopup(True)
        datas_layout.addWidget(QLabel("Até:"))
        datas_layout.addWidget(self.date_fim)
        
        form_layout.addRow("Período:", datas_layout)
        
        # Status
        self.cmb_status = QComboBox()
        self.cmb_status.addItem("Todos os status", "")
        self.cmb_status.addItem("✅ TOTALMENTE RECEBIDO", "TOTALMENTE RECEBIDO")
        self.cmb_status.addItem("⚠️ PARCIALMENTE RECEBIDO", "PARCIALMENTE RECEBIDO")
        self.cmb_status.addItem("❌ NÃO RECEBIDO", "NÃO RECEBIDO")
        form_layout.addRow("Status:", self.cmb_status)
        
        # Terminal de destino
        self.txt_destino = QLineEdit()
        self.txt_destino.setPlaceholderText("Ex: PCAN-LS")
        form_layout.addRow("Destino:", self.txt_destino)
        
        group_filtros.setLayout(form_layout)
        layout.addWidget(group_filtros)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        
        btn_limpar = QPushButton("🗑️ Limpar Filtros")
        btn_limpar.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        btn_limpar.clicked.connect(self.limpar_filtros_manifestos)
        btn_layout.addWidget(btn_limpar)
        
        btn_layout.addStretch()
        
        btn_buscar = QPushButton("🔍 Buscar Manifestos")
        btn_buscar.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        btn_buscar.clicked.connect(self.buscar_manifestos)
        btn_layout.addWidget(btn_buscar)
        
        layout.addLayout(btn_layout)
        
        # Tabela de resultados
        self.tabela_manifestos = QTableWidget()
        self.tabela_manifestos.setColumnCount(7)
        self.tabela_manifestos.setHorizontalHeaderLabels([
            "Nº Manifesto", "Data", "Destino", "Status", 
            "Volumes", "Caixas (Rec/Exp)", "Ações"
        ])
        
        # Configurar header
        header = self.tabela_manifestos.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.Stretch)
            # Definir largura específica para a coluna Ações
            header.setSectionResizeMode(6, QHeaderView.Fixed)
            self.tabela_manifestos.setColumnWidth(6, 180)  # Aumentar largura da coluna Ações
        
        # Aumentar altura padrão das linhas
        self.tabela_manifestos.verticalHeader().setDefaultSectionSize(60)  # Aumentado de 50 para 60
        
        # Permitir seleção de texto nas células
        self.tabela_manifestos.setSelectionBehavior(QTableWidget.SelectItems)
        self.tabela_manifestos.setSelectionMode(QTableWidget.ContiguousSelection)
        self.tabela_manifestos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela_manifestos.setAlternatingRowColors(True)
        
        self.tabela_manifestos.setStyleSheet("""
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

        layout.addWidget(self.tabela_manifestos)
        
        # Estatísticas da busca
        self.lbl_stats_manifestos = QLabel("Use os filtros acima para buscar manifestos")
        self.lbl_stats_manifestos.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.lbl_stats_manifestos)
        
    def criar_tab_volumes(self, tab):
        """Cria a tab de busca de volumes"""
        layout = QVBoxLayout(tab)
        
        # Grupo de busca
        group_busca = QGroupBox("Buscar Volume por Número")
        form_layout = QFormLayout()
        
        # Número do volume
        self.txt_numero_volume = QLineEdit()
        self.txt_numero_volume.setPlaceholderText("Digite parte ou todo o número do volume (Ex: 251381004311)")
        self.txt_numero_volume.textChanged.connect(self.buscar_volumes_em_tempo_real)
        form_layout.addRow("Número do Volume:", self.txt_numero_volume)
        
        # Checkbox para busca em tempo real
        self.chk_tempo_real = QCheckBox("Buscar automaticamente ao digitar")
        self.chk_tempo_real.setChecked(True)
        form_layout.addRow("", self.chk_tempo_real)
        
        group_busca.setLayout(form_layout)
        layout.addWidget(group_busca)
        
        # Botão de busca manual (caso tempo real esteja desativado)
        btn_buscar_manual = QPushButton("🔍 Buscar Volumes")
        btn_buscar_manual.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_buscar_manual.clicked.connect(self.buscar_volumes)
        layout.addWidget(btn_buscar_manual)
        
        # Tabela de resultados
        self.tabela_volumes = QTableWidget()
        self.tabela_volumes.setColumnCount(8)
        self.tabela_volumes.setHorizontalHeaderLabels([
            "Nº Volume", "Remetente", "Destinatário", "Nº Manifesto",
            "Data", "Status Volume", "Caixas", "Ações"
        ])
        
        # Configurar header
        header = self.tabela_volumes.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.Stretch)
            # Definir largura específica para a coluna Ações
            header.setSectionResizeMode(7, QHeaderView.Fixed)
            self.tabela_volumes.setColumnWidth(7, 200)  # Aumentar largura da coluna Ações
        
        # Aumentar altura padrão das linhas
        self.tabela_volumes.verticalHeader().setDefaultSectionSize(60)  # Aumentado de 50 para 60
        
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
        
        layout.addWidget(self.tabela_volumes)
        
        # Estatísticas da busca
        self.lbl_stats_volumes = QLabel("Digite o número do volume para buscar")
        self.lbl_stats_volumes.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.lbl_stats_volumes)
        
    def criar_acoes_manifesto(self, manifesto_id):
        """Cria os botões de ação para um manifesto"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        btn_detalhes = QPushButton("Ver\nDetalhes")
        btn_detalhes.setToolTip("Ver detalhes")
        btn_detalhes.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px;
                min-width: 30px;  /* Aumentado de 25px para 30px */
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        btn_detalhes.clicked.connect(lambda: self.ver_detalhes_manifesto(manifesto_id))
        
        btn_conferir = QPushButton("Conferir\nManifesto")
        btn_conferir.setToolTip("Iniciar conferência")
        btn_conferir.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px;
                min-width: 30px;  /* Aumentado de 25px para 30px */
            }
            QPushButton:hover {
                background-color: #3d8b40;
            }
        """)
        btn_conferir.clicked.connect(lambda: self.iniciar_conferencia_manifesto(manifesto_id))
        
        layout.addWidget(btn_detalhes)
        layout.addWidget(btn_conferir)
        
        widget.setLayout(layout)
        return widget
        
    def criar_acoes_volume(self, volume_id, quantidade_expedida, quantidade_recebida, manifesto_id):
        """Cria os botões de ação para um volume"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        btn_detalhes = QPushButton("Ver\nDetalhes")
        btn_detalhes.setToolTip("Ver detalhes")
        btn_detalhes.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px;
                min-width: 30px;  /* Aumentado de 25px para 30px */
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        btn_detalhes.clicked.connect(lambda: self.ver_detalhes_volume(volume_id))
        
        btn_conferir = QPushButton("Conferir\nManifesto")
        btn_conferir.setToolTip("Iniciar conferência")
        btn_conferir.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px;
                min-width: 30px;  /* Aumentado de 25px para 30px */
            }
            QPushButton:hover {
                background-color: #3d8b40;
            }
        """)
        btn_conferir.clicked.connect(lambda: self.abrir_conferencia(manifesto_id))
        
        btn_receber = QPushButton("Receber\nVolume")
        btn_receber.setToolTip("Receber volume")
        btn_receber.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px;
                min-width: 30px;  /* Aumentado de 25px para 30px */
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        btn_receber.clicked.connect(lambda: self.receber_volume_direto(volume_id, manifesto_id, quantidade_expedida))
        
        layout.addWidget(btn_detalhes)
        layout.addWidget(btn_conferir)
        layout.addWidget(btn_receber)
        
        widget.setLayout(layout)
        return widget
        
    def limpar_filtros_manifestos(self):
        """Limpa todos os filtros de manifestos"""
        self.txt_numero_manifesto.clear()
        self.date_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.date_fim.setDate(QDate.currentDate())
        self.cmb_status.setCurrentIndex(0)
        self.txt_destino.clear()
        
    def buscar_manifestos(self):
        """Busca manifestos com os filtros aplicados - VERSÃO SIMPLIFICADA E FUNCIONAL"""
        try:
            # Obter TODOS os manifestos primeiro
            todos_manifestos = listar_manifestos()
            
            if not todos_manifestos:
                self.tabela_manifestos.setRowCount(0)
                self.lbl_stats_manifestos.setText("❌ Nenhum manifesto encontrado no sistema")
                return
            
            # Aplicar filtros manualmente
            manifestos_filtrados = []
            
            for manifesto in todos_manifestos:
                if self._manifesto_atende_filtros(manifesto):
                    manifestos_filtrados.append(manifesto)
            
            # Preencher tabela com resultados
            self._preencher_tabela_manifestos(manifestos_filtrados)
            
            # Atualizar estatísticas
            if len(manifestos_filtrados) == 0:
                self.lbl_stats_manifestos.setText("❌ Nenhum manifesto encontrado com os filtros aplicados")
            else:
                self.lbl_stats_manifestos.setText(
                    f"✅ Encontrados {len(manifestos_filtrados)} manifesto(s)"
                )
            
        except Exception as e:
            print(f"ERRO na busca de manifestos: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            QMessageBox.critical(
                self,
                "Erro na Busca",
                f"Erro ao buscar manifestos:\n{str(e)}"
            )
    
    def _manifesto_atende_filtros(self, manifesto):
        """Verifica se um manifesto atende a todos os filtros aplicados"""
        # Filtro por número do manifesto
        numero_filtro = self.txt_numero_manifesto.text().strip()
        if numero_filtro:
            numero_manifesto = manifesto.get('numero_manifesto', '')
            if not numero_manifesto or numero_filtro not in numero_manifesto:
                return False
        
        # Filtro por status
        status_filtro = self.cmb_status.currentData()
        if status_filtro:  # Se não for string vazia
            status_manifesto = manifesto.get('status', '')
            if status_filtro != status_manifesto:
                return False
        
        # Filtro por destino
        destino_filtro = self.txt_destino.text().strip()
        if destino_filtro:
            destino_manifesto = manifesto.get('terminal_destino', '')
            if not destino_manifesto or destino_filtro.upper() not in destino_manifesto.upper():
                return False
        
        # Filtro por data
        data_inicio = self.date_inicio.date().toString("yyyy-MM-dd")
        data_fim = self.date_fim.date().toString("yyyy-MM-dd")
        data_manifesto = manifesto.get('data_manifesto', '')
        
        if data_manifesto:
            # Converter data do manifesto para formato comparável
            try:
                # Supondo que a data do manifesto está no formato DD/MM/YYYY
                partes = data_manifesto.split('/')
                if len(partes) == 3:
                    dia, mes, ano = partes
                    data_manifesto_sql = f"{ano}-{mes}-{dia}"
                    
                    if data_inicio and data_manifesto_sql < data_inicio:
                        return False
                    if data_fim and data_manifesto_sql > data_fim:
                        return False
            except:
                # Se houver erro na conversão, ignora o filtro de data
                pass
        
        return True
    
    def _preencher_tabela_manifestos(self, manifestos):
        """Preenche a tabela com a lista de manifestos"""
        self.tabela_manifestos.setRowCount(len(manifestos))
        
        for i, manifesto in enumerate(manifestos):
            # Aumentar altura específica da linha (opcional, já temos altura padrão)
            self.tabela_manifestos.setRowHeight(i, 60)  # Aumentado de 50 para 60
            
            # Nº Manifesto
            item_numero = QTableWidgetItem(manifesto['numero_manifesto'] or "N/A")
            item_numero.setTextAlignment(Qt.AlignCenter)
            self.tabela_manifestos.setItem(i, 0, item_numero)
            
            # Data
            data = manifesto['data_manifesto'] or "N/A"
            item_data = QTableWidgetItem(data)
            item_data.setTextAlignment(Qt.AlignCenter)
            self.tabela_manifestos.setItem(i, 1, item_data)
            
            # Destino
            item_destino = QTableWidgetItem(manifesto['terminal_destino'] or "N/A")
            item_destino.setTextAlignment(Qt.AlignCenter)
            self.tabela_manifestos.setItem(i, 2, item_destino)
            
            # Status
            status_manifesto = manifesto['status']
            item_status = QTableWidgetItem(self._formatar_status_manifesto(status_manifesto))
            item_status.setTextAlignment(Qt.AlignCenter)
            
            if status_manifesto == 'TOTALMENTE RECEBIDO':
                item_status.setBackground(QColor(76, 175, 80, 50))
            elif status_manifesto == 'PARCIALMENTE RECEBIDO':
                item_status.setBackground(QColor(255, 193, 7, 50))
            else:
                item_status.setBackground(QColor(244, 67, 54, 50))
            
            self.tabela_manifestos.setItem(i, 3, item_status)
            
            # Volumes
            total_vol = manifesto.get('total_volumes', 0) or 0
            item_volumes = QTableWidgetItem(f"{total_vol} vol.")
            item_volumes.setTextAlignment(Qt.AlignCenter)
            self.tabela_manifestos.setItem(i, 4, item_volumes)
            
            # Caixas
            exp = manifesto.get('total_caixas_expedidas', 0) or 0
            rec = manifesto.get('total_caixas_recebidas', 0) or 0
            item_caixas = QTableWidgetItem(f"{rec}/{exp}")
            item_caixas.setTextAlignment(Qt.AlignCenter)
            self.tabela_manifestos.setItem(i, 5, item_caixas)
            
            # Ações
            acoes = self.criar_acoes_manifesto(manifesto['id'])
            self.tabela_manifestos.setCellWidget(i, 6, acoes)
    
    def buscar_volumes_em_tempo_real(self):
        """Busca volumes em tempo real enquanto digita"""
        if self.chk_tempo_real.isChecked() and self.txt_numero_volume.text().strip():
            self.buscar_volumes()
    
    def buscar_volumes(self):
        """Busca volumes por número"""
        try:
            numero_busca = self.txt_numero_volume.text().strip()
            
            if not numero_busca:
                self.tabela_volumes.setRowCount(0)
                self.lbl_stats_volumes.setText("Digite o número do volume para buscar")
                return
            
            print(f"DEBUG - Buscando volumes com: '{numero_busca}'")
            
            # Buscar em todos os manifestos
            todos_manifestos = listar_manifestos()
            volumes_encontrados = []
            
            for manifesto in todos_manifestos:
                try:
                    volumes = listar_volumes(manifesto['id'])
                    for volume in volumes:
                        # Buscar por correspondência parcial no número do volume
                        if numero_busca.upper() in volume['numero_volume'].upper():
                            volumes_encontrados.append({
                                'volume': volume,
                                'manifesto': manifesto
                            })
                except Exception as e:
                    print(f"Erro ao buscar volumes do manifesto {manifesto['id']}: {e}")
                    continue
            
            print(f"DEBUG - Volumes encontrados: {len(volumes_encontrados)}")
            
            # Preencher tabela
            self.tabela_volumes.setRowCount(len(volumes_encontrados))
            
            for i, item in enumerate(volumes_encontrados):
                volume = item['volume']
                manifesto = item['manifesto']
                
                # Aumentar altura específica da linha
                self.tabela_volumes.setRowHeight(i, 60)  # Aumentado de 50 para 60
                
                # Nº Volume
                item_numero = QTableWidgetItem(volume['numero_volume'])
                item_numero.setTextAlignment(Qt.AlignCenter)
                self.tabela_volumes.setItem(i, 0, item_numero)
                
                # Remetente
                item_remetente = QTableWidgetItem(volume['remetente'])
                item_remetente.setTextAlignment(Qt.AlignCenter)
                self.tabela_volumes.setItem(i, 1, item_remetente)
                
                # Destinatário
                item_destinatario = QTableWidgetItem(volume['destinatario'])
                item_destinatario.setTextAlignment(Qt.AlignCenter)
                self.tabela_volumes.setItem(i, 2, item_destinatario)
                
                # Nº Manifesto
                item_manifesto = QTableWidgetItem(manifesto['numero_manifesto'])
                item_manifesto.setTextAlignment(Qt.AlignCenter)
                self.tabela_volumes.setItem(i, 3, item_manifesto)
                
                # Data do Manifesto
                data = manifesto['data_manifesto'] or "N/A"
                item_data = QTableWidgetItem(data)
                item_data.setTextAlignment(Qt.AlignCenter)
                self.tabela_volumes.setItem(i, 4, item_data)
                
                # Status do Volume
                status = volume['status']
                item_status = QTableWidgetItem(self._formatar_status_volume(status))
                item_status.setTextAlignment(Qt.AlignCenter)
                
                if status == 'COMPLETO':
                    item_status.setBackground(QColor(76, 175, 80, 50))
                elif status == 'PARCIAL':
                    item_status.setBackground(QColor(255, 193, 7, 50))
                elif status == 'VOLUME EXTRA':
                    item_status.setBackground(QColor(156, 39, 176, 50))
                else:
                    item_status.setBackground(QColor(244, 67, 54, 50))
                
                self.tabela_volumes.setItem(i, 5, item_status)
                
                # Caixas
                caixas_texto = f"{volume['quantidade_recebida']}/{volume['quantidade_expedida']}"
                item_caixas = QTableWidgetItem(caixas_texto)
                item_caixas.setTextAlignment(Qt.AlignCenter)
                self.tabela_volumes.setItem(i, 6, item_caixas)
                
                # Ações
                acoes = self.criar_acoes_volume(
                    volume['id'], 
                    volume['quantidade_expedida'], 
                    volume['quantidade_recebida'],
                    volume['manifesto_id']
                )
                self.tabela_volumes.setCellWidget(i, 7, acoes)
            
            # Atualizar estatísticas
            if len(volumes_encontrados) == 0:
                self.lbl_stats_volumes.setText(f"❌ Nenhum volume encontrado com '{numero_busca}'")
            else:
                self.lbl_stats_volumes.setText(
                    f"✅ Encontrados {len(volumes_encontrados)} volume(s) com '{numero_busca}'"
                )
            
        except Exception as e:
            print(f"ERRO na busca de volumes: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            QMessageBox.critical(
                self,
                "Erro na Busca",
                f"Erro ao buscar volumes:\n{str(e)}"
            )
    
    def ver_detalhes_volume(self, volume_id):
        """Exibe os detalhes de um volume"""
        QMessageBox.information(self, "Detalhes do Volume", f"Detalhes do volume ID: {volume_id}")
        
    def iniciar_conferencia_manifesto(self, manifesto_id):
        """Inicia a conferência de um manifesto diretamente da busca"""
        try:
            from ui.conferencia_window import ConferenciaWindow
            
            # Verificar se já existe uma janela de conferência aberta para este manifesto
            if manifesto_id in self.conferencia_windows:
                janela_existente = self.conferencia_windows[manifesto_id]
                if janela_existente.isVisible():
                    janela_existente.raise_()
                    janela_existente.activateWindow()
                    return
                else:
                    # Janela foi fechada, remover do dicionário
                    del self.conferencia_windows[manifesto_id]
            
            # Se não houver, criar uma nova janela
            try:
                nova_janela = ConferenciaWindow(manifesto_id=manifesto_id, parent=self)
                self.conferencia_windows[manifesto_id] = nova_janela
                nova_janela.show()
                nova_janela.raise_()
                nova_janela.activateWindow()
                
                # Conectar sinal para remover do dicionário quando fechar
                nova_janela.destroyed.connect(lambda: self.remover_janela_conferencia(manifesto_id))
                
            except Exception as e:
                print(f"Erro ao abrir janela de conferência: {str(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Não foi possível abrir a conferência:\n{str(e)}"
                )
        except Exception as e:
            print(f"Erro ao iniciar conferência: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            QMessageBox.critical(
                self,
                "Erro",
                f"Ocorreu um erro inesperado ao iniciar a conferência:\n{str(e)}"
            )
    
    def remover_janela_conferencia(self, manifesto_id):
        """Remove a janela de conferência do dicionário quando fechada"""
        if manifesto_id in self.conferencia_windows:
            del self.conferencia_windows[manifesto_id]
    
    def receber_volume_direto(self, volume_id, manifesto_id, quantidade_expedida):
        """Recebe um volume diretamente da busca, solicitando responsável e mostrando número correto"""
        try:
            from PyQt5.QtWidgets import QInputDialog, QMessageBox, QDialog, QLineEdit
            from src.ui.conferencia_window import VolumeMultiploDialog
            from src.database import obter_volume, obter_caixas, marcar_caixa_recebida, marcar_volume_recebido
            
            # 1. Obter dados do volume imediatamente para as validações
            volume = obter_volume(volume_id)
            if volume is None:
                QMessageBox.critical(self, "Erro", f"Volume {volume_id} não encontrado!")
                return

            # 2. Lógica de formatação do número (4 ou 7 dígitos)
            numero_completo = volume['numero_volume']
            # Pega apenas o que está antes da barra, se houver barra
            parte_antes_barra = numero_completo.split('/')[0] if '/' in numero_completo else numero_completo
            remetente = volume['remetente'].upper()
            
            # Se for CABW ou CABE, pega 7 dígitos, senão pega 4
            if 'CABW' in remetente or 'CABE' in remetente:
                numero_exibicao = parte_antes_barra[-7:] 
            else:
                numero_exibicao = parte_antes_barra[-4:]

            # 3. Solicitar nome do responsável (Correção solicitada)
            nome, ok = QInputDialog.getText(
                self,
                "Responsável pelo Recebimento",
                f"Digite o nome de quem está recebendo o volume final {numero_exibicao}:",
                QLineEdit.Normal,
                ""
            )
            
            # Se cancelar ou deixar em branco, aborta a operação
            if not ok or not nome.strip():
                return

            nome_usuario = nome.strip().upper()

            # 4. Verificar caixas
            caixas = obter_caixas(volume_id)
            
            if quantidade_expedida > 1 and len(caixas) > 0:
                # Se tiver caixas individuais cadastradas, abrir diálogo para seleção passando o nome
                dialog = VolumeMultiploDialog(volume, caixas, self, nome_usuario)
                if dialog.exec_() == QDialog.Accepted:
                    QMessageBox.information(
                        self,
                        "Sucesso",
                        f"{dialog.quantidade_marcada} caixa(s) marcada(s) como recebida(s) com sucesso por {nome_usuario}!"
                    )
                    # Emitir sinal
                    self.volume_recebido.emit()
            else:
                # Se for apenas uma caixa, confirmar recebimento com o número formatado
                reply = QMessageBox.question(
                    self, 
                    'Confirmar Recebimento',
                    f'Confirma o recebimento do volume final {numero_exibicao}?\n\n'
                    f'Remetente: {volume["remetente"]}\n'
                    f'Responsável: {nome_usuario}',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # Passa o nome do usuário capturado
                    marcar_volume_recebido(volume_id, 1, nome_usuario)
                    QMessageBox.information(
                        self, 
                        "Sucesso", 
                        f"Volume final {numero_exibicao} recebido com sucesso!"
                    )
                    # Emitir sinal
                    self.volume_recebido.emit()
            
            # Atualizar a tabela de volumes
            self.buscar_volumes()
            
        except Exception as e:
            print(f"Erro ao receber volume: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            QMessageBox.critical(
                self,
                "Erro",
                f"Ocorreu um erro ao processar o recebimento:\n{str(e)}"
            )
            
            
    def ver_detalhes_manifesto(self, manifesto_id: int):
        """Abre os detalhes do manifesto"""
        try:
            from .detalhes_manifesto_dialog import DetalhesManifestoDialog
            dialog = DetalhesManifestoDialog(manifesto_id, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao abrir detalhes do manifesto:\n{str(e)}"
            )
    
    def abrir_conferencia(self, manifesto_id: int):
        """Abre a conferência do manifesto"""
        try:
            from .conferencia_window import ConferenciaWindow
            self.conferencia_window = ConferenciaWindow(manifesto_id, self)
            self.conferencia_window.show()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao abrir conferência:\n{str(e)}"
            )
    
    def _formatar_status_manifesto(self, status: str) -> str:
        """Formata o status do manifesto para exibição"""
        emojis = {
            'TOTALMENTE RECEBIDO': '✅',
            'PARCIALMENTE RECEBIDO': '⚠️',
            'NÃO RECEBIDO': '❌'
        }
        emoji = emojis.get(status, '❓')
        return f"{emoji} {status}"
    
    def _formatar_status_volume(self, status: str) -> str:
        """Formata o status do volume para exibição"""
        emojis = {
            'COMPLETO': '✅',
            'PARCIAL': '⚠️',
            'NÃO RECEBIDO': '❌',
            'VOLUME EXTRA': '➕'
        }
        emoji = emojis.get(status, '❓')
        return f"{emoji} {status}"