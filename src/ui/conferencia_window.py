"""
Sistema de Conferência de Manifestos - Janela de Conferência
Arquivo: src/ui/conferencia_window.py
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTextEdit,
                             QGroupBox, QMessageBox, QDialog, QSpinBox,
                             QCheckBox, QFrame, QScrollArea, QRadioButton,
                             QButtonGroup, QInputDialog, QApplication, 
                             QDesktopWidget, QGridLayout, QProgressBar, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
from datetime import datetime

from src.database import (obter_manifesto, buscar_volume, obter_caixas,
                          marcar_caixa_recebida, marcar_volume_recebido,
                          iniciar_conferencia, finalizar_conferencia,
                          obter_estatisticas_manifesto, listar_volumes,
                          registrar_log)
from src.pdf_extractor import ManifestoExtractor


class ConferenciaWindow(QMainWindow):
    """Janela principal de conferência de manifestos - Tela Cheia OTIMIZADA COM FUNCIONALIDADE COMPLETA"""
    
    conferencia_finalizada = pyqtSignal()
    
    def __init__(self, manifesto_id: int, parent=None):
        super().__init__(parent)
        self.manifesto_id = manifesto_id
        self.manifesto = obter_manifesto(manifesto_id)
        self.conferencia_ativa = False
        self.volume_encontrado = None
        self.usuario_conferente = ""
        self.init_ui()
        self.carregar_manifesto()
        self.showMaximized()  # Abre em tela cheia
        
    def init_ui(self):
        """Inicializa a interface OTIMIZADA para tela cheia"""
        self.setWindowTitle(f"Conferência - {self.manifesto['numero_manifesto']}")
        
        # Configuração para tela cheia - sem tamanho mínimo fixo
        self.setMinimumSize(1024, 768)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal em grid - OTIMIZADO PARA TELA CHEIA
        main_layout = QGridLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # ===== HEADER =====
        self.criar_header(main_layout)
        
        # ===== PAINEL ESQUERDO - CONTROLES =====
        self.criar_painel_controles(main_layout)
        
        # ===== PAINEL CENTRAL - ESTATÍSTICAS =====
        self.criar_painel_estatisticas(main_layout)
        
        # ===== PAINEL DIREITO - RESULTADOS =====
        self.criar_painel_resultados(main_layout)
        
        # ===== BARRA DE PROGRESSO =====
        self.criar_barra_progresso(main_layout)
        
        # ===== RODAPÉ - BOTÕES DE AÇÃO =====
        self.criar_rodape(main_layout)
        
        # CONFIGURAÇÃO CRÍTICA PARA TELA CHEIA
        main_layout.setColumnStretch(0, 1)  # Coluna controles
        main_layout.setColumnStretch(1, 1)  # Coluna estatísticas  
        main_layout.setColumnStretch(2, 2)  # Coluna resultados (MAIOR)
        
        # Linhas: 0=Header, 1=Principal (Expande), 2=Progresso, 3=Rodapé
        main_layout.setRowStretch(0, 0)     # Header fixo (adaptável)
        main_layout.setRowStretch(1, 1)     # Linha principal EXPANSÍVEL
        main_layout.setRowStretch(2, 0)     # Barra progresso - fixa
        main_layout.setRowStretch(3, 0)     # Rodapé - fixo
        
    def criar_header(self, layout):
        """Cria o cabeçalho com informações principais - OTIMIZADO"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #007bff, stop:1 #0056b3);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        # Removido setFixedHeight para evitar cortes em resoluções baixas ou fontes grandes
        header_frame.setMinimumHeight(100) 
        header_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        
        header_layout = QHBoxLayout(header_frame)
        
        # Informações do manifesto
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        titulo = QLabel("CONFERÊNCIA DE MANIFESTO")
        titulo.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
        """)
        titulo.setWordWrap(True) # Segurança contra corte
        info_layout.addWidget(titulo)
        
        detalhes = QLabel(
            f"<b>Manifesto:</b> {self.manifesto['numero_manifesto']} | "
            f"<b>Data:</b> {self.manifesto['data_manifesto']} | "
            f"<b>Destino:</b> {self.manifesto['terminal_destino']}"
        )
        detalhes.setStyleSheet("color: white; font-size: 13px;") # Fonte levemente aumentada
        detalhes.setTextFormat(Qt.RichText)
        detalhes.setWordWrap(True) # Essencial para não cortar informações
        info_layout.addWidget(detalhes)
        
        header_layout.addLayout(info_layout, stretch=2)
        header_layout.addStretch(1)
        
        # Status da conferência
        status_layout = QVBoxLayout()
        status_layout.setSpacing(5)
        
        self.lbl_status_conferencia = QLabel("CONFERÊNCIA NÃO INICIADA")
        self.lbl_status_conferencia.setStyleSheet("""
            color: white;
            font-size: 14px;
            font-weight: bold;
            padding: 8px 15px;
            background-color: rgba(255,255,255,0.2);
            border-radius: 15px;
        """)
        self.lbl_status_conferencia.setAlignment(Qt.AlignCenter)
        self.lbl_status_conferencia.setWordWrap(True)
        status_layout.addWidget(self.lbl_status_conferencia)
        
        self.lbl_conferente = QLabel("Conferente: ---")
        self.lbl_conferente.setStyleSheet("color: white; font-size: 12px;")
        self.lbl_conferente.setAlignment(Qt.AlignCenter)
        self.lbl_conferente.setWordWrap(True)
        status_layout.addWidget(self.lbl_conferente)
        
        header_layout.addLayout(status_layout)
        
        layout.addWidget(header_frame, 0, 0, 1, 3)
        
    def criar_painel_controles(self, layout):
        """Cria o painel esquerdo com controles de busca - OTIMIZADO"""
        controles_group = QGroupBox("🔍 BUSCAR VOLUME")
        controles_layout = QVBoxLayout(controles_group)
        controles_layout.setSpacing(12)
        
        # Instrução
        instrucao = QLabel(
            "Digite o <b>REMETENTE</b> e os <b>ÚLTIMOS DÍGITOS ANTES DA /</b> do n° do volume:"
        )
        instrucao.setStyleSheet("font-size: 12px; color: #6c757d; margin-bottom: 5px;")
        instrucao.setWordWrap(True) # Ativado para evitar corte
        # Removido setFixedHeight(40) para permitir expansão automática
        instrucao.setMinimumHeight(40)
        controles_layout.addWidget(instrucao)
        
        # Campo Remetente
        lbl_remetente = QLabel("Remetente:")
        lbl_remetente.setStyleSheet("font-weight: bold; color: #495057; font-size: 12px;")
        controles_layout.addWidget(lbl_remetente)
        
        self.txt_remetente = QLineEdit()
        self.txt_remetente.setPlaceholderText("Ex: PAMASP, CABW, etc...")
        self.txt_remetente.setMinimumHeight(35) # Alterado de fixed para minimum
        self.txt_remetente.textChanged.connect(self.atualizar_instrucao_digitos)
        self.txt_remetente.returnPressed.connect(self.focar_digitos)
        controles_layout.addWidget(self.txt_remetente)
        
        # Campo Dígitos
        lbl_digitos_layout = QHBoxLayout()
        self.lbl_digitos = QLabel("Últimos 4 dígitos (antes da /):")
        self.lbl_digitos.setStyleSheet("font-weight: bold; color: #495057; font-size: 12px;")
        self.lbl_digitos.setWordWrap(True)
        lbl_digitos_layout.addWidget(self.lbl_digitos)
        
        lbl_digitos_layout.addStretch()
        
        self.lbl_exemplo = QLabel("Ex: 4311")
        self.lbl_exemplo.setStyleSheet("color: #6c757d; font-size: 11px; font-style: italic;")
        lbl_digitos_layout.addWidget(self.lbl_exemplo)
        controles_layout.addLayout(lbl_digitos_layout)
        
        self.txt_digitos = QLineEdit()
        self.txt_digitos.setPlaceholderText("Digite os últimos dígitos ANTES da /")
        self.txt_digitos.setMinimumHeight(35) # Alterado de fixed para minimum
        self.txt_digitos.returnPressed.connect(self.buscar_volume_btn)
        controles_layout.addWidget(self.txt_digitos)
        
        # Botão Buscar
        self.btn_buscar = QPushButton("🔍 BUSCAR VOLUME")
        self.btn_buscar.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 12px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.btn_buscar.setMinimumHeight(45)
        self.btn_buscar.clicked.connect(self.buscar_volume_btn)
        self.btn_buscar.setEnabled(False)
        controles_layout.addWidget(self.btn_buscar)
        
        # Dica interativa
        dica_frame = QFrame()
        dica_frame.setStyleSheet("""
            QFrame {
                background-color: #e7f3ff;
                border: 1px solid #b3d9ff;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        # Removido setFixedHeight(80) para evitar corte de texto
        dica_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        
        dica_layout = QVBoxLayout(dica_frame)
        dica_layout.setContentsMargins(10, 10, 10, 10) # Margens internas garantidas
        
        dica_titulo = QLabel("💡 Dica Importante")
        dica_titulo.setStyleSheet("font-weight: bold; color: #0066cc; margin-bottom: 5px; font-size: 11px;")
        dica_layout.addWidget(dica_titulo)
        
        dica_texto = QLabel(
            "Para <b>251381004311/0001</b>, digite apenas <b>4311</b><br>"
            "(últimos 4 dígitos antes da barra)"
        )
        dica_texto.setStyleSheet("font-size: 11px; color: #0066cc; line-height: 1.3;")
        dica_texto.setWordWrap(True) # Garantia visual
        dica_layout.addWidget(dica_texto)
        
        controles_layout.addWidget(dica_frame)
        controles_layout.addStretch()
        
        # POLÍTICA DE TAMANHO para expansão controlada
        controles_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout.addWidget(controles_group, 1, 0)
        
    def criar_painel_estatisticas(self, layout):
        """Cria o painel central com estatísticas - OTIMIZADO"""
        stats_group = QGroupBox("📊 PROGRESSO")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(10)
        
        # Cards de estatísticas
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(8)
        
        # Card Total Volumes
        card_volumes = self.criar_card_estatistica("VOLUMES", "0", "#007bff")
        cards_layout.addWidget(card_volumes)
        
        # Card Caixas
        card_caixas = self.criar_card_estatistica("CAIXAS", "0/0", "#28a745")
        cards_layout.addWidget(card_caixas)
        
        # Card Progresso
        card_progresso = self.criar_card_estatistica("PROGRESSO", "0%", "#ffc107")
        cards_layout.addWidget(card_progresso)
        
        stats_layout.addLayout(cards_layout)
        
        # Detalhamento - ALTURA FLEXÍVEL
        detalhes_frame = QFrame()
        detalhes_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        detalhes_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding) # Permitir expansão
        
        detalhes_layout = QVBoxLayout(detalhes_frame)
        
        self.lbl_detalhes_stats = QLabel("Inicie a conferência para ver as estatísticas...")
        self.lbl_detalhes_stats.setStyleSheet("font-size: 12px; line-height: 1.4;")
        self.lbl_detalhes_stats.setWordWrap(True)
        self.lbl_detalhes_stats.setAlignment(Qt.AlignTop | Qt.AlignLeft) # Alinhamento ao topo
        detalhes_layout.addWidget(self.lbl_detalhes_stats)
        
        stats_layout.addWidget(detalhes_frame)
        
        # POLÍTICA DE TAMANHO para expansão controlada
        stats_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout.addWidget(stats_group, 1, 1)
        
    def criar_card_estatistica(self, titulo, valor, cor):
        """Cria um card de estatística individual - OTIMIZADO"""
        card = QFrame()
        # setFixedHeight(80) alterado para Minimum para evitar cortes
        card.setMinimumHeight(80)
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {cor};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(2)
        card_layout.setContentsMargins(5, 5, 5, 5)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("""
            color: white;
            font-size: 10px;
            font-weight: bold;
            margin-bottom: 2px;
        """)
        lbl_titulo.setAlignment(Qt.AlignCenter)
        lbl_titulo.setWordWrap(True)
        card_layout.addWidget(lbl_titulo)
        
        lbl_valor = QLabel(valor)
        lbl_valor.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
        """)
        lbl_valor.setAlignment(Qt.AlignCenter)
        lbl_valor.setWordWrap(False) # Valores curtos não devem quebrar
        card_layout.addWidget(lbl_valor)
        
        # Armazenar referência para atualização
        if titulo == "VOLUMES":
            self.lbl_total_volumes = lbl_valor
        elif titulo == "CAIXAS":
            self.lbl_total_caixas = lbl_valor
        elif titulo == "PROGRESSO":
            self.lbl_progresso = lbl_valor
            
        return card
        
    def criar_painel_resultados(self, layout):
        """Cria o painel direito com resultados - ALTAMENTE OTIMIZADO"""
        resultados_group = QGroupBox("📦 RESULTADO DA BUSCA")
        resultados_layout = QVBoxLayout(resultados_group)
        resultados_layout.setSpacing(10)
        
        # Área de resultados - EXPANSÍVEL
        self.txt_resultado = QTextEdit()
        self.txt_resultado.setReadOnly(True)
        self.txt_resultado.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                line-height: 1.3;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 12px;
                background-color: #f8f9fa;
            }
        """)
        self.txt_resultado.setText("""
╔══════════════════════════════════════════════════════════════╗
║                 AGUARDANDO CONFERÊNCIA                      ║
╚══════════════════════════════════════════════════════════════╝

• A conferência ainda não foi iniciada
• Clique em 'INICIAR CONFERÊNCIA' para começar
• Use os campos à esquerda para buscar volumes
        """)
        # Importante: Permitir que o QTextEdit ocupe o espaço disponível
        self.txt_resultado.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        resultados_layout.addWidget(self.txt_resultado)
        
        # Botão de confirmação
        self.btn_confirmar = QPushButton("✅ CONFIRMAR RECEBIMENTO")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 15px;
                font-weight: bold;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.btn_confirmar.setMinimumHeight(50)
        self.btn_confirmar.clicked.connect(self.confirmar_recebimento)
        self.btn_confirmar.setVisible(False)
        resultados_layout.addWidget(self.btn_confirmar)
        
        # Histórico rápido
        historico_frame = QFrame()
        # Removido setFixedHeight(70) para evitar corte
        historico_frame.setMinimumHeight(70)
        historico_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        
        historico_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 6px;
                padding: 10px;
                margin-top: 8px;
            }
        """)
        historico_layout = QVBoxLayout(historico_frame)
        historico_layout.setContentsMargins(10, 10, 10, 10)
        
        historico_titulo = QLabel("📝 ULTIMAS ACOES")
        historico_titulo.setStyleSheet("font-weight: bold; color: #856404; margin-bottom: 5px; font-size: 11px;")
        historico_layout.addWidget(historico_titulo)
        
        self.lbl_historico = QLabel("Nenhuma ação realizada")
        self.lbl_historico.setStyleSheet("font-size: 11px; color: #856404; line-height: 1.3;")
        self.lbl_historico.setWordWrap(True) # Essencial
        historico_layout.addWidget(self.lbl_historico)
        
        resultados_layout.addWidget(historico_frame)
        
        # POLÍTICA DE TAMANHO para expansão máxima
        resultados_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout.addWidget(resultados_group, 1, 2)
        
    def criar_barra_progresso(self, layout):
        """Cria a barra de progresso - OTIMIZADA"""
        progresso_frame = QFrame()
        # Alterado de Fixed para Minimum
        progresso_frame.setMinimumHeight(70)
        progresso_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        progresso_layout = QVBoxLayout(progresso_frame)
        
        # Labels de progresso
        labels_layout = QHBoxLayout()
        
        self.lbl_progresso_texto = QLabel("Progresso da conferência: 0%")
        self.lbl_progresso_texto.setStyleSheet("font-weight: bold; color: #495057; font-size: 13px;")
        self.lbl_progresso_texto.setWordWrap(True)
        labels_layout.addWidget(self.lbl_progresso_texto)
        
        labels_layout.addStretch()
        
        self.lbl_tempo_decorrido = QLabel("Tempo: --:--:--")
        self.lbl_tempo_decorrido.setStyleSheet("color: #6c757d; font-size: 11px;")
        labels_layout.addWidget(self.lbl_tempo_decorrido)
        
        progresso_layout.addLayout(labels_layout)
        
        # Barra de progresso
        self.barra_progresso = QProgressBar()
        self.barra_progresso.setFixedHeight(20) # Barra em si pode ser fixa
        self.barra_progresso.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
                background-color: #e9ecef;
                height: 20px;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        self.barra_progresso.setValue(0)
        progresso_layout.addWidget(self.barra_progresso)
        
        layout.addWidget(progresso_frame, 2, 0, 1, 3)
        
    def criar_rodape(self, layout):
        """Cria o rodapé com botões de ação - OTIMIZADO"""
        rodape_frame = QFrame()
        # Alterado de Fixed para Minimum para garantir que botões não cortem se layout apertar
        rodape_frame.setMinimumHeight(80)
        rodape_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        rodape_layout = QHBoxLayout(rodape_frame)
        rodape_layout.setSpacing(15)
        
        # Botão Iniciar
        self.btn_iniciar = QPushButton("▶️ INICIAR CONFERÊNCIA")
        self.btn_iniciar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px 20px;
                font-size: 13px;
                font-weight: bold;
                min-width: 160px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.btn_iniciar.setMinimumHeight(45)
        self.btn_iniciar.clicked.connect(self.iniciar_conferencia_handler)
        rodape_layout.addWidget(self.btn_iniciar)
        
        # Botão Finalizar
        self.btn_finalizar = QPushButton("✅ FINALIZAR CONFERÊNCIA")
        self.btn_finalizar.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                padding: 12px 20px;
                font-size: 13px;
                font-weight: bold;
                min-width: 160px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: white;
            }
        """)
        self.btn_finalizar.setMinimumHeight(45)
        self.btn_finalizar.clicked.connect(self.finalizar_conferencia_handler)
        self.btn_finalizar.setEnabled(False)
        rodape_layout.addWidget(self.btn_finalizar)
        
        rodape_layout.addStretch()
        
        # Botão Fechar
        btn_fechar = QPushButton("FECHAR")
        btn_fechar.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 12px 20px;
                font-size: 13px;
                min-width: 100px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        btn_fechar.setMinimumHeight(45)
        btn_fechar.clicked.connect(self.close)
        rodape_layout.addWidget(btn_fechar)
        
        layout.addWidget(rodape_frame, 3, 0, 1, 3)

    # === MÉTODOS DE FUNCIONALIDADE - MANTIDOS DA VERSÃO FUNCIONAL ===
    
    def carregar_manifesto(self):
        """Carrega e atualiza informações do manifesto"""
        self.atualizar_resumo()
        
    def atualizar_instrucao_digitos(self):
        """Atualiza a instrução de dígitos baseado no remetente"""
        remetente = self.txt_remetente.text().strip().upper()
        
        if 'CABW' in remetente or 'CABE' in remetente:
            self.lbl_digitos.setText("Últimos 7 dígitos (antes da /):")
            self.txt_digitos.setPlaceholderText("Digite os últimos 7 dígitos ANTES da /")
        else:
            self.lbl_digitos.setText("Últimos 4 dígitos (antes da /):")
            self.txt_digitos.setPlaceholderText("Digite os últimos 4 dígitos ANTES da /")
            
        # Habilitar botão buscar apenas se ambos campos preenchidos
        self.btn_buscar.setEnabled(
            bool(self.txt_remetente.text().strip()) and 
            bool(self.txt_digitos.text().strip())
        )
            
    def focar_digitos(self):
        """Move o foco para o campo de dígitos"""
        self.txt_digitos.setFocus()
        
    def buscar_volume_btn(self):
        """Busca volume e exibe resultado - FUNCIONALIDADE ORIGINAL"""
        if not self.conferencia_ativa:
            QMessageBox.warning(
                self,
                "Aviso",
                "Inicie a conferência primeiro!"
            )
            return
            
        remetente = self.txt_remetente.text().strip().upper()
        digitos = self.txt_digitos.text().strip()
        
        if not remetente or not digitos:
            QMessageBox.warning(
                self,
                "Campos Obrigatórios",
                "Preencha o remetente e os últimos dígitos!"
            )
            return
        
        # Buscar volume
        volumes = buscar_volume(self.manifesto_id, remetente, digitos)
        
        if not volumes:
            # NÃO ENCONTRADO
            self.exibir_nao_encontrado(remetente, digitos)
            self.volume_encontrado = None
            self.btn_confirmar.setVisible(False)
        elif len(volumes) == 1:
            # ENCONTRADO ÚNICO - Mostrar e pedir confirmação
            self.volume_encontrado = volumes[0]
            self.exibir_volume_encontrado(volumes[0])
            self.btn_confirmar.setVisible(True)
        else:
            # MÚLTIPLOS VOLUMES
            self.exibir_multiplos_volumes(volumes)
            self.volume_encontrado = None
            self.btn_confirmar.setVisible(False)
            
    def exibir_nao_encontrado(self, remetente: str, digitos: str):
        """Exibe mensagem de volume não encontrado - FUNCIONALIDADE ORIGINAL"""
        resultado = f"""
╔══════════════════════════════════════════════════════════════╗
║                     ❌ VOLUME NÃO ENCONTRADO                  ║
╚══════════════════════════════════════════════════════════════╝

Remetente informado: {remetente}
Últimos dígitos (antes da /): {digitos}

Este volume NÃO está no manifesto {self.manifesto['numero_manifesto']}.

Opções:
1. Verificar se digitou corretamente
2. Conferir se o volume pertence a outro manifesto
3. Use o botão "Inserir Volume Extra" na tela principal

"""
        self.txt_resultado.setStyleSheet("""
            QTextEdit {
                border: 2px solid #f44336;
                background-color: #ffebee;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        self.txt_resultado.setText(resultado)
        
        # Limpar campos
        self.txt_digitos.clear()
        self.txt_digitos.setFocus()
        
    def exibir_volume_encontrado(self, volume: dict):
        """Exibe volume encontrado e aguarda confirmação - FUNCIONALIDADE ORIGINAL"""
        caixas = obter_caixas(volume['id'])
        
        resultado = f"""
╔══════════════════════════════════════════════════════════════╗
║                   ✅ VOLUME ENCONTRADO!                       ║
╚══════════════════════════════════════════════════════════════╝

N° Volume: {volume['numero_volume']}
Remetente: {volume['remetente']} → Destinatário: {volume['destinatario']}

Quantidade: {volume['quantidade_expedida']} caixa(s)
Peso: {volume['peso_total']} kg | Cubagem: {volume['cubagem']} m³
Prioridade: {volume['prioridade']}

Status Atual:
"""
        
        # Mostrar status de cada caixa
        for caixa in caixas:
            status_emoji = "✅" if caixa['status'] == 'RECEBIDA' else "⬜"
            status_texto = "RECEBIDA" if caixa['status'] == 'RECEBIDA' else "NÃO RECEBIDA"
            resultado += f"  {status_emoji} Caixa {caixa['numero_caixa']} de {volume['quantidade_expedida']}: {status_texto}\n"
        
        resultado += f"""

{'⚠️ ATENÇÃO: Verifique se este é o volume correto!' if volume['quantidade_expedida'] == 1 else '⚠️ ATENÇÃO: Este volume tem múltiplas caixas!'}

{'Clique em CONFIRMAR RECEBIMENTO para registrar.' if volume['quantidade_expedida'] == 1 else 'Clique em CONFIRMAR para escolher qual(is) caixa(s) receber.'}
"""
        
        self.txt_resultado.setStyleSheet("""
            QTextEdit {
                border: 2px solid #FF9800;
                background-color: #FFF3E0;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        self.txt_resultado.setText(resultado)
        
    def confirmar_recebimento(self):
        """Confirma o recebimento do volume encontrado - FUNCIONALIDADE ORIGINAL"""
        if not self.volume_encontrado:
            return
        
        volume = self.volume_encontrado
        caixas = obter_caixas(volume['id'])
        
        if volume['quantidade_expedida'] == 1:
            # Volume simples - confirmar direto
            if caixas[0]['status'] == 'RECEBIDA':
                QMessageBox.information(
                    self,
                    "Já Recebido",
                    "Esta caixa já foi recebida anteriormente!"
                )
            else:
                marcar_caixa_recebida(volume['id'], 1, self.usuario_conferente)
                self.mostrar_sucesso_recebimento(volume, 1, 1)
                self.atualizar_resumo()
        else:
            # Volume múltiplo - abrir diálogo de seleção
            dialog = VolumeMultiploDialog(volume, caixas, self, self.usuario_conferente)
            if dialog.exec_() == QDialog.Accepted:
                self.atualizar_resumo()
                self.mostrar_sucesso_recebimento(volume, dialog.quantidade_marcada, volume['quantidade_expedida'])
        
        # Limpar para próxima busca
        self.txt_remetente.clear()
        self.txt_digitos.clear()
        self.txt_remetente.setFocus()
        self.volume_encontrado = None
        self.btn_confirmar.setVisible(False)
        
    def mostrar_sucesso_recebimento(self, volume: dict, recebidas: int, total: int):
        """Mostra mensagem de sucesso após recebimento - FUNCIONALIDADE ORIGINAL"""
        resultado = f"""
╔══════════════════════════════════════════════════════════════╗
║               ✅ RECEBIMENTO CONFIRMADO COM SUCESSO!          ║
╚══════════════════════════════════════════════════════════════╝

N° Volume: {volume['numero_volume']}
Remetente: {volume['remetente']} → Destinatário: {volume['destinatario']}

Recebido agora: {recebidas} de {total} caixa(s)
Horário: {datetime.now().strftime('%H:%M:%S')}
Recebido por: {self.usuario_conferente}

✅ Registrado no sistema!
"""
        self.txt_resultado.setStyleSheet("""
            QTextEdit {
                border: 2px solid #4CAF50;
                background-color: #e8f5e9;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        self.txt_resultado.setText(resultado)
        
    def exibir_multiplos_volumes(self, volumes: list):
        """Exibe quando múltiplos volumes são encontrados - FUNCIONALIDADE ORIGINAL"""
        resultado = f"""
╔══════════════════════════════════════════════════════════════╗
║              ⚠️  MÚLTIPLOS VOLUMES ENCONTRADOS                ║
╚══════════════════════════════════════════════════════════════╝

Foram encontrados {len(volumes)} volumes com estes dígitos:

"""
        for i, vol in enumerate(volumes, 1):
            resultado += f"{i}. {vol['numero_volume']} ({vol['remetente']} → {vol['destinatario']})\n"
        
        resultado += "\nPor favor, seja mais específico."
        
        self.txt_resultado.setStyleSheet("""
            QTextEdit {
                border: 2px solid #ff9800;
                background-color: #fff3e0;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        self.txt_resultado.setText(resultado)
        
    def atualizar_resumo(self):
        """Atualiza o resumo da conferência - FUNCIONALIDADE ORIGINAL"""
        stats = obter_estatisticas_manifesto(self.manifesto_id)
        
        total_vol = stats['total_volumes'] or 0
        exp = stats['total_caixas_expedidas'] or 0
        rec = stats['total_caixas_recebidas'] or 0
        perc = stats['percentual_recebido']
        
        completos = stats['volumes_completos'] or 0
        parciais = stats['volumes_parciais'] or 0
        nao_rec = stats['volumes_nao_recebidos'] or 0
        
        # Atualizar cards
        self.lbl_total_volumes.setText(str(total_vol))
        self.lbl_total_caixas.setText(f"{rec}/{exp}")
        self.lbl_progresso.setText(f"{perc:.1f}%")
        self.barra_progresso.setValue(int(perc))
        self.lbl_progresso_texto.setText(f"Progresso da conferência: {perc:.1f}%")
        
        # Atualizar detalhes
        detalhes = f"""📊 ESTATÍSTICAS DA CONFERÊNCIA

Total de nºs de volume: {total_vol}
Total de caixas esperadas: {exp}
Caixas recebidas: {rec} ({perc:.1f}%)
Caixas faltantes: {exp - rec}

Status dos volumes:
  ✅ Completos: {completos}
  ⚠️ Parciais: {parciais}
  ❌ Não recebidos: {nao_rec}"""
        
        self.lbl_detalhes_stats.setText(detalhes)
        
    def iniciar_conferencia_handler(self):
        """Inicia a conferência - FUNCIONALIDADE ORIGINAL"""
        # Solicitar nome do conferente
        nome, ok = QInputDialog.getText(
            self,
            "Nome do Conferente",
            "Digite o nome de quem vai conferir:",
            QLineEdit.Normal,
            ""
        )
        
        if not ok or not nome.strip():
            QMessageBox.warning(
                self,
                "Nome Obrigatório",
                "É necessário informar o nome do conferente!"
            )
            return
            
        reply = QMessageBox.question(
            self,
            "Iniciar Conferência",
            f"Deseja iniciar a conferência do manifesto {self.manifesto['numero_manifesto']}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.usuario_conferente = nome.strip()
            iniciar_conferencia(self.manifesto_id, self.usuario_conferente)
            self.conferencia_ativa = True
            
            # Atualizar interface
            self.lbl_status_conferencia.setText("CONFERÊNCIA EM ANDAMENTO")
            self.lbl_conferente.setText(f"Conferente: {self.usuario_conferente}")
            self.btn_iniciar.setEnabled(False)
            self.btn_finalizar.setEnabled(True)
            self.txt_remetente.setFocus()
            
            QMessageBox.information(
                self,
                "Conferência Iniciada",
                f"Conferência iniciada por {self.usuario_conferente}! Comece a conferir os volumes."
            )
            
    def finalizar_conferencia_handler(self):
        """Finaliza a conferência solicitando nome do conferente - FUNCIONALIDADE ORIGINAL"""
        stats = obter_estatisticas_manifesto(self.manifesto_id)
        
        exp = stats['total_caixas_expedidas'] or 0
        rec = stats['total_caixas_recebidas'] or 0
        
        if rec < exp:
            # Conferência incompleta
            faltantes = exp - rec
            reply = QMessageBox.warning(
                self,
                "⚠️ Conferência Incompleta",
                f"ATENÇÃO: Nem todas as caixas foram recebidas!\n\n"
                f"Esperadas: {exp} caixas\n"
                f"Recebidas: {rec} caixas\n"
                f"Faltantes: {faltantes} caixas\n\n"
                f"Deseja realmente finalizar?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        # Finalizar e registrar conferente
        finalizar_conferencia(self.manifesto_id)
        registrar_log(
            self.manifesto_id,
            "CONFERÊNCIA FINALIZADA",
            f"Recebido por: {self.usuario_conferente}",
            self.usuario_conferente
        )
        
        self.conferencia_finalizada.emit()
        
        QMessageBox.information(
            self,
            "✅ Conferência Finalizada",
            f"Conferência finalizada com sucesso!\n\n"
            f"Recebidas: {rec}/{exp} caixas ({stats['percentual_recebido']:.1f}%)\n"
            f"Responsável: {self.usuario_conferente}"
        )
        
        self.close()


class VolumeMultiploDialog(QDialog):
    """Diálogo para selecionar caixas específicas de um volume - FUNCIONALIDADE ORIGINAL"""
    
    def __init__(self, volume: dict, caixas: list, parent=None, usuario: str = "Sistema"):
        super().__init__(parent)
        self.volume = volume
        self.caixas = caixas
        self.usuario = usuario
        self.quantidade_marcada = 0
        self.init_ui()
        
    def init_ui(self):
        """Inicializa a interface"""
        self.setWindowTitle("Selecionar Caixas")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel(f"📦 Volume: {self.volume['numero_volume']}")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        titulo.setFont(font)
        titulo.setWordWrap(True)
        layout.addWidget(titulo)
        
        # Informações
        info = QLabel(
            f"<b>Remetente:</b> {self.volume['remetente']} → "
            f"<b>Destinatário:</b> {self.volume['destinatario']}<br>"
            f"<b>Total de caixas:</b> {self.volume['quantidade_expedida']}"
        )
        info.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Status e seleção de caixas
        layout.addWidget(QLabel("<b>Selecione qual(is) caixa(s) está(ão) sendo recebida(s):</b>"))
        
        self.checkboxes = []
        for caixa in self.caixas:
            cb = QCheckBox(
                f"Caixa {caixa['numero_caixa']} de {self.volume['quantidade_expedida']}"
            )
            
            if caixa['status'] == 'RECEBIDA':
                cb.setChecked(True)
                cb.setEnabled(False)
                cb.setText(cb.text() + f" ✅ (Já recebida)")
            
            self.checkboxes.append((cb, caixa))
            layout.addWidget(cb)
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        
        btn_confirmar = QPushButton("✅ Confirmar Seleção")
        btn_confirmar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_confirmar.clicked.connect(self.confirmar)
        btn_layout.addWidget(btn_confirmar)
        
        layout.addLayout(btn_layout)
        
    def confirmar(self):
        """Confirma a seleção das caixas"""
        selecionadas = []
        for cb, caixa in self.checkboxes:
            if cb.isChecked() and cb.isEnabled():
                selecionadas.append(caixa)
        
        if not selecionadas:
            QMessageBox.warning(
                self,
                "Aviso",
                "Selecione pelo menos uma caixa que está sendo recebida!"
            )
            return
        
        # Marcar caixas como recebidas
        for caixa in selecionadas:
            marcar_caixa_recebida(self.volume['id'], caixa['numero_caixa'], self.usuario)
        
        self.quantidade_marcada = len(selecionadas)
        self.accept()