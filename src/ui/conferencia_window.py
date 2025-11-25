"""
Sistema de Conferência de Manifestos - Janela de Conferência
Arquivo: src/ui/conferencia_window.py
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTextEdit,
                             QGroupBox, QMessageBox, QDialog, QSpinBox,
                             QCheckBox, QFrame)
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
        self.init_ui()
        self.carregar_manifesto()
        
    def init_ui(self):
        """Inicializa a interface"""
        self.setWindowTitle("Conferência de Manifesto")
        self.setGeometry(150, 150, 900, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Cabeçalho do manifesto
        self.criar_cabecalho(layout)
        
        # Área de busca
        self.criar_area_busca(layout)
        
        # Área de resultados
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
        <b>Origem:</b> {self.manifesto['terminal_origem']} → <b>Destino:</b> {self.manifesto['terminal_destino']}<br>
        <b>Missão:</b> {self.manifesto.get('missao', 'N/A')} | <b>Aeronave:</b> {self.manifesto.get('aeronave', 'N/A')}
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
            "Digite o <b>REMETENTE</b> e os <b>ÚLTIMOS DÍGITOS</b> do n° do volume para conferir:"
        )
        group_layout.addWidget(lbl_instrucao)
        
        # Campo Remetente
        remetente_layout = QHBoxLayout()
        remetente_layout.addWidget(QLabel("Remetente:"))
        
        self.txt_remetente = QLineEdit()
        self.txt_remetente.setPlaceholderText("Ex: PAMALS, CABW")
        self.txt_remetente.setMaximumWidth(200)
        self.txt_remetente.textChanged.connect(self.atualizar_instrucao_digitos)
        self.txt_remetente.returnPressed.connect(self.focar_digitos)
        remetente_layout.addWidget(self.txt_remetente)
        
        remetente_layout.addStretch()
        group_layout.addLayout(remetente_layout)
        
        # Campo Últimos Dígitos
        digitos_layout = QHBoxLayout()
        
        self.lbl_digitos = QLabel("Últimos 4 dígitos:")
        digitos_layout.addWidget(self.lbl_digitos)
        
        self.txt_digitos = QLineEdit()
        self.txt_digitos.setPlaceholderText("Digite os últimos dígitos")
        self.txt_digitos.setMaximumWidth(200)
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
            "💡 <i>Dica: Para CABW use 7 dígitos. Para outros remetentes, 4 dígitos.</i>"
        )
        lbl_dica.setStyleSheet("color: #666; font-size: 11px;")
        group_layout.addWidget(lbl_dica)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def criar_area_resultados(self, layout):
        """Cria a área de exibição de resultados"""
        group = QGroupBox("📦 Resultado da Busca")
        group_layout = QVBoxLayout()
        
        self.txt_resultado = QTextEdit()
        self.txt_resultado.setReadOnly(True)
        self.txt_resultado.setMinimumHeight(200)
        self.txt_resultado.setMaximumHeight(300)
        self.txt_resultado.setStyleSheet("""
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        group_layout.addWidget(self.txt_resultado)
        
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
        
        if remetente == 'CABW':
            self.lbl_digitos.setText("Últimos 7 dígitos:")
            self.txt_digitos.setPlaceholderText("Digite os últimos 7 dígitos")
        else:
            self.lbl_digitos.setText("Últimos 4 dígitos:")
            self.txt_digitos.setPlaceholderText("Digite os últimos 4 dígitos")
            
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
        elif len(volumes) == 1:
            # ENCONTRADO ÚNICO
            self.processar_volume_unico(volumes[0])
        else:
            # MÚLTIPLOS VOLUMES (raro, mas possível)
            self.exibir_multiplos_volumes(volumes)
            
    def exibir_nao_encontrado(self, remetente: str, digitos: str):
        """Exibe mensagem de volume não encontrado"""
        resultado = f"""
╔══════════════════════════════════════════════════════════════╗
║                     ❌ VOLUME NÃO ENCONTRADO                  ║
╚══════════════════════════════════════════════════════════════╝

Remetente informado: {remetente}
Últimos dígitos: {digitos}

Este volume NÃO está no manifesto {self.manifesto['numero_manifesto']}.

Opções:
1. Verificar se digitou corretamente
2. Conferir se o volume pertence a outro manifesto
3. Registrar como volume extra (não previsto)

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
        
    def processar_volume_unico(self, volume: dict):
        """Processa volume único encontrado"""
        # Verificar se tem múltiplas caixas
        caixas = obter_caixas(volume['id'])
        
        if volume['quantidade_expedida'] == 1:
            # Volume simples (1 caixa)
            self.processar_volume_simples(volume, caixas[0])
        else:
            # Volume com múltiplas caixas
            self.processar_volume_multiplo(volume, caixas)
            
    def processar_volume_simples(self, volume: dict, caixa: dict):
        """Processa volume com apenas 1 caixa"""
        if caixa['status'] == 'RECEBIDA':
            # Já foi recebida
            resultado = f"""
