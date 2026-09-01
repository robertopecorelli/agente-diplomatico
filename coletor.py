import os
import json
import time
import requests
import feedparser
import psycopg2
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from psycopg2.extras import execute_values
from google import genai
from google.genai import types

URL_BANCO_PADRAO = "postgresql://postgres.mgplflhxuefrpayazhyn:Jm1r4jZGIYWYcmqM@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

gemini_key = os.getenv("GEMINI_API_KEY")
ai_client = genai.Client(api_key=gemini_key) if gemini_key else None

def conectar_banco():
    return psycopg2.connect(URL_BANCO_PADRAO)

def analisar_noticia_com_gemini(titulo, conteudo, max_retries=3):
    """Usa o Gemini 3.6 Flash respeitando o limite da cota gratuita."""
    if not ai_client:
        print("  ⚠️ Chave GEMINI_API_KEY não encontrada no ambiente.")
        return "Resumo indisponível.", "Política Internacional", []

    prompt = f"""
    Você é um assistente especializado na preparação para o CACD (Concurso de Admissão à Carreira de Diplomata).
    Análise a seguinte notícia diplomática:

    Título: {titulo}
    Conteúdo/Resumo: {conteudo}

    Retorne um JSON VÁLIDO com exatamente a seguinte estrutura:
    {{
        "resumo": "Resumo de 2 a 3 frases focando nos impactos diplomáticos e relevância teórica/prática.",
        "disciplina": "Escolha UMA das opções: Política Internacional, Direito Internacional, Economia, História da Política Externa Brasileira, Geografia ou Língua Portuguesa",
        "tags": ["até", "4", "palavras-chave"]
    }}
    """

    for tentativa in range(max_retries):
        try:
            response = ai_client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            dados = json.loads(response.text)
            return dados.get("resumo", ""), dados.get("disciplina", "Política Internacional"), dados.get("tags", [])
        except Exception as e:
            if "503" in str(e) or "429" in str(e):
                tempo_espera = 5 * (tentativa + 1)
                print(f"  ⚠️ Cota/Servidor ocupado. Aguardando {tempo_espera}s para tentar novamente...")
                time.sleep(tempo_espera)
            else:
                print(f"  ❌ Erro no Gemini: {e}")
                return "Erro ao gerar resumo.", "Política Internacional", []
    
    return "Erro ao gerar resumo.", "Política Internacional", []

def coletar_noticias_mre():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Raspando MRE...")
    url = "https://www.gov.br/mre/pt-br/canais_atendimento/imprensa/notas-a-imprensa"
    artigos = []

    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, 'html.parser')
            itens = soup.find_all(['article', 'li'], class_=lambda c: c and ('tileItem' in c or 'entry' in c or 'item' in c))

            for item in itens:
                tag_a = item.find('a', class_='summary url') or item.find('a', href=True)
                if not tag_a: continue
                titulo, link = tag_a.get_text(strip=True), tag_a['href']
                tag_resumo = item.find('span', class_='description') or item.find('p')
                resumo = tag_resumo.get_text(strip=True) if tag_resumo else ""

                if titulo and link.startswith('http'):
                    artigos.append({"titulo": titulo, "link": link, "fonte": "MRE", "data_publicacao": datetime.now(timezone.utc), "conteudo_bruto": resumo})
        print(f"-> MRE: {len(artigos)} notas extraídas.")
    except Exception as e:
        print(f"-> Erro MRE: {e}")
    return artigos

def coletar_noticias_onu():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Coletando RSS ONU...")
    url = "https://news.un.org/feed/subscribe/pt/news/all/rss.xml"
    artigos = []

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            feed = feedparser.parse(res.content)
            for entry in feed.entries:
                artigos.append({"titulo": entry.get("title", ""), "link": entry.get("link", ""), "fonte": "ONU", "data_publicacao": datetime.now(timezone.utc), "conteudo_bruto": entry.get("summary", "")})
        print(f"-> ONU: {len(artigos)} notas extraídas.")
    except Exception as e:
        print(f"-> Erro ONU: {e}")
    return artigos

def salvar_no_banco(artigos):
    if not artigos:
        print("Nenhum artigo novo para processar.")
        return

    conexao = conectar_banco()
    cursor = conexao.cursor()

    dados_processados = []
    
    # Para evitar estourar limites em testes, processa as primeiras 5 notícias por vez
    artigos_para_processar = artigos[:5]
    total = len(artigos_para_processar)

    print(f"\n--- Processando {total} notícias com a IA ---")

    for i, item in enumerate(artigos_para_processar, 1):
        print(f"[{i}/{total}] Analisando: {item['titulo'][:60]}...")
        resumo_ia, disciplina, tags = analisar_noticia_com_gemini(item["titulo"], item["conteudo_bruto"])
        
        dados_processados.append((
            item["titulo"], item["link"], item["fonte"], 
            item["data_publicacao"], item["conteudo_bruto"], 
            resumo_ia, disciplina, tags
        ))
        
        # Espera 4.5s para manter a cota abaixo de 15 requisições por minuto
        if i < total:
            time.sleep(4.5)

    sql = """
        INSERT INTO artigos_diplomaticos (titulo, link, fonte, data_publicacao, conteudo_bruto, resumo_ia, disciplina_cacd, tags)
        VALUES %s
        ON CONFLICT (link) DO UPDATE SET 
            resumo_ia = EXCLUDED.resumo_ia,
            disciplina_cacd = EXCLUDED.disciplina_cacd,
            tags = EXCLUDED.tags;
    """

    try:
        execute_values(cursor, sql, dados_processados)
        conexao.commit()
        print(f"\n✅ Sucesso: {len(dados_processados)} artigos salvos e atualizados no Supabase!")
    except Exception as e:
        conexao.rollback()
        print(f"❌ Erro ao gravar no Supabase: {e}")
    finally:
        cursor.close()
        conexao.close()

if __name__ == "__main__":
    mre = coletar_noticias_mre()
    onu = coletar_noticias_onu()
    salvar_no_banco(mre + onu)