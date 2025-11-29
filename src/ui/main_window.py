"""
Sistema de Conferência de Manifestos - Interface Principal
Arquivo: src/ui/main_window.py
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QFileDialog, QStatusBar,
                             QAction, QToolBar, QDialog, QInputDialog, QLineEdit,
                             QSpinBox, QFormLayout)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QColor, QFont
from datetime import datetime
import time
import sys
import os

# Adiciona o diretório src ao path para importações
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import (listar_manifestos, obter_estatisticas_manifesto,
                      obter_manifesto, adicionar_volume, marcar_volume_recebido,
                      listar_volumes)
from pdf_extractor import extrair_manifesto_pdf, criar_manifesto_exemplo
from ui.novo_manifesto_dialog import NovoManifestoDialog
from ui.conferencia_window import ConferenciaWindow
from ui.detalhes_manifesto_dialog import DetalhesManifestoDialog

# Senha para apagar manifestos
SENHA_EXCLUSAO = "pitaco"


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
        
        # Botão Novo Manifesto
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
        
        # Botão Criar Exemplo (para testes)
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

        # Botão Busca Avançada
        btn_busca = QPushButton("🔍 Busca Avançada")
        btn_busca.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        btn_busca.clicked.connect(self.abrir_busca)
        header_layout.addWidget(btn_busca)
        
        layout.addLayout(header_layout)
        
        # Tabela de manifestos
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels([
            "Nº Manifesto", "Data", "Destino", 
            "Status", "Volumes", "Ações"
        ])
        
        # Configurar tabela - CONFIGURAÇÃO OTIMIZADA
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # Nº Manifesto - MAIOR
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Data  
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Destino
        header.setSectionResizeMode(3, QHeaderView.Interactive)  # Status - REDUZIDO
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Volumes
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Ações
        
        # Definir larguras específicas
        self.tabela.setColumnWidth(0, 180)  # Nº Manifesto - MAIS LARGO
        self.tabela.setColumnWidth(3, 140)  # Status - REDUZIDO
        
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setAlternatingRowColors(True)
        
        # IMPORTANTE: Desabilitar duplo clique acidental
        self.tabela.setSelectionMode(QTableWidget.SingleSelection)
        
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
        
        # Conectar clique na linha
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

        # Nova ação: Busca Avançada
        acao_busca = QAction("&Busca Avançada", self)
        acao_busca.setShortcut("Ctrl+F")
        acao_busca.triggered.connect(self.abrir_busca)
        menu_arquivo.addAction(acao_busca)
        
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

        # Botão Busca Avançada
        acao_busca = QAction("🔍 Busca", self)
        acao_busca.triggered.connect(self.abrir_busca)
        toolbar.addAction(acao_busca)
        
    def abrir_busca(self):
        """Abre janela de busca avançada"""
        from ui.busca_window import BuscaWindow
        self.busca_window = BuscaWindow(self)
        self.busca_window.show()
        
    def on_linha_clicada(self, row, column):
        """Quando clicar na linha do manifesto, abre a lista de volumes"""
        if column == self.tabela.columnCount() - 1:
            return
        
        item_numero = self.tabela.item(row, 0)
        if item_numero:
            numero_manifesto = item_numero.text()
            manifestos = listar_manifestos()
            manifesto_id = None
            for m in manifestos:
                if m['numero_manifesto'] == numero_manifesto:
                    manifesto_id = m['id']
                    break
            
            if manifesto_id:
                self.ver_detalhes(manifesto_id)
        
    def atualizar_tabela(self):
        """Atualiza a tabela de manifestos"""
        self.status_bar.showMessage("Carregando manifestos...")
        
        manifestos = listar_manifestos()
        self.tabela.setRowCount(len(manifestos))
        
        for i, manifesto in enumerate(manifestos):
            # Aumentar altura da linha - DENTRO DO LOOP
            self.tabela.setRowHeight(i, 65)
            
            # Nº Manifesto - CENTRALIZADO
            item_manifesto = QTableWidgetItem(manifesto['numero_manifesto'] or "N/A")
            item_manifesto.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 0, item_manifesto)
            
            # Data - CENTRALIZADO
            data = manifesto['data_manifesto'] or "N/A"
            item_data = QTableWidgetItem(data)
            item_data.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 1, item_data)
            
            # Destino - CENTRALIZADO
            item_destino = QTableWidgetItem(manifesto['terminal_destino'] or "N/A")
            item_destino.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 2, item_destino)
            
            # Status - CENTRALIZADO
            status = manifesto['status']
            item_status = QTableWidgetItem(self._formatar_status(status))
            item_status.setTextAlignment(Qt.AlignCenter)
            
            if status == 'TOTALMENTE RECEBIDO':
                item_status.setBackground(QColor(76, 175, 80, 50))
            elif status == 'PARCIALMENTE RECEBIDO':
                item_status.setBackground(QColor(255, 193, 7, 50))
            else:
                item_status.setBackground(QColor(244, 67, 54, 50))
            
            self.tabela.setItem(i, 3, item_status)
            
            # Volumes - CENTRALIZADO
            total_vol = manifesto['total_volumes'] or 0
            exp = manifesto['total_caixas_expedidas'] or 0
            rec = manifesto['total_caixas_recebidas'] or 0
            
            item_volumes = QTableWidgetItem(f"{rec}/{exp} caixas ({total_vol} vol.)")
            item_volumes.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 4, item_volumes)
            
            # Botões de ação - CENTRALIZADOS NA COLUNA
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(15, 5, 15, 5)
            btn_layout.setSpacing(8)
            
            # Espaço antes dos botões para centralização
            btn_layout.addStretch()
            
            # 1. Conferir Material
            btn_conferir = QPushButton("Conferir\nManifesto")
            btn_conferir.setMinimumSize(100, 42)
            btn_conferir.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 4px 6px;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
                QPushButton:pressed {
                    background-color: #0a6cb4;
                }
            """)
            btn_conferir.setToolTip("Conferir material do manifesto")
            btn_conferir.clicked.connect(
                lambda checked, m_id=manifesto['id']: self.abrir_conferencia(m_id)
            )
            btn_layout.addWidget(btn_conferir)
            
            # 2. Inserir Volume Extra
            btn_extra = QPushButton("Inserir\nExtravolume")
            btn_extra.setMinimumSize(100, 42)
            btn_extra.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 4px 6px;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e68900;
                }
                QPushButton:pressed {
                    background-color: #d17a00;
                }
            """)
            btn_extra.setToolTip("Inserir volume extra (não constava no manifesto)")
            btn_extra.clicked.connect(
                lambda checked, m_id=manifesto['id']: self.inserir_volume_extra(m_id)
            )
            btn_layout.addWidget(btn_extra)
            
            # 3. Receber Tudo
            btn_tudo = QPushButton("Receber\nTudo")
            btn_tudo.setMinimumSize(100, 42)
            btn_tudo.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 4px 6px;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
            btn_tudo.setToolTip("Receber todos os volumes de uma vez")
            btn_tudo.clicked.connect(
                lambda checked, m_id=manifesto['id']: self.receber_tudo(m_id)
            )
            btn_layout.addWidget(btn_tudo)
            
            # 4. Apagar Manifesto
            btn_apagar = QPushButton("Excluir\nManifesto")
            btn_apagar.setMinimumSize(100, 42)
            btn_apagar.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 4px 6px;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
                QPushButton:pressed {
                    background-color: #c00a0a;
                }
            """)
            btn_apagar.setToolTip("Excluir manifesto (requer senha)")
            btn_apagar.clicked.connect(
                lambda checked, m_id=manifesto['id']: self.apagar_manifesto(m_id)
            )
            btn_layout.addWidget(btn_apagar)
            
            # Espaço depois dos botões para centralização
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
        from database import criar_manifesto, adicionar_volume
        import time
        
        reply = QMessageBox.question(
            self,
            "Criar Exemplo",
            "Deseja criar um manifesto de exemplo para teste?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                dados, volumes = criar_manifesto_exemplo()
                numero_unico = f"{dados['numero_manifesto']}-EX{int(time.time() * 1000) % 100000}"
                
                time.sleep(0.5)
                
                manifesto_id = criar_manifesto(
                    numero=numero_unico,
                    data=dados['data_manifesto'],
                    origem=dados.get('terminal_origem', ''),
                    destino=dados['terminal_destino'],
                    missao=dados.get('missao'),
                    aeronave=dados.get('aeronave')
                )
                
                time.sleep(0.3)
                
                total_caixas = 0
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
                    total_caixas += vol['quantidade_expedida']
                    time.sleep(0.05)
                
                time.sleep(0.5)
                self.atualizar_tabela()
                
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Manifesto de exemplo criado!\n\n"
                    f"Número: {numero_unico}\n"
                    f"Nºs de volume: {len(volumes)}\n"
                    f"Total de CAIXAS: {total_caixas}"
                )
                
            except Exception as e:
                import traceback
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Erro ao criar exemplo:\n{str(e)}\n\n{traceback.format_exc()}"
                )
    
    def abrir_conferencia(self, manifesto_id: int):
        """Abre janela de conferência"""
        self.conferencia_window = ConferenciaWindow(manifesto_id, self)
        self.conferencia_window.show()
        self.conferencia_window.conferencia_finalizada.connect(self.atualizar_tabela)
        
    def inserir_volume_extra(self, manifesto_id: int):
        """Insere volume extra que não constava no manifesto"""
        dialog = VolumeExtraDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                adicionar_volume(
                    manifesto_id=manifesto_id,
                    remetente=dialog.remetente,
                    destinatario="PAMALS",
                    numero_volume=dialog.numero_volume,
                    quantidade_exp=dialog.quantidade,
                    tipo_material="VOLUME EXTRA",
                    embalagem="CAIXA"
                )
                
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Volume extra {dialog.numero_volume} adicionado ao manifesto!"
                )
                
                self.atualizar_tabela()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Erro ao adicionar volume extra:\n{str(e)}"
                )
    
    def receber_tudo(self, manifesto_id: int):
        """Recebe todos os volumes de uma vez"""
        reply = QMessageBox.question(
            self,
            "Receber Tudo",
            "Tem certeza que deseja marcar TODOS os volumes deste manifesto como recebidos?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                volumes = listar_volumes(manifesto_id)
                
                for volume in volumes:
                    marcar_volume_recebido(volume['id'], volume['quantidade_expedida'], "Sistema")
                
                from database import finalizar_conferencia, registrar_log
                
                # Solicitar nome
                nome, ok = QInputDialog.getText(
                    self,
                    "Nome do Responsável",
                    "Digite o nome de quem está recebendo:",
                    QLineEdit.Normal,
                    ""
                )
                
                if ok and nome.strip():
                    finalizar_conferencia(manifesto_id)
                    registrar_log(
                        manifesto_id,
                        "RECEBIMENTO TOTAL",
                        f"Todos os volumes recebidos por: {nome.strip()}",
                        nome.strip()
                    )
                
                self.atualizar_tabela()
                
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Todos os {len(volumes)} volumes foram marcados como recebidos!"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Erro ao receber volumes:\n{str(e)}"
                )
    
    def apagar_manifesto(self, manifesto_id: int):
        """Apaga manifesto com senha"""
        senha, ok = QInputDialog.getText(
            self,
            "Apagar Manifesto",
            "Digite a senha para apagar o manifesto:",
            QLineEdit.Password,
            ""
        )
        
        if not ok:
            return
        
        if senha != SENHA_EXCLUSAO:
            QMessageBox.critical(
                self,
                "Senha Incorreta",
                "Senha incorreta! Não é possível apagar o manifesto."
            )
            return
        
        manifesto = obter_manifesto(manifesto_id)
        
        reply = QMessageBox.warning(
            self,
            "Confirmação",
            f"Tem certeza que deseja APAGAR o manifesto {manifesto['numero_manifesto']}?\n\n"
            f"Esta ação NÃO pode ser desfeita!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from database import get_connection
                
                conn = get_connection()
                try:
                    cursor = conn.cursor()
                    
                    # Apagar em cascata
                    cursor.execute("DELETE FROM logs WHERE manifesto_id = ?", (manifesto_id,))
                    cursor.execute("DELETE FROM caixas_individuais WHERE volume_id IN (SELECT id FROM volumes WHERE manifesto_id = ?)", (manifesto_id,))
                    cursor.execute("DELETE FROM volumes WHERE manifesto_id = ?", (manifesto_id,))
                    cursor.execute("DELETE FROM manifestos WHERE id = ?", (manifesto_id,))
                    
                finally:
                    conn.close()
                
                self.atualizar_tabela()
                
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Manifesto {manifesto['numero_manifesto']} apagado com sucesso!"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Erro ao apagar manifesto:\n{str(e)}"
                )
        
    def ver_detalhes(self, manifesto_id: int):
        """Abre diálogo de detalhes do manifesto"""
        dialog = DetalhesManifestoDialog(manifesto_id, self)
        dialog.exec_()
        self.atualizar_tabela()
        
    def mostrar_sobre(self):
        """Mostra diálogo sobre o sistema"""
        QMessageBox.about(
            self,
            "Sobre",
            "<h2>Sistema de Conferência de Manifestos CAN</h2>"
            "<p><b>Versão:</b> 1.0.0</p>"
            "<p><b>Desenvolvido para:</b> Correio Aéreo Nacional</p>"
            "<p>Sistema para agilizar a conferência de manifestos de carga.</p>"
            "<p><b>Funcionalidades:</b></p>"
            "<ul>"
            "<li>✅ Conferência inteligente com confirmação</li>"
            "<li>✅ Seleção de caixas individuais</li>"
            "<li>✅ Inserção de volumes extras</li>"
            "<li>✅ Recebimento total em lote</li>"
            "<li>✅ Exclusão protegida por senha</li>"
            "</ul>"
            "<p><b>Clique em qualquer linha para ver detalhes!</b></p>"
        )