╔══════════════════════════════════════════════════════════════╗
║                ⚠️  VOLUME JÁ FOI RECEBIDO                    ║
╚══════════════════════════════════════════════════════════════╝

N° Volume: {volume['numero_volume']}
Remetente: {volume['remetente']} → Destinatário: {volume['destinatario']}

Quantidade: 1 de 1 caixa ✅
Peso: {volume['peso_total']} kg | Cubagem: {volume['cubagem']} m³

Status: JÁ RECEBIDA em {caixa['data_hora_recepcao'][:16]}
Por: {caixa['usuario_conferente']}
"""
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
        else:
            # Marcar como recebida
            marcar_caixa_recebida(volume['id'], caixa['numero_caixa'], "Usuário")
            
            resultado = f"""
╔══════════════════════════════════════════════════════════════╗
║                   ✅ VOLUME RECEBIDO COM SUCESSO              ║
╚══════════════════════════════════════════════════════════════╝

N° Volume: {volume['numero_volume']}
Remetente: {volume['remetente']} → Destinatário: {volume['destinatario']}

Quantidade: 1 de 1 caixa ✅
Peso: {volume['peso_total']} kg | Cubagem: {volume['cubagem']} m³
Prioridade: {volume['prioridade']}

✅ RECEBIDO AGORA ({datetime.now().strftime('%H:%M:%S')})
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
            
            # Atualizar resumo
            self.atualizar_resumo()
        
        self.txt_resultado.setText(resultado)
        
        # Limpar campos para próxima conferência
        self.txt_remetente.clear()
        self.txt_digitos.clear()
        self.txt_remetente.setFocus()
        
    def processar_volume_multiplo(self, volume: dict, caixas: list):
        """Processa volume com múltiplas caixas"""
        # Contar recebidas e não recebidas
        recebidas = [c for c in caixas if c['status'] == 'RECEBIDA']
        nao_recebidas = [c for c in caixas if c['status'] == 'NÃO RECEBIDA']
        
        # Mostrar diálogo
        dialog = VolumeMultiploDialog(volume, caixas, self)
        if dialog.exec_() == QDialog.Accepted:
            self.atualizar_resumo()
            
            # Mostrar resumo do que foi feito
            resultado = f"""
╔══════════════════════════════════════════════════════════════╗
║               ✅ VOLUME MÚLTIPLO PROCESSADO                   ║
╚══════════════════════════════════════════════════════════════╝

N° Volume: {volume['numero_volume']}
Remetente: {volume['remetente']} → Destinatário: {volume['destinatario']}

Total de caixas: {volume['quantidade_expedida']}
Recebidas agora: {dialog.quantidade_marcada}
Total recebidas: {len(recebidas) + dialog.quantidade_marcada}/{volume['quantidade_expedida']}

Status: {'✅ COMPLETO' if len(recebidas) + dialog.quantidade_marcada == volume['quantidade_expedida'] else '⚠️ PARCIAL'}
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
        
        # Limpar campos
        self.txt_remetente.clear()
        self.txt_digitos.clear()
        self.txt_remetente.setFocus()
        
    def exibir_multiplos_volumes(self, volumes: list):
        """Exibe quando múltiplos volumes são encontrados (raro)"""
        resultado = f"""
