import os
import requests
import feedparser
import psycopg2
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from psycopg2.extras import execute_values

# URL do banco de dados PostgreSQL no Supabase (com ID correto)
URL_BANCO_PADRAO = "postgresql://postgres.mgplflhxuefrpayazhyn:Jm1r4jZGIYWYcmqM@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"

# Cabeçalhos HTTP para simular um navegador e evitar bloqueios
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}

def conectar_banco():
    """Estabelece conexão com o banco de dados PostgreSQL."""
    db_url = URL_BANCO_PADRAO
    return psycopg2.connect(db_url)

def coletar_noticias_mre():
    """Web Scraping para a página de Notas à Imprensa do MRE (gov.br)."""
    print(f"[{datetime.now()}] Raspando notas à imprensa do MRE...")
    url = "https://www.gov.br/mre/pt-br/canais_atendimento/imprensa/notas-a-imprensa"
    artigos = []

    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            print(f"-> Erro ao acessar MRE: Status {res.status_code}")
            return []

        soup = BeautifulSoup(res.content, 'html.parser')
        itens = soup.find_all(['article', 'li'], class_=lambda c: c and ('tileItem' in c or 'entry' in c or 'item' in c))

        for item in itens:
            tag_a = item.find('a', class_='summary url') or item.find('a', href=True)
            if not tag_a:
                continue

            titulo = tag_a.get_text(strip=True)
            link = tag_a['href']

            tag_resumo = item.find('span', class_='description') or item.find('p')
            resumo = tag_resumo.get_text(strip=True) if tag_resumo else ""

            if titulo and link.startswith('http'):
                artigos.append({
                    "titulo": titulo,
                    "link": link,
                    "fonte": "MRE",
                    "data_publicacao": datetime.now(timezone.utc),
                    "conteudo_bruto": resumo
                })

        print(f"-> MRE: {len(artigos)} notas extraídas.")
    except Exception as e:
        print(f"-> Erro ao raspar MRE: {e}")

    return artigos

def coletar_noticias_onu():
    """Coleta do feed RSS oficial da ONU."""
    print(f"[{datetime.now()}] Coletando RSS da ONU...")
    url = "https://news.un.org/feed/subscribe/pt/news/all/rss.xml"
    artigos = []

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            feed = feedparser.parse(res.content)
            for entry in feed.entries:
                artigos.append({
                    "titulo": entry.get("title", "Sem Título"),
                    "link": entry.get("link", ""),
                    "fonte": "ONU",
                    "data_publicacao": datetime.now(timezone.utc),
                    "conteudo_bruto": entry.get("summary", "")
                })
        print(f"-> ONU: {len(artigos)} notas extraídas.")
    except Exception as e:
        print(f"-> Erro ao coletar ONU: {e}")

    return artigos

def salvar_no_banco(artigos):
    if not artigos:
        print("Nenhum artigo novo para salvar.")
        return

    conexao = conectar_banco()
    cursor = conexao.cursor()

    dados = [
        (item["titulo"], item["link"], item["fonte"], item["data_publicacao"], item["conteudo_bruto"])
        for item in artigos
    ]

    sql = """
        INSERT INTO artigos_diplomaticos (titulo, link, fonte, data_publicacao, conteudo_bruto)
        VALUES %s
        ON CONFLICT (link) DO NOTHING;
    """

    try:
        execute_values(cursor, sql, dados)
        conexao.commit()
        print(f"[{datetime.now()}] Sucesso: {len(artigos)} registros processados no Supabase.")
    except Exception as e:
        conexao.rollback()
        print(f"Erro no banco: {e}")
    finally:
        cursor.close()
        conexao.close()

if __name__ == "__main__":
    mre = coletar_noticias_mre()
    onu = coletar_noticias_onu()
    salvar_no_banco(mre + onu)