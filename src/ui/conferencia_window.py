"""
Sistema de Conferência de Manifestos - Janela de Conferência
Arquivo: src/ui/conferencia_window.py
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTextEdit,
                             QGroupBox, QMessageBox, QDialog, QSpinBox,
                             QCheckBox, QFrame, QScrollArea, QRadioButton,
                             QButtonGroup, QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette
from datetime import datetime

from src.database import (obter_manifesto, buscar_volume, obter_caixas,
                          marcar_caixa_recebida, marcar_volume_recebido,
                          iniciar_conferencia, finalizar_conferencia,
                          obter_estatisticas_manifesto, listar_volumes,
                          registrar_log)
from src.pdf_extractor import ManifestoExtractor


class ConferenciaWindow(QMainWindow):
    """Janela principal de conferência de manifestos"""
    
    conferencia_finalizada = pyqtSignal()
    
    def __init__(self, manifesto_id: int, parent=None):
        super().__init__(parent)
        self.manifesto_id = manifesto_id
        self.manifesto = obter_manifesto(manifesto_id)
        self.conferencia_ativa = False
        self.volume_encontrado = None  # Armazena volume para confirmação
        self.init_ui()
        self.carregar_manifesto()
        
    def init_ui(self):
        """Inicializa a interface"""
        self.setWindowTitle("Conferência de Manifesto")
        self.setGeometry(150, 150, 1000, 750)
        
        # ScrollArea principal
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Widget central dentro do scroll
        central_widget = QWidget()
        scroll.setWidget(central_widget)
        self.setCentralWidget(scroll)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Cabeçalho do manifesto
        self.criar_cabecalho(layout)
        
        # Área de busca
        self.criar_area_busca(layout)
        
        # Área de resultados (com botão de confirmação)
        self.criar_area_resultados(layout)
        
        # Resumo
        self.criar_resumo(layout)
        
        # Botões de ação
        self.criar_botoes_acao(layout)
        
    def criar_cabecalho(self, layout):
        """Cria o cabeçalho com informações do manifesto"""
        group = QGroupBox("📋 Informações do Manifesto")
        group_layout = QVBoxLayout()
        
        info_text = f"""
        <b>Nº Manifesto:</b> {self.manifesto['numero_manifesto']}<br>
        <b>Data:</b> {self.manifesto['data_manifesto']}<br>
        <b>Destino:</b> {self.manifesto['terminal_destino']}<br>
        """
        
        lbl_info = QLabel(info_text)
        lbl_info.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        group_layout.addWidget(lbl_info)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def criar_area_busca(self, layout):
        """Cria a área de busca de volumes"""
        group = QGroupBox("🔍 Conferência de Volumes")
        group_layout = QVBoxLayout()
        
        # Instrução
        lbl_instrucao = QLabel(
            "Digite o <b>REMETENTE</b> e os <b>ÚLTIMOS DÍGITOS ANTES DA /</b> do n° do volume:"
        )
        group_layout.addWidget(lbl_instrucao)
        
        # Campo Remetente
        remetente_layout = QHBoxLayout()
        remetente_layout.addWidget(QLabel("Remetente:"))
        
        self.txt_remetente = QLineEdit()
        self.txt_remetente.setPlaceholderText("Ex: PAMASP, CABW")
        self.txt_remetente.setMaximumWidth(200)
        self.txt_remetente.textChanged.connect(self.atualizar_instrucao_digitos)
        self.txt_remetente.returnPressed.connect(self.focar_digitos)
        remetente_layout.addWidget(self.txt_remetente)
        
        remetente_layout.addStretch()
        group_layout.addLayout(remetente_layout)
        
        # Campo Últimos Dígitos
        digitos_layout = QHBoxLayout()
        
        self.lbl_digitos = QLabel("Últimos 4 dígitos (antes da /):")
        digitos_layout.addWidget(self.lbl_digitos)
        
        self.txt_digitos = QLineEdit()
        self.txt_digitos.setPlaceholderText("Digite os últimos dígitos ANTES da /")
        self.txt_digitos.setMaximumWidth(250)
        self.txt_digitos.returnPressed.connect(self.buscar_volume_tecla_enter)
        digitos_layout.addWidget(self.txt_digitos)
        
        btn_buscar = QPushButton("🔍 Buscar")
        btn_buscar.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        btn_buscar.clicked.connect(self.buscar_volume_btn)
        digitos_layout.addWidget(btn_buscar)
        
        digitos_layout.addStretch()
        group_layout.addLayout(digitos_layout)
        
        # Dica
        lbl_dica = QLabel(
            "💡 <i>Exemplo: 251381004311/0001 → Digite apenas '4311' (4 últimos antes da /)</i>"
        )
        lbl_dica.setStyleSheet("color: #666; font-size: 11px;")
        group_layout.addWidget(lbl_dica)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def criar_area_resultados(self, layout):
        """Cria a área de exibição de resultados"""
        group = QGroupBox("📦 Resultado da Busca")
        group_layout = QVBoxLayout()
        
        # Área de texto com scroll
        scroll_resultado = QScrollArea()
        scroll_resultado.setWidgetResizable(True)
        scroll_resultado.setMinimumHeight(200)
        scroll_resultado.setMaximumHeight(350)
        
        self.txt_resultado = QTextEdit()
        self.txt_resultado.setReadOnly(True)
        self.txt_resultado.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.txt_resultado.setStyleSheet("""
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        
        scroll_resultado.setWidget(self.txt_resultado)
        group_layout.addWidget(self.txt_resultado)
        
        # Botão de confirmação (inicialmente oculto)
        self.btn_confirmar = QPushButton("✅ CONFIRMAR RECEBIMENTO")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 15px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_confirmar.clicked.connect(self.confirmar_recebimento)
        self.btn_confirmar.setVisible(False)
        group_layout.addWidget(self.btn_confirmar)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def criar_resumo(self, layout):
        """Cria o resumo da conferência"""
        group = QGroupBox("📊 Resumo da Conferência")
        group_layout = QVBoxLayout()
        
        self.lbl_resumo = QLabel("Aguardando início da conferência...")
        self.lbl_resumo.setStyleSheet("""
            padding: 15px;
            background-color: #f5f5f5;
            border-radius: 5px;
            font-size: 13px;
        """)
        group_layout.addWidget(self.lbl_resumo)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def criar_botoes_acao(self, layout):
        """Cria os botões de ação"""
        btn_layout = QHBoxLayout()
        
        self.btn_iniciar = QPushButton("▶️ Iniciar Conferência")
        self.btn_iniciar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_iniciar.clicked.connect(self.iniciar_conferencia_handler)
        btn_layout.addWidget(self.btn_iniciar)
        
        self.btn_finalizar = QPushButton("✅ Finalizar Conferência")
        self.btn_finalizar.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.btn_finalizar.clicked.connect(self.finalizar_conferencia_handler)
        self.btn_finalizar.setEnabled(False)
        btn_layout.addWidget(self.btn_finalizar)
        
        btn_layout.addStretch()
        
        btn_fechar = QPushButton("Fechar")
        btn_fechar.clicked.connect(self.close)
        btn_layout.addWidget(btn_fechar)
        
        layout.addLayout(btn_layout)
        
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
            
    def focar_digitos(self):
        """Move o foco para o campo de dígitos"""
        self.txt_digitos.setFocus()
        
    def buscar_volume_tecla_enter(self):
        """Busca volume ao pressionar Enter"""
        self.buscar_volume_btn()
        
    def buscar_volume_btn(self):
        """Busca volume e exibe resultado"""
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
        """Exibe mensagem de volume não encontrado"""
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
        """Exibe volume encontrado e aguarda confirmação"""
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
        """Confirma o recebimento do volume encontrado"""
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
                marcar_caixa_recebida(volume['id'], 1, "Usuário")
                self.mostrar_sucesso_recebimento(volume, 1, 1)
                self.atualizar_resumo()
        else:
            # Volume múltiplo - abrir diálogo de seleção
            dialog = VolumeMultiploDialog(volume, caixas, self)
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
        """Mostra mensagem de sucesso após recebimento"""
        resultado = f"""
╔══════════════════════════════════════════════════════════════╗
║               ✅ RECEBIMENTO CONFIRMADO COM SUCESSO!          ║
╚══════════════════════════════════════════════════════════════╝

N° Volume: {volume['numero_volume']}
Remetente: {volume['remetente']} → Destinatário: {volume['destinatario']}

Recebido agora: {recebidas} de {total} caixa(s)
Horário: {datetime.now().strftime('%H:%M:%S')}

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
        """Exibe quando múltiplos volumes são encontrados"""
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
        """Atualiza o resumo da conferência"""
        stats = obter_estatisticas_manifesto(self.manifesto_id)
        
        total_vol = stats['total_volumes'] or 0
        exp = stats['total_caixas_expedidas'] or 0
        rec = stats['total_caixas_recebidas'] or 0
        perc = stats['percentual_recebido']
        
        completos = stats['volumes_completos'] or 0
        parciais = stats['volumes_parciais'] or 0
        nao_rec = stats['volumes_nao_recebidos'] or 0
        
        resumo = f"""
