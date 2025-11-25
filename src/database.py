"""
Sistema de Conferência de Manifestos - Módulo de Banco de Dados
Arquivo: src/database.py
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Caminho do banco de dados
DB_PATH = Path("data/database.db")

def init_database():
    """Inicializa o banco de dados criando as tabelas necessárias"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de manifestos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manifestos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_manifesto TEXT UNIQUE NOT NULL,
            data_manifesto DATE,
            terminal_origem TEXT,
            terminal_destino TEXT,
            missao TEXT,
            aeronave TEXT,
            pdf_path TEXT,
            status TEXT CHECK(status IN ('NÃO RECEBIDO', 'PARCIALMENTE RECEBIDO', 'TOTALMENTE RECEBIDO')) DEFAULT 'NÃO RECEBIDO',
            data_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_conferencia_inicio DATETIME,
            data_conferencia_fim DATETIME,
            usuario_responsavel TEXT
        )
    """)
    
    # Tabela de volumes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS volumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manifesto_id INTEGER NOT NULL,
            remetente TEXT NOT NULL,
            destinatario TEXT NOT NULL,
            numero_volume TEXT NOT NULL,
            quantidade_expedida INTEGER NOT NULL DEFAULT 1,
            quantidade_recebida INTEGER DEFAULT 0,
            peso_total REAL,
            cubagem REAL,
            prioridade TEXT,
            tipo_material TEXT,
            embalagem TEXT,
            status TEXT CHECK(status IN ('COMPLETO', 'PARCIAL', 'NÃO RECEBIDO', 'VOLUME EXTRA')) DEFAULT 'NÃO RECEBIDO',
            data_hora_primeira_recepcao DATETIME,
            data_hora_ultima_recepcao DATETIME,
            FOREIGN KEY (manifesto_id) REFERENCES manifestos(id),
            UNIQUE(manifesto_id, numero_volume)
        )
    """)
    
    # Tabela de caixas individuais
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS caixas_individuais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            volume_id INTEGER NOT NULL,
            numero_caixa INTEGER NOT NULL,
            status TEXT CHECK(status IN ('RECEBIDA', 'NÃO RECEBIDA')) DEFAULT 'NÃO RECEBIDA',
            data_hora_recepcao DATETIME,
            usuario_conferente TEXT,
            FOREIGN KEY (volume_id) REFERENCES volumes(id),
            UNIQUE(volume_id, numero_caixa)
        )
    """)
    
    # Tabela de logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manifesto_id INTEGER,
            acao TEXT NOT NULL,
            detalhes TEXT,
            usuario TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (manifesto_id) REFERENCES manifestos(id)
        )
    """)
    
    conn.commit()
    conn.close()

def get_connection():
    """Retorna uma conexão com o banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== MANIFESTOS ====================

def criar_manifesto(numero: str, data: str, origem: str, destino: str, 
                   missao: str = None, aeronave: str = None, pdf_path: str = None) -> int:
    """Cria um novo manifesto no banco de dados"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO manifestos (numero_manifesto, data_manifesto, terminal_origem, 
                               terminal_destino, missao, aeronave, pdf_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (numero, data, origem, destino, missao, aeronave, pdf_path))
    
    manifesto_id = cursor.lastrowid
    
    # Registrar log
    registrar_log(manifesto_id, "CRIAÇÃO", f"Manifesto {numero} registrado no sistema")
    
    conn.commit()
    conn.close()
    
    return manifesto_id

def listar_manifestos(filtro_status: str = None, filtro_data_inicio: str = None, 
                     filtro_data_fim: str = None) -> List[Dict]:
    """Lista todos os manifestos com filtros opcionais"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT m.*, 
               COUNT(DISTINCT v.id) as total_volumes,
               SUM(v.quantidade_expedida) as total_caixas_expedidas,
               SUM(v.quantidade_recebida) as total_caixas_recebidas
        FROM manifestos m
        LEFT JOIN volumes v ON m.id = v.manifesto_id
        WHERE 1=1
    """
    params = []
    
    if filtro_status:
        query += " AND m.status = ?"
        params.append(filtro_status)
    
    if filtro_data_inicio:
        query += " AND m.data_manifesto >= ?"
        params.append(filtro_data_inicio)
    
    if filtro_data_fim:
        query += " AND m.data_manifesto <= ?"
        params.append(filtro_data_fim)
    
    query += " GROUP BY m.id ORDER BY m.data_manifesto DESC, m.id DESC"
    
    cursor.execute(query, params)
    manifestos = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return manifestos