class VolumeExtraDialog(QDialog):
    """Diálogo para inserir volume extra"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.remetente = ""
        self.numero_volume = ""
        self.quantidade = 1
        self.init_ui()
        
    def init_ui(self):
        """Inicializa a interface"""
        self.setWindowTitle("Inserir Volume Extra")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("➕ Inserir Volume Extra (não constava no manifesto)")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        titulo.setFont(font)
        layout.addWidget(titulo)
        
        # Formulário
        form_layout = QFormLayout()
        
        self.txt_remetente = QLineEdit()
        self.txt_remetente.setPlaceholderText("Ex: PAMASP, AFA, CABW")
        form_layout.addRow("Remetente*:", self.txt_remetente)
        
        self.txt_numero = QLineEdit()
        self.txt_numero.setPlaceholderText("Ex: 251381004311/0001")
        form_layout.addRow("N° do Volume*:", self.txt_numero)
        
        self.spin_quantidade = QSpinBox()
        self.spin_quantidade.setMinimum(1)
        self.spin_quantidade.setMaximum(99)
        self.spin_quantidade.setValue(1)
        form_layout.addRow("Quantidade de caixas:", self.spin_quantidade)
        
        layout.addLayout(form_layout)
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        
        btn_salvar = QPushButton("💾 Salvar")
        btn_salvar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        btn_salvar.clicked.connect(self.salvar)
        btn_layout.addWidget(btn_salvar)
        
        layout.addLayout(btn_layout)
        
    def salvar(self):
        """Valida e salva os dados"""
        self.remetente = self.txt_remetente.text().strip().upper()
        self.numero_volume = self.txt_numero.text().strip()
        self.quantidade = self.spin_quantidade.value()
        
        if not self.remetente or not self.numero_volume:
            QMessageBox.warning(
                self,
                "Campos Obrigatórios",
                "Preencha o remetente e o número do volume!"
            )
            return
        
        self.accept()