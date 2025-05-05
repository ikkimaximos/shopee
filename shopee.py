#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Extrator de Categorias da Shopee via API - Script para extrair todas as categorias 
do catálogo da Shopee BR usando a API interna e salvar em um arquivo CSV.

Autor: Claude
Data: Maio 2025
"""

import os
import time
import json
import requests
import pandas as pd
from tqdm import tqdm
import logging
import sqlalchemy
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extrator_api_shopee.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# URL base da API
API_BASE_URL = "https://seller.shopee.com.br/help/api/v3/global_category/list/"

# Headers para simular um navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://seller.shopee.com.br/edu/category-guide/",
    "Origin": "https://seller.shopee.com.br"
}

def obter_cookie_sessao():
    """
    Obtém cookies de sessão para usar na API.
    Aviso: Esta é uma função simplificada para exemplo. Em uma implementação real,
    você pode precisar de uma rotina mais robusta para autenticação.
    """
    try:
        # Fazer uma solicitação para a página principal para obter cookies
        session = requests.Session()
        resp = session.get("https://seller.shopee.com.br/edu/category-guide/", headers=HEADERS)
        if resp.status_code == 200:
            logger.info("Cookies de sessão obtidos com sucesso")
            return session.cookies.get_dict()
        else:
            logger.warning(f"Falha ao obter cookies: Status {resp.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Erro ao obter cookies: {str(e)}")
        return {}

def extrair_categorias_via_api():
    """
    Função principal para extrair todas as categorias da Shopee usando a API.
    
    Returns:
        list: Lista de dicionários com os dados das categorias
    """
    todas_categorias = []
    pagina_atual = 1
    tamanho_pagina = 100  # Número de resultados por página
    tem_mais_paginas = True
    
    # Obter cookies para a sessão
    cookies = obter_cookie_sessao()
    
    # Primeira requisição para descobrir o total de páginas
    try:
        params = {
            "page": 1,
            "size": tamanho_pagina
        }
        
        response = requests.get(
            API_BASE_URL,
            params=params,
            headers=HEADERS,
            cookies=cookies
        )
        
        if response.status_code != 200:
            logger.error(f"Erro ao acessar API: Status {response.status_code}")
            return []
        
        data = response.json()
        
        # Verificar a resposta para entender a estrutura
        if "data" not in data or "global_cats" not in data["data"]:
            logger.error(f"Estrutura da API diferente do esperado: {data}")
            return []
        
        # Calcular o total de itens e páginas
        total_itens = data["data"].get("total", 0)
        total_paginas = (total_itens + tamanho_pagina - 1) // tamanho_pagina
        
        logger.info(f"Total de itens encontrados: {total_itens}")
        logger.info(f"Total de páginas a processar: {total_paginas}")
        
        # Processar todas as páginas
        for pagina in tqdm(range(1, total_paginas + 1), desc="Processando páginas da API"):
            # Se não for a primeira página, fazer nova requisição
            if pagina > 1:
                params["page"] = pagina
                response = requests.get(
                    API_BASE_URL,
                    params=params,
                    headers=HEADERS,
                    cookies=cookies
                )
                
                if response.status_code != 200:
                    logger.error(f"Erro ao acessar página {pagina}: Status {response.status_code}")
                    continue
                
                data = response.json()
                
                if "data" not in data or "global_cats" not in data["data"]:
                    logger.error(f"Estrutura da API diferente do esperado na página {pagina}")
                    continue
            
            # Processar os itens desta página
            itens = data["data"]["global_cats"]
            
            for item in itens:
                try:
                    path = item.get("path", [])
                    categoria = path[0]["category_name"] if len(path) > 0 else ""
                    subcategoria = path[1]["category_name"] if len(path) > 1 else ""
                    terceiro_nivel = path[2]["category_name"] if len(path) > 2 else ""
                    quarto_nivel = path[3]["category_name"] if len(path) > 3 else ""
                    quinto_nivel = path[4]["category_name"] if len(path) > 4 else ""
                    id_categoria = item.get("category_id", "")
                    imagens = item.get("images", [])
                    imagem_categoria = imagens[0] if imagens else ""
                    categoria_item = {
                        "categoria": categoria,
                        "subcategoria": subcategoria,
                        "3_nivel_categoria": terceiro_nivel,
                        "4_nivel_categoria": quarto_nivel,
                        "5_nivel_categoria": quinto_nivel,
                        "id_categoria": id_categoria,
                        "imagem_categoria": imagem_categoria
                    }
                    todas_categorias.append(categoria_item)
                except Exception as e:
                    logger.error(f"Erro ao processar item: {str(e)}")
                    continue
            # Pequeno delay entre requisições para não sobrecarregar a API
            time.sleep(0.5)
        
        logger.info(f"Total de categorias extraídas: {len(todas_categorias)}")
        return todas_categorias
        
    except Exception as e:
        logger.error(f"Erro não tratado: {str(e)}")
        return todas_categorias

def salvar_csv(categorias, nome_arquivo="categorias_shopee_api.csv"):
    """
    Função para salvar os dados em um arquivo CSV.
    
    Args:
        categorias: Lista de dicionários com os dados das categorias
        nome_arquivo: Nome do arquivo CSV de saída
    """
    try:
        if not categorias:
            logger.warning("Nenhuma categoria para salvar")
            return False
        
        df = pd.DataFrame(categorias)
        
        # Garantir que todas as colunas necessárias estão presentes
        colunas_esperadas = [
            "categoria", "subcategoria", "3_nivel_categoria",
            "4_nivel_categoria", "5_nivel_categoria",
            "id_categoria", "imagem_categoria"
        ]
        
        for coluna in colunas_esperadas:
            if coluna not in df.columns:
                df[coluna] = ""
        
        # Reordenar colunas
        df = df[colunas_esperadas]
        
        # Salvar no formato CSV
        df.to_csv(nome_arquivo, index=False, encoding="utf-8-sig")
        logger.info(f"Dados salvos com sucesso no arquivo: {nome_arquivo}")
        
        # Estatísticas
        logger.info(f"Total de registros: {len(df)}")
        logger.info(f"Categorias principais: {df['categoria'].nunique()}")
        logger.info(f"Subcategorias: {df['subcategoria'].nunique()}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar CSV: {str(e)}")
        return False

def salvar_excel(categorias, nome_arquivo="categorias_shopee_api.xlsx"):
    """
    Função para salvar os dados em um arquivo Excel.
    
    Args:
        categorias: Lista de dicionários com os dados das categorias
        nome_arquivo: Nome do arquivo Excel de saída
    """
    try:
        if not categorias:
            logger.warning("Nenhuma categoria para salvar")
            return False
        
        df = pd.DataFrame(categorias)
        
        # Garantir que todas as colunas necessárias estão presentes
        colunas_esperadas = [
            "categoria", "subcategoria", "3_nivel_categoria",
            "4_nivel_categoria", "5_nivel_categoria",
            "id_categoria", "imagem_categoria"
        ]
        
        for coluna in colunas_esperadas:
            if coluna not in df.columns:
                df[coluna] = ""
        
        # Reordenar colunas
        df = df[colunas_esperadas]
        
        # Salvar no formato Excel
        df.to_excel(nome_arquivo, index=False, engine='openpyxl')
        logger.info(f"Dados salvos com sucesso no arquivo: {nome_arquivo}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar Excel: {str(e)}")
        return False

def salvar_postgres(categorias, tabela="categorias_shopee", if_exists="replace"):
    """
    Salva os dados extraídos no banco PostgreSQL.
    Cria a tabela se não existir.
    """
    try:
        if not categorias:
            logger.warning("Nenhuma categoria para salvar no Postgres")
            return False
        
        df = pd.DataFrame(categorias)
        colunas_esperadas = [
            "categoria", "subcategoria", "3_nivel_categoria",
            "4_nivel_categoria", "5_nivel_categoria",
            "id_categoria", "imagem_categoria"
        ]
        for coluna in colunas_esperadas:
            if coluna not in df.columns:
                df[coluna] = ""
        df = df[colunas_esperadas]
        
        # Ler dados de conexão do .env
        usuario = os.getenv("POSTGRES_USER")
        senha = os.getenv("POSTGRES_PASSWORD")
        host = os.getenv("POSTGRES_HOST")
        banco = os.getenv("POSTGRES_DB")
        porta = os.getenv("POSTGRES_PORT", 5432)
        
        url = f"postgresql+psycopg2://{usuario}:{senha}@{host}:{porta}/{banco}"
        engine = sqlalchemy.create_engine(url)
        
        # Cria a tabela se não existir e insere os dados
        df.to_sql(tabela, engine, if_exists=if_exists, index=False)
        logger.info(f"Dados salvos com sucesso no Postgres, tabela: {tabela}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar no Postgres: {str(e)}")
        return False

def main():
    """Função principal do programa."""
    logger.info("Iniciando extração das categorias da Shopee via API...")
    
    # Extrair categorias via API
    categorias = extrair_categorias_via_api()
    
    # Verificar se foram extraídas categorias
    if not categorias:
        logger.error("Nenhuma categoria foi extraída. Verifique os logs para mais detalhes.")
        return False
    
    # Salvar dados
    sucesso_csv = salvar_csv(categorias)
    sucesso_excel = salvar_excel(categorias)
    sucesso_postgres = salvar_postgres(categorias)
    
    if sucesso_csv or sucesso_excel or sucesso_postgres:
        logger.info("Processo concluído com sucesso!")
        return True
    else:
        logger.error("Erro ao salvar os dados. Verifique os logs para mais detalhes.")
        return False

if __name__ == "__main__":
    main()