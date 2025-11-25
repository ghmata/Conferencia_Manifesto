"""
Sistema de Conferência de Manifestos - Interface Principal
Arquivo: src/ui/main_window.py
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QFileDialog, QStatusBar,
                             QAction, QToolBar, QDialog)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QColor, QFont
from datetime import datetime
import time

from src.database import (listar_manifestos, obter_estatisticas_manifesto,
                          obter_manifesto)
from src.pdf_extractor import extrair_manifesto_pdf, criar_manifesto_exemplo
from src.ui.novo_manifesto_dialog import NovoManifestoDialog
from src.ui.conferencia_window import ConferenciaWindow
from src.ui.detalhes_manifesto_dialog import DetalhesManifestoDialog


class MainWindow(QMainWindow):
    """Janela principal do sistema"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.atualizar_tabela()
        
    def init_ui(self):
        """Inicializa a interface do usuário"""
        self.setWindowTitle("Sistema de Conferência de Manifestos - CAN")
        self.setGeometry(100, 100, 1200, 700)
        
        # Criar menu
        self.criar_menu()
        
        # Criar toolbar
        self.criar_toolbar()
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Cabeçalho
        header_layout = QHBoxLayout()
        
        titulo = QLabel("📦 Manifestos Registrados")
        titulo_font = QFont()
        titulo_font.setPointSize(16)
        titulo_font.setBold(True)
        titulo.setFont(titulo_font)
        header_layout.addWidget(titulo)
        
        header_layout.addStretch()
        
        # Botões de ação
        btn_novo = QPushButton("➕ Novo Manifesto")
        btn_novo.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_novo.clicked.connect(self.novo_manifesto)
        header_layout.addWidget(btn_novo)
        
        btn_exemplo = QPushButton("🧪 Criar Exemplo")
        btn_exemplo.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        btn_exemplo.clicked.connect(self.criar_manifesto_exemplo)
        header_layout.addWidget(btn_exemplo)
        
        layout.addLayout(header_layout)
        
        # Tabela de manifestos
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)  # Reduzido para 6 colunas
        self.tabela.setHorizontalHeaderLabels([
            "Nº Manifesto", "Data", "Destino", 
            "Status", "Volumes", "Ações"
        ])
        
        # Configurar tabela
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setStyleSheet("""
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
        
        # IMPORTANTE: Conectar clique na linha para abrir detalhes
        self.tabela.cellClicked.connect(self.on_linha_clicada)
        
        layout.addWidget(self.tabela)
        
        # Barra de status
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Sistema pronto")
        
    def criar_menu(self):
        """Cria o menu da aplicação"""
        menubar = self.menuBar()
        
        # Menu Arquivo
        menu_arquivo = menubar.addMenu("&Arquivo")
        
        acao_novo = QAction("&Novo Manifesto", self)
        acao_novo.setShortcut("Ctrl+N")
        acao_novo.triggered.connect(self.novo_manifesto)
        menu_arquivo.addAction(acao_novo)
        
        menu_arquivo.addSeparator()
        
        acao_sair = QAction("&Sair", self)
        acao_sair.setShortcut("Ctrl+Q")
        acao_sair.triggered.connect(self.close)
        menu_arquivo.addAction(acao_sair)
        
        # Menu Visualizar
        menu_view = menubar.addMenu("&Visualizar")
        
        acao_atualizar = QAction("&Atualizar", self)
        acao_atualizar.setShortcut("F5")
        acao_atualizar.triggered.connect(self.atualizar_tabela)
        menu_view.addAction(acao_atualizar)
        
        # Menu Ajuda
        menu_ajuda = menubar.addMenu("&Ajuda")
        
        acao_sobre = QAction("&Sobre", self)
        acao_sobre.triggered.connect(self.mostrar_sobre)
        menu_ajuda.addAction(acao_sobre)
        
    def criar_toolbar(self):
        """Cria a toolbar"""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)
        
        # Botão Atualizar
        acao_atualizar = QAction("🔄 Atualizar", self)
        acao_atualizar.triggered.connect(self.atualizar_tabela)
        toolbar.addAction(acao_atualizar)
        
        toolbar.addSeparator()
        
        # Botão Novo Manifesto
        acao_novo = QAction("➕ Novo", self)
        acao_novo.triggered.connect(self.novo_manifesto)
        toolbar.addAction(acao_novo)
        
    def on_linha_clicada(self, row, column):
        """
        NOVO: Quando clicar na linha do manifesto, abre a lista de volumes
        """
        # Ignorar se clicou nos botões de ação (última coluna)
        if column == self.tabela.columnCount() - 1:
            return
        
        # Obter ID do manifesto da linha clicada
        item_numero = self.tabela.item(row, 0)
        if item_numero:
            numero_manifesto = item_numero.text()
            
            # Buscar manifesto por número para obter ID
            manifestos = listar_manifestos()
            manifesto_id = None
            for m in manifestos:
                if m['numero_manifesto'] == numero_manifesto:
                    manifesto_id = m['id']
                    break
            
            if manifesto_id:
                # Abrir janela de detalhes (lista de volumes)
                self.ver_detalhes(manifesto_id)
        
    def atualizar_tabela(self):
        """Atualiza a tabela de manifestos"""
        self.status_bar.showMessage("Carregando manifestos...")
        
        manifestos = listar_manifestos()
        self.tabela.setRowCount(len(manifestos))
        
        for i, manifesto in enumerate(manifestos):
            # Nº Manifesto
            self.tabela.setItem(i, 0, QTableWidgetItem(
                manifesto['numero_manifesto'] or "N/A"
            ))
            
            # Data
            data = manifesto['data_manifesto'] or "N/A"
            self.tabela.setItem(i, 1, QTableWidgetItem(data))
            
            # Destino (removido Origem)
            self.tabela.setItem(i, 2, QTableWidgetItem(
                manifesto['terminal_destino'] or "N/A"
            ))
            
            # Status
            status = manifesto['status']
            item_status = QTableWidgetItem(self._formatar_status(status))
            item_status.setTextAlignment(Qt.AlignCenter)
            
            # Cores baseadas no status
            if status == 'TOTALMENTE RECEBIDO':
                item_status.setBackground(QColor(76, 175, 80, 50))
            elif status == 'PARCIALMENTE RECEBIDO':
                item_status.setBackground(QColor(255, 193, 7, 50))
            else:
                item_status.setBackground(QColor(244, 67, 54, 50))
            
            self.tabela.setItem(i, 3, item_status)
            
            # Volumes
            total_vol = manifesto['total_volumes'] or 0
            exp = manifesto['total_caixas_expedidas'] or 0
            rec = manifesto['total_caixas_recebidas'] or 0
            
            item_volumes = QTableWidgetItem(f"{rec}/{exp} caixas ({total_vol} vol.)")
            item_volumes.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 4, item_volumes)
            
            # Botões de ação
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(5, 2, 5, 2)
            btn_layout.setSpacing(5)
            
            # Botão Conferir
            btn_conferir = QPushButton("🔍 Conferir")
            btn_conferir.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
            """)
            btn_conferir.clicked.connect(
                lambda checked, m_id=manifesto['id']: self.abrir_conferencia(m_id)
            )
            btn_layout.addWidget(btn_conferir)
            
            btn_layout.addStretch()
            self.tabela.setCellWidget(i, 5, btn_widget)
        
        self.status_bar.showMessage(
            f"Total: {len(manifestos)} manifesto(s) registrado(s)"
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
        
    def novo_manifesto(self):
        """Abre diálogo para criar novo manifesto"""
        dialog = NovoManifestoDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.atualizar_tabela()
    
    def criar_manifesto_exemplo(self):
        """Cria um manifesto de exemplo para demonstração"""
        from src.database import criar_manifesto, adicionar_volume
        
        reply = QMessageBox.question(
            self,
            "Criar Exemplo",
            "Deseja criar um manifesto de exemplo para teste?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Criar manifesto
                dados, volumes = criar_manifesto_exemplo()
                
                # Adicionar timestamp ao número para evitar duplicatas
                numero_unico = f"{dados['numero_manifesto']}-{int(time.time())}"
                
                manifesto_id = criar_manifesto(
                    numero=numero_unico,
                    data=dados['data_manifesto'],
                    origem=dados.get('terminal_origem', ''),
                    destino=dados['terminal_destino'],
                    missao=dados.get('missao'),
                    aeronave=dados.get('aeronave')
                )
                
                # Adicionar volumes
                for vol in volumes:
                    adicionar_volume(
                        manifesto_id=manifesto_id,
                        remetente=vol['remetente'],
                        destinatario=vol['destinatario'],
                        numero_volume=vol['numero_volume'],
                        quantidade_exp=vol['quantidade_expedida'],
                        peso=vol['peso_total'],
                        cubagem=vol['cubagem'],
                        prioridade=vol['prioridade'],
                        tipo_material=vol.get('tipo_material'),
                        embalagem=vol.get('embalagem')
                    )
                
                # Pequeno delay para garantir que o banco foi atualizado
                time.sleep(0.1)
                
                self.atualizar_tabela()
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Manifesto de exemplo {numero_unico} criado com sucesso!\n"
                    f"Total de volumes: {len(volumes)}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Erro ao criar manifesto de exemplo:\n{str(e)}"
                )
    
    def abrir_conferencia(self, manifesto_id: int):
        """Abre janela de conferência"""
        self.conferencia_window = ConferenciaWindow(manifesto_id, self)
        self.conferencia_window.show()
        self.conferencia_window.conferencia_finalizada.connect(self.atualizar_tabela)
        
    def ver_detalhes(self, manifesto_id: int):
        """Abre diálogo de detalhes do manifesto (LISTA DE VOLUMES)"""
        dialog = DetalhesManifestoDialog(manifesto_id, self)
        dialog.exec_()
        # Atualizar tabela ao fechar (caso tenha havido mudanças)
        self.atualizar_tabela()
        
    def mostrar_sobre(self):
        """Mostra diálogo sobre o sistema"""
        QMessageBox.about(
            self,
            "Sobre",
            "<h2>Sistema de Conferência de Manifestos CAN</h2>"
            "<p><b>Versão:</b> 1.0.0</p>"
            "<p><b>Desenvolvido para:</b> Correio Aéreo Nacional</p>"
            "<p>Sistema para agilizar a conferência de manifestos de carga, "
            "permitindo registro rápido, rastreabilidade completa e "
            "histórico de recebimentos.</p>"
            "<p><b>Funcionalidades:</b></p>"
            "<ul>"
            "<li>✅ Importação de manifestos em PDF</li>"
            "<li>✅ Conferência rápida via busca inteligente</li>"
            "<li>✅ Controle de volumes múltiplos</li>"
            "<li>✅ Histórico completo de recebimentos</li>"
            "<li>✅ Relatórios e estatísticas</li>"
            "</ul>"
            "<p><b>Clique em qualquer linha para ver detalhes dos volumes!</b></p>"
        )