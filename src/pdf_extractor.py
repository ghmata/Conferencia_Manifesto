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
            
            # Extrair volumes (destinatário PAMALS e variações)
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
        
        # Número do manifesto - busca no início do documento
        match = re.search(r'Manifesto:\s*(?:Página\s*)?(\d{12})', texto, re.IGNORECASE)
        if match:
            dados['numero_manifesto'] = match.group(1)
        else:
            # Tenta buscar só o número de 12 dígitos no início
            match = re.search(r'^(\d{12})', texto, re.MULTILINE)
            if match:
                dados['numero_manifesto'] = match.group(1)
        
        # Data - NÃO extrair do PDF, será preenchida com data atual
        # dados['data_manifesto'] será None aqui
        
        # Terminal Origem
        match = re.search(r'TERMINAL DE ORIGEM:\s*([A-Z\-]+)', texto, re.IGNORECASE)
        if match:
            dados['terminal_origem'] = match.group(1).strip()
        else:
            # Tenta buscar PCAN-XX ou TCTL-XX
            match = re.search(r'((?:PCAN|TCTL)-[A-Z]{2})', texto)
            if match:
                dados['terminal_origem'] = match.group(1)
        
        # Terminal Destino
        match = re.search(r'TERMINAL DE DESTINO:\s*([A-Z\-]+)', texto, re.IGNORECASE)
        if match:
            dados['terminal_destino'] = match.group(1).strip()
        else:
            # Busca o segundo PCAN-XX ou TCTL-XX
            matches = re.findall(r'((?:PCAN|TCTL)-[A-Z]{2})', texto)
            if len(matches) >= 2:
                dados['terminal_destino'] = matches[1]
        
        # Missão
        match = re.search(r'MISSÃO:\s*([A-Z0-9\s]+?)(?:\n|V\.)', texto, re.IGNORECASE)
        if match:
            dados['missao'] = match.group(1).strip()
        else:
            # Busca FAB seguido de números ou "Terrestre"
            match = re.search(r'(FAB\s+\d+|Terrestre)', texto)
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
    
    def _padronizar_remetente(self, remetente: str) -> str:
        """
        Padroniza o nome do remetente, priorizando palavras-chave específicas
        """
        rem = remetente.upper().strip()
        
        # Regras de padronização
        regras = [
            ('CABW', 'CABW'),
            ('CABE', 'CABE'),
            ('BACO', 'BACO'),  # Captura BACO/ESUP, SUP BACO, BACOESUP, etc
            ('BACG', 'BACG'),
            ('GAC-PAC', 'GAC-PAC'),
            ('GACPAC', 'GAC-PAC'),
            ('BAGL', 'BAGL'),
            ('CTLA', 'CTLA'),
            ('CLTA', 'CTLA'),  # Correção comum
            ('BAAN', 'BAAN'),
            ('BASP', 'BASP'),
            ('BANT', 'BANT'),
        ]
        
        for palavra_chave, padrao in regras:
            if palavra_chave in rem:
                return padrao
        
        # Se não encontrou nenhuma regra, retorna o primeiro termo válido
        partes = rem.split()
        if partes:
            return partes[0]
        
        return rem
    
    def _padronizar_destinatario(self, destinatario: str) -> str:
        """
        Padroniza o destinatário
        """
        dest = destinatario.upper().strip()
        
        # Se contém PAMALS ou PAMA, padronizar
        if 'PAMALS' in dest or ('PAMA' in dest and 'LS' in dest):
            return 'PAMALS'
        
        return dest
    
    def _e_destinatario_pamals(self, destinatario: str) -> bool:
        """
        Verifica se o destinatário é PAMALS ou suas variações
        Aceita: PAMALS, PAMA-LS, LS PAMA-LS, etc
        """
        if not destinatario:
            return False
        
        dest = destinatario.upper().strip()
        
        # Remover espaços extras
        dest = re.sub(r'\s+', ' ', dest)
        
        # Variações aceitas
        variacoes = [
            'PAMALS',
            'PAMA-LS',
            'PAMA LS',
            'LS PAMA-LS',
            'LS PAMA LS',
            'PAMA - LS',
            'LS PAMA - LS'
        ]
        
        # Verificar correspondência exata
        if dest in variacoes:
            return True
        
        # Verificar se contém PAMA e LS (mais flexível)
        if 'PAMA' in dest and 'LS' in dest:
            return True
        
        return False
    
    def _extrair_volumes(self, texto: str) -> List[Dict]:
        """
        Extrai informações dos volumes do manifesto
        IMPORTANTE: Apenas volumes onde DESTINATÁRIO é PAMALS (ou variações)
        """
        volumes = []
        
        # Dividir texto em linhas
        linhas = texto.split('\n')
        
        # Debug - IMPORTANTE: Dados extraídos são inseridos imediatamente no banco
        # Não há cache ou armazenamento temporário
        print(f"\n{'='*80}")
        print(f"EXTRAÇÃO EM TEMPO REAL - Formato padrão de tabela")
        print(f"{'='*80}\n")
        
        for i, linha in enumerate(linhas):
            # Ignorar linhas de cabeçalho e rodapé
            if any(palavra in linha.upper() for palavra in ['MANIFESTO', 'PÁGINA', 'TOTAIS', 'ENTREGUE', 'RECEBIDO']):
                continue
            
            # Buscar linha que contenha número de volume (padrão: XXX.../XXXX)
            if re.search(r'\d{12}/\d{4}', linha):
                partes = linha.split()
                
                if len(partes) < 3:
                    continue
                
                # Extrair componentes
                remetente = None
                destinatario = None
                numero_volume = None
                peso = None
                cubagem = None
                quantidade_exp = 1  # Default
                prioridade = None
                tipo_material = None
                
                # 1. Encontrar número de volume
                for j, parte in enumerate(partes):
                    if re.match(r'\d{12}/\d{4}', parte):
                        numero_volume_base = parte
                        
                        # Verificar se tem intervalo (-XXXX) para o número do volume
                        if j < len(partes) - 1 and partes[j + 1].startswith('-'):
                            prox = partes[j + 1]
                            # Tem intervalo: /0001-0004
                            numero_volume = numero_volume_base + prox
                        else:
                            numero_volume = numero_volume_base
                        
                        # CORREÇÃO CRÍTICA: Buscar a quantidade EXP diretamente da coluna
                        # A quantidade está localizada após o tipo de material e antes da prioridade
                        # Padrão: ... [TIPO_MATERIAL] [QUANTIDADE_EXP] [QUANTIDADE_REC] [PRIORIDADE]
                        
                        # Buscar a posição da prioridade (último número de 2 dígitos)
                        idx_prioridade = None
                        for idx, p in enumerate(partes):
                            if re.match(r'^\d{2}$', p):
                                idx_prioridade = idx
                        
                        if idx_prioridade is not None and idx_prioridade >= 2:
                            # A quantidade EXP está 2 posições antes da prioridade
                            # [..., quantidade_exp, quantidade_rec, prioridade]
                            if idx_prioridade - 2 >= 0:
                                quant_str = partes[idx_prioridade - 2]
                                if re.match(r'^\d+$', quant_str):
                                    quantidade_exp = int(quant_str)
                        
                        # ALTERNATIVA MELHORADA: Procurar por padrão específico da tabela
                        # Buscar por números inteiros entre o número do volume e a prioridade
                        # que não sejam decimais (peso/cubagem) e não sejam a prioridade
                        if quantidade_exp == 1:  # Se não encontrou pelo método anterior
                            for k in range(j + 1, len(partes)):
                                token = partes[k]
                                # Se é um número inteiro e não é a prioridade
                                if (re.match(r'^\d+$', token) and 
                                    (idx_prioridade is None or k != idx_prioridade) and
                                    not re.match(r'^\d+[,\.]\d+$', token)):
                                    # Verificar se não é um número de volume
                                    if not re.match(r'\d{12}/\d{4}', token):
                                        potencial_qtd = int(token)
                                        if 1 <= potencial_qtd <= 999:  # Quantidade razoável
                                            quantidade_exp = potencial_qtd
                                            break
                        
                        # Destinatário está ANTES do número de volume
                        if j > 0:
                            destinatario = partes[j - 1]
                            
                            # Padronizar destinatário
                            destinatario = self._padronizar_destinatario(destinatario)
                            
                            # Remetente é tudo antes do destinatário
                            remetente_partes = []
                            for k in range(j - 1):
                                palavra = partes[k]
                                if re.match(r'^\d+[,\.]\d+$', palavra) or re.match(r'^\d{12}', palavra):
                                    break
                                remetente_partes.append(palavra)
                            
                            if remetente_partes:
                                remetente_bruto = ' '.join(remetente_partes)
                                # Padronizar remetente
                                remetente = self._padronizar_remetente(remetente_bruto)
                        
                        # Peso e cubagem DEPOIS do número
                        if j < len(partes) - 2:
                            for m in range(j + 1, min(j + 8, len(partes))):
                                valor = partes[m]
                                if re.match(r'^\d+[,\.]\d+$', valor):
                                    if peso is None:
                                        peso = self._converter_decimal(valor)
                                    elif cubagem is None:
                                        cubagem = self._converter_decimal(valor)
                                        break
                        
                        # Tipo de material
                        if 'Aeronáutico' in linha or 'Aeronautico' in linha:
                            tipo_material = 'Aeronáutico'
                        elif 'Sem Restrições' in linha or 'Sem Restricoes' in linha or 'Sem Reestições' in linha:
                            tipo_material = 'Sem Restrições'
                        elif 'Gás Comprimido' in linha or 'Gas Comprimido' in linha:
                            tipo_material = 'Gás Comprimido'
                        else:
                            tipo_material = 'Geral'
                        
                        # Prioridade já foi encontrada acima
                        if idx_prioridade is not None:
                            prioridade = partes[idx_prioridade]
                        
                        break
                
                # Verificar se encontrou dados essenciais
                if not numero_volume or not destinatario:
                    continue
                
                # Se não encontrou remetente, usar "DESCONHECIDO"
                if not remetente or remetente.strip() == '':
                    remetente = "DESCONHECIDO"
                
                # FILTRO: Verificar se destinatário é PAMALS (ou variações)
                if not self._e_destinatario_pamals(destinatario):
                    print(f"❌ IGNORADO - Dest: '{destinatario}' não é PAMALS")
                    continue
                
                print(f"✅ EXTRAÍDO - Rem: '{remetente}' | Dest: '{destinatario}' | Vol: {numero_volume} | Qtd: {quantidade_exp}")
                
                volume = {
                    'remetente': remetente.strip(),
                    'destinatario': destinatario.strip(),
                    'numero_volume': numero_volume,
                    'quantidade_expedida': quantidade_exp,
                    'quantidade_recebida': 0,
                    'peso_total': peso,
                    'cubagem': cubagem,
                    'prioridade': prioridade,
                    'tipo_material': tipo_material,
                    'embalagem': 'CAIXA'
                }
                volumes.append(volume)
        
        print(f"\n{'='*80}")
        print(f"EXTRAÇÃO CONCLUÍDA: {len(volumes)} volumes (números de volume)")
        print(f"Total de CAIXAS: {sum(v['quantidade_expedida'] for v in volumes)}")
        print(f"Obs: Total de volumes = soma de todos os nºs de volume + caixas adicionais")
        print(f"{'='*80}\n")
        
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
        
        # Data não é mais obrigatória aqui (será preenchida automaticamente)
        
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
        IMPORTANTE: Extrai apenas os dígitos ANTES da barra "/"
        
        Exemplo: 251381004311/0001
        - 4 dígitos: "4311" (últimos 4 antes da /)
        - 7 dígitos: "1004311" (últimos 7 antes da /)
        
        Os números DEPOIS da / referem-se à identificação de caixas (0001-0004)
        """
        # Pegar apenas a parte ANTES da barra
        if '/' in numero_volume:
            parte_antes_barra = numero_volume.split('/')[0]
        else:
            parte_antes_barra = numero_volume
        
        # Remover tudo exceto números
        apenas_numeros = re.sub(r'\D', '', parte_antes_barra)
        
        # Retornar últimos N dígitos
        return apenas_numeros[-quantidade:] if len(apenas_numeros) >= quantidade else apenas_numeros
    
    @staticmethod
    def determinar_regra_busca(remetente: str) -> int:
        """
        Determina quantos dígitos usar na busca baseado no remetente
        CABW e CABE: 7 dígitos
        Outros: 4 dígitos
        """
        rem = remetente.upper()
        return 7 if ('CABW' in rem or 'CABE' in rem) else 4


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
        'data_manifesto': datetime.now().strftime("%d/%m/%Y"),  # Data atual
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
            'remetente': 'AFA',
            'destinatario': 'PAMALS',
            'numero_volume': '251374000524/0001',
            'quantidade_expedida': 4,
            'quantidade_recebida': 0,
            'peso_total': 20.0,
            'cubagem': 0.190,
            'prioridade': '04',
            'tipo_material': 'Aeronáutico',
            'embalagem': 'CAIXA'
        },
        {
            'remetente': 'BACO / BACO',
            'destinatario': 'PAMALS',
            'numero_volume': '251386000550/0001',
            'quantidade_expedida': 4,
            'quantidade_recebida': 0,
            'peso_total': 219.5,
            'cubagem': 125.484,
            'prioridade': '06',
            'tipo_material': 'Sem Restrições',
            'embalagem': 'CAIXA'
        }
    ]
    
    return dados_manifesto, volumes