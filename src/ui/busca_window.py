"""
Sistema de Conferência de Manifestos - Janela de Busca Avançada
Arquivo: src/ui/busca_window.py
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QTabWidget, QHeaderView,
                             QMessageBox, QDateEdit, QComboBox, QFormLayout,
                             QGroupBox, QCheckBox)
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QFont, QColor
import sys
import os

# Adiciona o diretório pai ao path para importações
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import (listar_manifestos, listar_volumes)


class BuscaWindow(QMainWindow):
    """Janela para busca avançada de manifestos e volumes"""

    def __init__(self, parent=None):
        super().__init__(parent)
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
        
        self.tabela_manifestos.setSelectionBehavior(QTableWidget.SelectRows)
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
        
        self.tabela_volumes.setSelectionBehavior(QTableWidget.SelectRows)
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
            # Nº Manifesto
            item_numero = QTableWidgetItem(manifesto['numero_manifesto'] or "N/A")
            self.tabela_manifestos.setItem(i, 0, item_numero)
            
            # Data
            data = manifesto['data_manifesto'] or "N/A"
            self.tabela_manifestos.setItem(i, 1, QTableWidgetItem(data))
            
            # Destino
            item_destino = QTableWidgetItem(manifesto['terminal_destino'] or "N/A")
            self.tabela_manifestos.setItem(i, 2, item_destino)
            
            # Status
            status_manifesto = manifesto['status']
            item_status = QTableWidgetItem(self._formatar_status_manifesto(status_manifesto))
            item_status.setTextAlignment(0x0004)  # Qt.AlignCenter = 0x0004
            
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
            item_volumes.setTextAlignment(0x0004)  # Qt.AlignCenter = 0x0004
            self.tabela_manifestos.setItem(i, 4, item_volumes)
            
            # Caixas
            exp = manifesto.get('total_caixas_expedidas', 0) or 0
            rec = manifesto.get('total_caixas_recebidas', 0) or 0
            item_caixas = QTableWidgetItem(f"{rec}/{exp}")
            item_caixas.setTextAlignment(0x0004)  # Qt.AlignCenter = 0x0004
            self.tabela_manifestos.setItem(i, 5, item_caixas)
            
            # Botão Ver Detalhes
            btn_detalhes = QPushButton("👁️ Ver")
            btn_detalhes.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    padding: 5px 10px;
                    border: none;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
            """)
            btn_detalhes.setToolTip("Ver detalhes do manifesto")
            btn_detalhes.clicked.connect(lambda checked, m_id=manifesto['id']: self.ver_detalhes_manifesto(m_id))
            self.tabela_manifestos.setCellWidget(i, 6, btn_detalhes)
    
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
                
                # Nº Volume
                self.tabela_volumes.setItem(i, 0, QTableWidgetItem(volume['numero_volume']))
                
                # Remetente
                self.tabela_volumes.setItem(i, 1, QTableWidgetItem(volume['remetente']))
                
                # Destinatário
                self.tabela_volumes.setItem(i, 2, QTableWidgetItem(volume['destinatario']))
                
                # Nº Manifesto
                self.tabela_volumes.setItem(i, 3, QTableWidgetItem(manifesto['numero_manifesto']))
                
                # Data do Manifesto
                data = manifesto['data_manifesto'] or "N/A"
                self.tabela_volumes.setItem(i, 4, QTableWidgetItem(data))
                
                # Status do Volume
                status = volume['status']
                item_status = QTableWidgetItem(self._formatar_status_volume(status))
                item_status.setTextAlignment(0x0004)  # Qt.AlignCenter = 0x0004
                
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
                item_caixas.setTextAlignment(0x0004)  # Qt.AlignCenter = 0x0004
                self.tabela_volumes.setItem(i, 6, item_caixas)
                
                # Botões de ação
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(5, 2, 5, 2)
                btn_layout.setSpacing(3)
                
                # Botão Ver Manifesto
                btn_manifesto = QPushButton("📋")
                btn_manifesto.setToolTip("Ver manifesto")
                btn_manifesto.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        border: none;
                        padding: 5px 8px;
                        border-radius: 3px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #0b7dda;
                    }
                """)
                btn_manifesto.clicked.connect(lambda checked, m_id=manifesto['id']: self.ver_detalhes_manifesto(m_id))
                btn_layout.addWidget(btn_manifesto)
                
                # Botão Conferir
                btn_conferir = QPushButton("🔍")
                btn_conferir.setToolTip("Conferir volume")
                btn_conferir.setStyleSheet("""
                    QPushButton {
                        background-color: #FF9800;
                        color: white;
                        border: none;
                        padding: 5px 8px;
                        border-radius: 3px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #e68900;
                    }
                """)
                btn_conferir.clicked.connect(lambda checked, m_id=manifesto['id']: self.abrir_conferencia(m_id))
                btn_layout.addWidget(btn_conferir)
                
                btn_layout.addStretch()
                self.tabela_volumes.setCellWidget(i, 7, btn_widget)
            
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