╔══════════════════════════════════════════════════════════════╗
║              ⚠️  MÚLTIPLOS VOLUMES ENCONTRADOS                ║
╚══════════════════════════════════════════════════════════════╝

Foram encontrados {len(volumes)} volumes com estes dígitos:

"""
        for i, vol in enumerate(volumes, 1):
            resultado += f"{i}. {vol['numero_volume']} ({vol['remetente']} → {vol['destinatario']})\n"
        
        resultado += "\nPor favor, seja mais específico ou confira manualmente."
        
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
<b>Total de volumes:</b> {total_vol}<br>
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
        """Finaliza a conferência"""
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
        
        # Finalizar
        finalizar_conferencia(self.manifesto_id)
        self.conferencia_finalizada.emit()
        
        QMessageBox.information(
            self,
            "✅ Conferência Finalizada",
            f"Conferência finalizada com sucesso!\n\n"
            f"Recebidas: {rec}/{exp} caixas ({stats['percentual_recebido']:.1f}%)"
        )
        
        self.close()


class VolumeMultiploDialog(QDialog):
    """Diálogo para conferir volume com múltiplas caixas"""
    
    def __init__(self, volume: dict, caixas: list, parent=None):
        super().__init__(parent)
        self.volume = volume
        self.caixas = caixas
        self.quantidade_marcada = 0
        self.init_ui()
        
    def init_ui(self):
        """Inicializa a interface"""
        self.setWindowTitle("Volume com Múltiplas Caixas")
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
            f"<b>Quantidade Expedida:</b> {self.volume['quantidade_expedida']} caixas<br>"
            f"<b>Peso Total:</b> {self.volume['peso_total']} kg | "
            f"<b>Cubagem:</b> {self.volume['cubagem']} m³"
        )
        info.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        layout.addWidget(info)
        
        # Status atual
        layout.addWidget(QLabel("<b>Status de Recebimento:</b>"))
        
        # Lista de caixas
        self.checkboxes = []
        for caixa in self.caixas:
            cb = QCheckBox(
                f"Caixa {caixa['numero_caixa']} de {self.volume['quantidade_expedida']}"
            )
            
            if caixa['status'] == 'RECEBIDA':
                cb.setChecked(True)
                cb.setEnabled(False)
                cb.setText(cb.text() + f" ✅ (Recebida em {caixa['data_hora_recepcao'][:16]})")
            
            self.checkboxes.append((cb, caixa))
            layout.addWidget(cb)
        
        # Opção rápida
        layout.addWidget(QLabel("<b>Ou informe quantidade:</b>"))
        
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Quantas caixas foram recebidas agora?"))
        
        self.spin_qty = QSpinBox()
        self.spin_qty.setMinimum(0)
        nao_recebidas = len([c for c in self.caixas if c['status'] == 'NÃO RECEBIDA'])
        self.spin_qty.setMaximum(nao_recebidas)
        self.spin_qty.setValue(nao_recebidas)
        qty_layout.addWidget(self.spin_qty)
        
        layout.addLayout(qty_layout)
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        
        btn_confirmar = QPushButton("✅ Confirmar Recebimento")
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
        """Confirma o recebimento das caixas"""
        # Usar quantidade do spinner
        quantidade = self.spin_qty.value()
        
        if quantidade > 0:
            marcar_volume_recebido(self.volume['id'], quantidade, "Usuário")
            self.quantidade_marcada = quantidade
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Aviso",
                "Selecione pelo menos uma caixa!"
            ) 