<b>📊 ESTATÍSTICAS DA CONFERÊNCIA</b><br><br>
<b>Total de nºs de volume:</b> {total_vol}<br>
<b>Total de caixas esperadas:</b> {exp}<br>
<b>Caixas recebidas:</b> {rec} ({perc:.1f}%)<br><br>
<b>Status dos volumes:</b><br>
  ✅ Completos: {completos}<br>
  ⚠️ Parciais: {parciais}<br>
  ❌ Não recebidos: {nao_rec}
"""
        
        self.lbl_resumo.setText(resumo)
        
    def iniciar_conferencia_handler(self):
        """Inicia a conferência"""
        reply = QMessageBox.question(
            self,
            "Iniciar Conferência",
            f"Deseja iniciar a conferência do manifesto {self.manifesto['numero_manifesto']}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            iniciar_conferencia(self.manifesto_id, "Usuário")
            self.conferencia_ativa = True
            self.btn_iniciar.setEnabled(False)
            self.btn_finalizar.setEnabled(True)
            self.txt_remetente.setFocus()
            
            QMessageBox.information(
                self,
                "Conferência Iniciada",
                "Conferência iniciada! Comece a conferir os volumes."
            )
            
    def finalizar_conferencia_handler(self):
        """Finaliza a conferência solicitando nome do conferente"""
        stats = obter_estatisticas_manifesto(self.manifesto_id)
        
        exp = stats['total_caixas_expedidas'] or 0
        rec = stats['total_caixas_recebidas'] or 0
        
        # Solicitar nome do conferente
        nome, ok = QInputDialog.getText(
            self,
            "Finalizar Conferência",
            "Digite o nome de quem recebeu o manifesto:",
            QLineEdit.Normal,
            ""
        )
        
        if not ok or not nome.strip():
            QMessageBox.warning(
                self,
                "Nome Obrigatório",
                "É necessário informar o nome do responsável pela conferência!"
            )
            return
        
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
            f"Recebido por: {nome.strip()}",
            nome.strip()
        )
        
        self.conferencia_finalizada.emit()
        
        QMessageBox.information(
            self,
            "✅ Conferência Finalizada",
            f"Conferência finalizada com sucesso!\n\n"
            f"Recebidas: {rec}/{exp} caixas ({stats['percentual_recebido']:.1f}%)\n"
            f"Responsável: {nome.strip()}"
        )
        
        self.close()


class VolumeMultiploDialog(QDialog):
    """Diálogo para selecionar caixas específicas de um volume"""
    
    def __init__(self, volume: dict, caixas: list, parent=None):
        super().__init__(parent)
        self.volume = volume
        self.caixas = caixas
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
        layout.addWidget(titulo)
        
        # Informações
        info = QLabel(
            f"<b>Remetente:</b> {self.volume['remetente']} → "
            f"<b>Destinatário:</b> {self.volume['destinatario']}<br>"
            f"<b>Total de caixas:</b> {self.volume['quantidade_expedida']}"
        )
        info.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
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
            marcar_caixa_recebida(self.volume['id'], caixa['numero_caixa'], "Usuário")
        
        self.quantidade_marcada = len(selecionadas)
        self.accept()