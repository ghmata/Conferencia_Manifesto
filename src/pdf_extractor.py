"""
Sistema de Conferência de Manifestos - Extrator de PDF
Arquivo: src/pdf_extractor.py
"""

import re
import pdfplumber
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

class ManifestoExtractor:
    """Classe para extrair dados de manifestos em PDF"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.dados_manifesto = {}
        self.volumes = []
        
    def extrair(self) -> Tuple[Dict, List[Dict]]:
        """
        Extrai dados do manifesto
        Retorna: (dados_cabecalho, lista_volumes)
        """
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {self.pdf_path}")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            texto_completo = ""
            
            # Extrair texto de todas as páginas
            for pagina in pdf.pages:
                texto_completo += pagina.extract_text() + "\n"
            
            # Extrair dados do cabeçalho
            self.dados_manifesto = self._extrair_cabecalho(texto_completo)
            
            # Extrair volumes (apenas PAMALS como destinatário)
            self.volumes = self._extrair_volumes(texto_completo)
        
        return self.dados_manifesto, self.volumes
    
    def _extrair_cabecalho(self, texto: str) -> Dict:
        """Extrai informações do cabeçalho do manifesto"""
        dados = {
            'numero_manifesto': None,
            'data_manifesto': None,
            'terminal_origem': None,
            'terminal_destino': None,
            'missao': None,
            'aeronave': None
        }
        
        # Padrões específicos para o formato do PDF fornecido
        
        # Número do manifesto - busca no início do documento
        match = re.search(r'Manifesto:\s*(?:Página\s*)?(\d{12})', texto, re.IGNORECASE)
        if match:
            dados['numero_manifesto'] = match.group(1)
        else:
            # Tenta buscar só o número de 12 dígitos no início
            match = re.search(r'^(\d{12})', texto, re.MULTILINE)
            if match:
                dados['numero_manifesto'] = match.group(1)
        
        # Data - formato DD/MM/YYYY
        match = re.search(r'(\d{2}/\d{2}/\d{4})\s+\d{2}:\d{2}', texto)
        if match:
            dados['data_manifesto'] = match.group(1)
        
        # Terminal Origem
        match = re.search(r'TERMINAL DE ORIGEM:\s*([A-Z\-]+)', texto, re.IGNORECASE)
        if match:
            dados['terminal_origem'] = match.group(1).strip()
        else:
            # Tenta buscar PCAN-XX
            match = re.search(r'(PCAN-[A-Z]{2})', texto)
            if match:
                dados['terminal_origem'] = match.group(1)
        
        # Terminal Destino
        match = re.search(r'TERMINAL DE DESTINO:\s*([A-Z\-]+)', texto, re.IGNORECASE)
        if match:
            dados['terminal_destino'] = match.group(1).strip()
        else:
            # Busca o segundo PCAN-XX
            matches = re.findall(r'(PCAN-[A-Z]{2})', texto)
            if len(matches) >= 2:
                dados['terminal_destino'] = matches[1]
        
        # Missão
        match = re.search(r'MISSÃO:\s*([A-Z0-9\s]+?)(?:\n|V\.)', texto, re.IGNORECASE)
        if match:
            dados['missao'] = match.group(1).strip()
        else:
            # Busca FAB seguido de números
            match = re.search(r'(FAB\s+\d+)', texto)
            if match:
                dados['missao'] = match.group(1)
        
        # Aeronave
        match = re.search(r'AERONAVE:\s*([A-Z0-9\-]+)', texto, re.IGNORECASE)
        if match:
            dados['aeronave'] = match.group(1).strip()
        else:
            # Busca C-XX ou similar
            match = re.search(r'(C-\d+)', texto)
            if match:
                dados['aeronave'] = match.group(1)
        
        return dados
    
    def _extrair_volumes(self, texto: str) -> List[Dict]:
        """
        Extrai informações dos volumes do manifesto
        IMPORTANTE: Apenas volumes onde DESTINATÁRIO é PAMALS
        """
        volumes = []
        
        # Dividir texto em linhas
        linhas = texto.split('\n')
        
        # Padrão mais flexível para capturar volumes
        # Formato: REMETENTE DESTINATARIO NUMERO/VOLUME PESO CUBAGEM (resto)
        # Exemplo: PAMALS PAMASP 251381004311/0001 25,00 0,340 Sem Restrições 1 04
        
        for i, linha in enumerate(linhas):
            # Busca linhas que começam com letras maiúsculas (remetentes)
            if re.match(r'^[A-Z]{4,}', linha):
                # Tenta extrair dados da linha
                partes = linha.split()
                
                if len(partes) >= 4:
                    remetente = partes[0]
                    destinatario = partes[1]
                    
                    # FILTRO: Apenas volumes onde DESTINATÁRIO é PAMALS
                    if destinatario.upper() != 'PAMALS':
                        continue
                    
                    # Busca número de volume (formato: números/números)
                    numero_volume = None
                    peso = None
                    cubagem = None
                    quantidade_exp = 1
                    prioridade = None
                    
                    for parte in partes[2:]:
                        # Número de volume
                        if '/' in parte and numero_volume is None:
                            numero_volume = parte
                        # Peso (número com vírgula ou ponto)
                        elif re.match(r'^\d+[,\.]\d+$', parte) and peso is None:
                            peso = self._converter_decimal(parte)
                        # Cubagem (próximo número decimal após peso)
                        elif re.match(r'^\d+[,\.]\d+$', parte) and peso is not None and cubagem is None:
                            cubagem = self._converter_decimal(parte)
                        # Prioridade (2 dígitos no final)
                        elif re.match(r'^\d{2}$', parte):
                            prioridade = parte
                    
                    # Se encontrou dados essenciais, adiciona o volume
                    if numero_volume and remetente and destinatario:
                        volume = {
                            'remetente': remetente,
                            'destinatario': destinatario,
                            'numero_volume': numero_volume,
                            'quantidade_expedida': quantidade_exp,
                            'quantidade_recebida': 0,
                            'peso_total': peso,
                            'cubagem': cubagem,
                            'prioridade': prioridade,
                            'tipo_material': 'Sem Restrições',  # Padrão do PDF
                            'embalagem': 'CAIXA'
                        }
                        volumes.append(volume)
        
        return volumes
    
    def _converter_decimal(self, valor: str) -> float:
        """Converte string com vírgula/ponto para float"""
        try:
            valor = valor.replace(',', '.')
            return float(valor)
        except:
            return 0.0
    
    def validar_dados(self) -> List[str]:
        """
        Valida os dados extraídos
        Retorna lista de erros/avisos encontrados
        """
        erros = []
        
        # Validar cabeçalho
        if not self.dados_manifesto.get('numero_manifesto'):
            erros.append("Número do manifesto não encontrado")
        
        if not self.dados_manifesto.get('data_manifesto'):
            erros.append("Data do manifesto não encontrada")
        
        if not self.dados_manifesto.get('terminal_destino'):
            erros.append("Terminal de destino não encontrado")
        
        # Validar volumes
        if not self.volumes:
            erros.append("Nenhum volume com DESTINATÁRIO PAMALS foi encontrado")
        else:
            # Validar cada volume
            for i, volume in enumerate(self.volumes, 1):
                if not volume.get('remetente'):
                    erros.append(f"Volume {i}: Remetente não identificado")
                
                if not volume.get('numero_volume'):
                    erros.append(f"Volume {i}: Número do volume não identificado")
                
                if volume.get('quantidade_expedida', 0) <= 0:
                    erros.append(f"Volume {i}: Quantidade expedida inválida")
        
        return erros
    
    @staticmethod
    def extrair_ultimos_digitos(numero_volume: str, quantidade: int) -> str:
        """
        Extrai os últimos N dígitos de um número de volume
        Remove caracteres não numéricos
        """
        # Remover tudo exceto números
        apenas_numeros = re.sub(r'\D', '', numero_volume)
        
        # Retornar últimos N dígitos
        return apenas_numeros[-quantidade:] if len(apenas_numeros) >= quantidade else apenas_numeros
    
    @staticmethod
    def determinar_regra_busca(remetente: str) -> int:
        """
        Determina quantos dígitos usar na busca baseado no remetente
        CABW: 7 dígitos
        Outros: 4 dígitos
        """
        return 7 if remetente.upper() == 'CABW' else 4


# ==================== FUNÇÕES AUXILIARES ====================

def extrair_manifesto_pdf(pdf_path: str) -> Tuple[Dict, List[Dict], List[str]]:
    """
    Função helper para extrair dados de um PDF de manifesto
    Retorna: (dados_cabecalho, volumes, erros)
    """
    try:
        extractor = ManifestoExtractor(pdf_path)
        dados_manifesto, volumes = extractor.extrair()
        erros = extractor.validar_dados()
        
        return dados_manifesto, volumes, erros
    
    except Exception as e:
        return {}, [], [f"Erro ao processar PDF: {str(e)}"]


def criar_manifesto_exemplo() -> Tuple[Dict, List[Dict]]:
    """
    Cria dados de exemplo para testes (quando PDF não está disponível)
    """
    dados_manifesto = {
        'numero_manifesto': '202531000635',
        'data_manifesto': '24/11/2025',
        'terminal_origem': 'PCAN-GR',
        'terminal_destino': 'PCAN-LS',
        'missao': 'FAB 2309',
        'aeronave': 'C-95'
    }
    
    volumes = [
        {
            'remetente': 'PAMASP',
            'destinatario': 'PAMALS',
            'numero_volume': '251381004311/0001',
            'quantidade_expedida': 1,
            'quantidade_recebida': 0,
            'peso_total': 25.0,
            'cubagem': 0.340,
            'prioridade': '04',
            'tipo_material': 'Sem Restrições',
            'embalagem': 'CAIXA'
        },
        {
            'remetente': 'PAMASP',
            'destinatario': 'PAMALS',
            'numero_volume': '251381004341/0001',
            'quantidade_expedida': 1,
            'quantidade_recebida': 0,
            'peso_total': 17.0,
            'cubagem': 0.030,
            'prioridade': '04',
            'tipo_material': 'Sem Restrições',
            'embalagem': 'CAIXA'
        },
        {
            'remetente': 'PAMASP',
            'destinatario': 'PAMALS',
            'numero_volume': '251381004370/0001',
            'quantidade_expedida': 4,
            'quantidade_recebida': 0,
            'peso_total': 80.0,
            'cubagem': 0.240,
            'prioridade': '04',
            'tipo_material': 'Sem Restrições',
            'embalagem': 'CAIXA'
        },
        {
            'remetente': 'CABW',
            'destinatario': 'PAMALS',
            'numero_volume': '251381009999/0001',
            'quantidade_expedida': 3,
            'quantidade_recebida': 0,
            'peso_total': 45.0,
            'cubagem': 0.180,
            'prioridade': '02',
            'tipo_material': 'Sem Restrições',
            'embalagem': 'ENVELOPE'
        },
        {
            'remetente': 'PAMASP',
            'destinatario': 'PAMALS',
            'numero_volume': '251381004371/0001',
            'quantidade_expedida': 1,
            'quantidade_recebida': 0,
            'peso_total': 1.0,
            'cubagem': 0.010,
            'prioridade': '04',
            'tipo_material': 'Sem Restrições',
            'embalagem': 'ENVELOPE'
        },
        {
            'remetente': 'PAMASP',
            'destinatario': 'PAMALS',
            'numero_volume': '251381004375/0001',
            'quantidade_expedida': 1,
            'quantidade_recebida': 0,
            'peso_total': 1.0,
            'cubagem': 0.010,
            'prioridade': '04',
            'tipo_material': 'Sem Restrições',
            'embalagem': 'ENVELOPE'
        }
    ]
    
    return dados_manifesto, volumes