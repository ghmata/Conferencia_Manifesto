""" 
Sistema de Conferência de Manifestos de Cargas - CAN
Arquivo: main.py
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from src.ui.main_window import MainWindow
from src.database import init_database

def main():
    """Função principal do sistema"""
    # Inicializar banco de dados
    init_database()
    
    # Configurar aplicação
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Habilitar High DPI
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Criar e exibir janela principal
    window = MainWindow()
    window.show()
    
    # Executar aplicação
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()