def obter_manifesto(manifesto_id: int) -> Optional[Dict]:
    """Obtém detalhes de um manifesto específico"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM manifestos WHERE id = ?", (manifesto_id,))
    manifesto = cursor.fetchone()
    
    conn.close()
    return dict(manifesto) if manifesto else None

def iniciar_conferencia(manifesto_id: int, usuario: str = "Sistema"):
    """Marca o início da conferência de um manifesto"""
    conn = get_connection()
    cursor = conn.cursor()
    
    agora = datetime.now().isoformat()
    cursor.execute("""
        UPDATE manifestos 
        SET data_conferencia_inicio = ?, usuario_responsavel = ?
        WHERE id = ?
    """, (agora, usuario, manifesto_id))
    
    registrar_log(manifesto_id, "INÍCIO CONFERÊNCIA", f"Usuário: {usuario}")
    
    conn.commit()
    conn.close()

def finalizar_conferencia(manifesto_id: int):
    """Finaliza a conferência e atualiza o status do manifesto"""
    conn = get_connection()
    cursor = conn.cursor()
    
    agora = datetime.now().isoformat()
    
    # Calcular status baseado nos volumes
    cursor.execute("""
        SELECT 
            COUNT(*) as total_volumes,
            SUM(quantidade_expedida) as total_expedido,
            SUM(quantidade_recebida) as total_recebido
        FROM volumes
        WHERE manifesto_id = ?
    """, (manifesto_id,))
    
    stats = cursor.fetchone()
    
    if stats['total_recebido'] == 0:
        status = 'NÃO RECEBIDO'
    elif stats['total_recebido'] == stats['total_expedido']:
        status = 'TOTALMENTE RECEBIDO'
    else:
        status = 'PARCIALMENTE RECEBIDO'
    
    cursor.execute("""
        UPDATE manifestos 
        SET data_conferencia_fim = ?, status = ?
        WHERE id = ?
    """, (agora, status, manifesto_id))
    
    registrar_log(manifesto_id, "FIM CONFERÊNCIA", 
                 f"Status: {status} ({stats['total_recebido']}/{stats['total_expedido']} caixas)")
    
    conn.commit()
    conn.close()

# ==================== VOLUMES ====================

def adicionar_volume(manifesto_id: int, remetente: str, destinatario: str,
                    numero_volume: str, quantidade_exp: int = 1,
                    peso: float = None, cubagem: float = None,
                    prioridade: str = None, tipo_material: str = None,
                    embalagem: str = None) -> int:
    """Adiciona um volume ao manifesto"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO volumes (manifesto_id, remetente, destinatario, numero_volume,
                           quantidade_expedida, peso_total, cubagem, prioridade,
                           tipo_material, embalagem)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (manifesto_id, remetente, destinatario, numero_volume, quantidade_exp,
          peso, cubagem, prioridade, tipo_material, embalagem))
    
    volume_id = cursor.lastrowid
    
    # Criar registros de caixas individuais
    for i in range(1, quantidade_exp + 1):
        cursor.execute("""
            INSERT INTO caixas_individuais (volume_id, numero_caixa)
            VALUES (?, ?)
        """, (volume_id, i))
    
    conn.commit()
    conn.close()
    
    return volume_id

