"""
Sistema de Conferência de Manifestos - Diálogo Novo Manifesto
Arquivo: src/ui/novo_manifesto_dialog.py
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFileDialog, QMessageBox,
                             QGroupBox, QFormLayout, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from pathlib import Path
from datetime import datetime

from src.database import criar_manifesto, adicionar_volume
from src.pdf_extractor import extrair_manifesto_pdf


class NovoManifestoDialog(QDialog):
    """Diálogo para criar novo manifesto"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf_path = None
        self.dados_manifesto = None
        self.volumes = []
        self.init_ui()
        
    def init_ui(self):
        """Inicializa a interface"""
        self.setWindowTitle("Novo Manifesto")
        self.setModal(True)
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Título
        titulo = QLabel("📦 Registrar Novo Manifesto")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        titulo.setFont(font)
        layout.addWidget(titulo)
        
        # Seção 1: Importar PDF
        group_pdf = QGroupBox("1. Importar PDF do Manifesto")
        group_pdf_layout = QVBoxLayout()
        
        pdf_layout = QHBoxLayout()
        self.pdf_label = QLabel("Nenhum arquivo selecionado")
        self.pdf_label.setStyleSheet("color: #666; font-style: italic;")
        pdf_layout.addWidget(self.pdf_label)
        
        btn_selecionar = QPushButton("📁 Selecionar PDF")
        btn_selecionar.clicked.connect(self.selecionar_pdf)
        pdf_layout.addWidget(btn_selecionar)
        
        group_pdf_layout.addLayout(pdf_layout)
        
        btn_extrair = QPushButton("🔍 Extrair Dados do PDF")
        btn_extrair.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        btn_extrair.clicked.connect(self.extrair_dados)
        group_pdf_layout.addWidget(btn_extrair)
        
        group_pdf.setLayout(group_pdf_layout)
        layout.addWidget(group_pdf)
        
        # Seção 2: Dados do Manifesto (CAMPOS REDUZIDOS)
        group_dados = QGroupBox("2. Dados do Manifesto")
        form_layout = QFormLayout()
        
        self.txt_numero = QLineEdit()
        self.txt_numero.setPlaceholderText("Ex: 202531000635")
        self.txt_numero.setReadOnly(True)  # Somente leitura, vem do PDF
        form_layout.addRow("Nº Manifesto*:", self.txt_numero)
        
        # Data preenchida automaticamente
        self.txt_data = QLineEdit()
        self.txt_data.setReadOnly(True)
        self.txt_data.setText(datetime.now().strftime("%d/%m/%Y"))
        form_layout.addRow("Data*:", self.txt_data)
        
        self.txt_destino = QLineEdit()
        self.txt_destino.setPlaceholderText("Ex: PCAN-LS")
        self.txt_destino.setReadOnly(True)  # Vem do PDF
        form_layout.addRow("Destino*:", self.txt_destino)
        
        # REMOVIDOS: Origem, Missão, Aeronave (não são necessários)
        
        group_dados.setLayout(form_layout)
        layout.addWidget(group_dados)
        
        # Seção 3: Status da Extração
        self.group_status = QGroupBox("3. Status da Extração")
        self.group_status.setVisible(False)
        status_layout = QVBoxLayout()
        
        self.txt_status = QTextEdit()
        self.txt_status.setReadOnly(True)
        self.txt_status.setMaximumHeight(150)
        status_layout.addWidget(self.txt_status)
        
        self.group_status.setLayout(status_layout)
        layout.addWidget(self.group_status)
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        
        self.btn_salvar = QPushButton("💾 Salvar Manifesto")
        self.btn_salvar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.btn_salvar.clicked.connect(self.salvar_manifesto)
        self.btn_salvar.setEnabled(False)
        btn_layout.addWidget(self.btn_salvar)
        
        layout.addLayout(btn_layout)
        
    def selecionar_pdf(self):
        """Abre diálogo para selecionar arquivo PDF"""
        arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Manifesto PDF",
            "",
            "PDF Files (*.pdf)"
        )
        
        if arquivo:
            self.pdf_path = arquivo
            self.pdf_label.setText(Path(arquivo).name)
            self.pdf_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
    def extrair_dados(self):
        """Extrai dados do PDF selecionado"""
        if not self.pdf_path:
            QMessageBox.warning(
                self,
                "Aviso",
                "Por favor, selecione um arquivo PDF primeiro."
            )
            return
        
        try:
            # Mostrar progresso
            self.txt_status.setText("⏳ Processando PDF...")
            self.group_status.setVisible(True)
            
            # Extrair dados
            self.dados_manifesto, self.volumes, erros = extrair_manifesto_pdf(
                self.pdf_path
            )
            
            # Debug: mostrar o que foi extraído
            print(f"DEBUG - Dados extraídos:")
            print(f"  Manifesto: {self.dados_manifesto}")
            print(f"  Volumes: {len(self.volumes)}")
            for v in self.volumes:
                print(f"    - {v['remetente']} → {v['destinatario']}: {v['numero_volume']}")
            
            # Preencher campos (apenas os que existem agora)
            if self.dados_manifesto:
                self.txt_numero.setText(
                    self.dados_manifesto.get('numero_manifesto', '')
                )
                
                # Data SEMPRE usa a data atual (data de inclusão no sistema)
                self.txt_data.setText(datetime.now().strftime("%d/%m/%Y"))
                
                self.txt_destino.setText(
                    self.dados_manifesto.get('terminal_destino', '')
                )
            
            # Mostrar status
            status_text = f"✅ Extração concluída!\n\n"
            status_text += f"📦 Volumes encontrados (PAMALS): {len(self.volumes)}\n\n"
            
            if self.volumes:
                status_text += "Volumes extraídos:\n"
                for vol in self.volumes:
                    status_text += f"  • {vol['remetente']} → {vol['destinatario']}: {vol['numero_volume']}\n"
                status_text += "\n"
            
            if erros:
                status_text += "⚠️ Avisos:\n"
                for erro in erros:
                    status_text += f"  • {erro}\n"
            else:
                status_text += "✅ Nenhum problema encontrado"
                
            self.txt_status.setText(status_text)
            
            # Habilitar botão salvar se tudo OK
            if self.dados_manifesto and self.volumes:
                self.btn_salvar.setEnabled(True)
                
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Dados extraídos com sucesso!\n"
                    f"Volumes com DESTINATÁRIO PAMALS: {len(self.volumes)}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Atenção",
                    f"Extração concluída, mas:\n"
                    f"- Volumes encontrados: {len(self.volumes)}\n"
                    f"- Erros: {len(erros)}\n\n"
                    f"Verifique o status da extração."
                )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao extrair dados do PDF:\n{str(e)}"
            )
            
    def validar_campos(self) -> bool:
        """Valida os campos obrigatórios"""
        if not self.txt_numero.text().strip():
            QMessageBox.warning(
                self,
                "Campo Obrigatório",
                "O número do manifesto é obrigatório."
            )
            return False
            
        if not self.txt_data.text().strip():
            QMessageBox.warning(
                self,
                "Campo Obrigatório",
                "A data do manifesto é obrigatória."
            )
            return False
            
        if not self.txt_destino.text().strip():
            QMessageBox.warning(
                self,
                "Campo Obrigatório",
                "O terminal de destino é obrigatório."
            )
            return False
            
        return True
        
    def salvar_manifesto(self):
        """Salva o manifesto no banco de dados"""
        if not self.validar_campos():
            return
        
        if not self.volumes:
            reply = QMessageBox.question(
                self,
                "Confirmação",
                "Nenhum volume foi extraído. Deseja continuar mesmo assim?\n"
                "Você poderá adicionar volumes manualmente depois.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        try:
            # Criar manifesto (SEM origem, missão e aeronave)
            manifesto_id = criar_manifesto(
                numero=self.txt_numero.text().strip(),
                data=self.txt_data.text().strip(),
                origem='',  # Não é mais necessário
                destino=self.txt_destino.text().strip(),
                missao=None,  # Removido
                aeronave=None,  # Removido
                pdf_path=self.pdf_path
            )
            
            # Adicionar volumes
            for volume in self.volumes:
                adicionar_volume(
                    manifesto_id=manifesto_id,
                    remetente=volume['remetente'],
                    destinatario=volume['destinatario'],
                    numero_volume=volume['numero_volume'],
                    quantidade_exp=volume['quantidade_expedida'],
                    peso=volume.get('peso_total'),
                    cubagem=volume.get('cubagem'),
                    prioridade=volume.get('prioridade'),
                    tipo_material=volume.get('tipo_material'),
                    embalagem=volume.get('embalagem')
                )
            
            QMessageBox.information(
                self,
                "Sucesso",
                f"Manifesto {self.txt_numero.text()} salvo com sucesso!\n"
                f"Total de volumes: {len(self.volumes)}"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao salvar manifesto:\n{str(e)}"
            )