def buscar_volume(manifesto_id: int, remetente: str, ultimos_digitos: str) -> List[Dict]:
    """Busca volume por remetente e últimos dígitos"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Padrão de busca: qualquer coisa + últimos dígitos
    padrao = f"%{ultimos_digitos}"
    
    cursor.execute("""
        SELECT * FROM volumes
        WHERE manifesto_id = ? 
        AND remetente = ?
        AND numero_volume LIKE ?
    """, (manifesto_id, remetente, padrao))
    
    volumes = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return volumes

def listar_volumes(manifesto_id: int) -> List[Dict]:
    """Lista todos os volumes de um manifesto"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM volumes
        WHERE manifesto_id = ?
        ORDER BY remetente, numero_volume
    """, (manifesto_id,))
    
    volumes = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return volumes

def obter_caixas(volume_id: int) -> List[Dict]:
    """Obtém todas as caixas individuais de um volume"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM caixas_individuais
        WHERE volume_id = ?
        ORDER BY numero_caixa
    """, (volume_id,))
    
    caixas = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return caixas

def marcar_caixa_recebida(volume_id: int, numero_caixa: int, 
                         usuario: str = "Sistema"):
    """Marca uma caixa individual como recebida"""
    conn = get_connection()
    cursor = conn.cursor()
    
    agora = datetime.now().isoformat()
    
    # Atualizar caixa
    cursor.execute("""
        UPDATE caixas_individuais
        SET status = 'RECEBIDA', data_hora_recepcao = ?, usuario_conferente = ?
        WHERE volume_id = ? AND numero_caixa = ?
    """, (agora, usuario, volume_id, numero_caixa))
    
    # Atualizar contadores do volume
    cursor.execute("""
        UPDATE volumes
        SET quantidade_recebida = (
            SELECT COUNT(*) FROM caixas_individuais
            WHERE volume_id = ? AND status = 'RECEBIDA'
        ),
        data_hora_ultima_recepcao = ?
        WHERE id = ?
    """, (volume_id, agora, volume_id))
    
    # Atualizar primeira recepção se for a primeira
    cursor.execute("""
        UPDATE volumes
        SET data_hora_primeira_recepcao = ?
        WHERE id = ? AND data_hora_primeira_recepcao IS NULL
    """, (agora, volume_id))
    
    # Atualizar status do volume
    cursor.execute("""
        UPDATE volumes
        SET status = CASE
            WHEN quantidade_recebida = 0 THEN 'NÃO RECEBIDO'
            WHEN quantidade_recebida = quantidade_expedida THEN 'COMPLETO'
            ELSE 'PARCIAL'
        END
        WHERE id = ?
    """, (volume_id,))
    
    conn.commit()
    conn.close()

def marcar_volume_recebido(volume_id: int, quantidade: int = None, 
                          usuario: str = "Sistema"):
    """Marca um volume como recebido (quantidade de caixas)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Se quantidade não especificada, marcar todas
    if quantidade is None:
        cursor.execute("SELECT quantidade_expedida FROM volumes WHERE id = ?", 
                      (volume_id,))
        quantidade = cursor.fetchone()['quantidade_expedida']
    
    # Obter caixas não recebidas
    cursor.execute("""
        SELECT numero_caixa FROM caixas_individuais
        WHERE volume_id = ? AND status = 'NÃO RECEBIDA'
        ORDER BY numero_caixa
        LIMIT ?
    """, (volume_id, quantidade))
    
    caixas = cursor.fetchall()
    
    conn.close()
    
    # Marcar cada caixa
    for caixa in caixas:
        marcar_caixa_recebida(volume_id, caixa['numero_caixa'], usuario)

# ==================== LOGS ====================

def registrar_log(manifesto_id: int, acao: str, detalhes: str = None, 
                 usuario: str = "Sistema"):
    """Registra uma ação no log"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO logs (manifesto_id, acao, detalhes, usuario)
        VALUES (?, ?, ?, ?)
    """, (manifesto_id, acao, detalhes, usuario))
    
    conn.commit()
    conn.close()

def obter_logs(manifesto_id: int) -> List[Dict]:
    """Obtém todos os logs de um manifesto"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM logs
        WHERE manifesto_id = ?
        ORDER BY timestamp DESC
    """, (manifesto_id,))
    
    logs = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return logs

# ==================== ESTATÍSTICAS ====================

def obter_estatisticas_manifesto(manifesto_id: int) -> Dict:
    """Retorna estatísticas detalhadas de um manifesto"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT v.id) as total_volumes,
            SUM(v.quantidade_expedida) as total_caixas_expedidas,
            SUM(v.quantidade_recebida) as total_caixas_recebidas,
            SUM(CASE WHEN v.status = 'COMPLETO' THEN 1 ELSE 0 END) as volumes_completos,
            SUM(CASE WHEN v.status = 'PARCIAL' THEN 1 ELSE 0 END) as volumes_parciais,
            SUM(CASE WHEN v.status = 'NÃO RECEBIDO' THEN 1 ELSE 0 END) as volumes_nao_recebidos,
            SUM(v.peso_total) as peso_total
        FROM volumes v
        WHERE v.manifesto_id = ?
    """, (manifesto_id,))
    
    stats = dict(cursor.fetchone())
    
    # Calcular percentual
    if stats['total_caixas_expedidas'] and stats['total_caixas_expedidas'] > 0:
        stats['percentual_recebido'] = (
            stats['total_caixas_recebidas'] / stats['total_caixas_expedidas'] * 100
        )
    else:
        stats['percentual_recebido'] = 0
    
    conn.close()
    return stats