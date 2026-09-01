import os
import feedparser
import requests
import resend

resend.api_key = os.getenv("RESEND_API_KEY")

# Fontes ampliadas: incluindo canais específicos de Discursos e Notas Oficiais
FONTES = {
    "MRE (Itamaraty - Notícias e Notas)": "https://www.gov.br/mre/pt-br/centrais-de-conteudo/noticias/RSS",
    "MRE (Itamaraty - Discursos)": "https://www.gov.br/mre/pt-br/centrais-de-conteudo/discursos/RSS",
    "ONU (United Nations - Press/Discursos)": "https://news.un.org/feed/subscribe/en/news/all/rss.xml"
}

def validar_idiomas_e_resumos(link_base, resumo_original):
    idiomas = ["pt", "en", "es", "fr"]
    dados_idiomas = {}
    
    idioma_atual = None
    for lang in idiomas:
        if f"/{lang}/" in link_base:
            idioma_atual = lang
            break
            
    if not idioma_atual:
        return {"en": {"link": link_base, "resumo": resumo_original}}

    for lang in idiomas:
        url_candidata = link_base.replace(f"/{idioma_atual}/", f"/{lang}/")
        try:
            response = requests.head(url_candidata, timeout=4, allow_redirects=True)
            if response.status_code == 200:
                dados_idiomas[lang] = {"link": url_candidata, "resumo": resumo_original if lang == idioma_atual else "Disponível no link oficial."}
            else:
                response_get = requests.get(url_candidata, timeout=4)
                if response_get.status_code == 200:
                    dados_idiomas[lang] = {"link": url_candidata, "resumo": resumo_original if lang == idioma_atual else "Disponível no link oficial."}
        except requests.RequestException:
            pass
            
    if not dados_idiomas:
        dados_idiomas[idioma_atual] = {"link": link_base, "resumo": resumo_original}
        
    return dados_idiomas

def executar_varredura():
    relatorio_geral = {}

    for nome_fonte, url_rss in FONTES.items():
        feed = feedparser.parse(url_rss)
        itens_fonte = []
        
        # Pega até 3 itens de cada categoria
        for entry in feed.entries[:3]: 
            resumo = entry.get("summary", "Resumo não disponível.")
            versoes = validar_idiomas_e_resumos(entry.link, resumo)
            
            itens_fonte.append({
                "titulo": entry.title,
                "data": entry.get("published", "Data recente"),
                "versoes": versoes
            })
        relatorio_geral[nome_fonte] = itens_fonte
        
    return relatorio_geral

def montar_html_minimalista(relatorio):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background-color: #f9f9fb;
                color: #111827;
                margin: 0;
                padding: 40px 20px;
            }}
            .container {{
                max-width: 680px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 12px;
                padding: 40px;
                border: 1px solid #e5e7eb;
            }}
            h1 {{
                font-size: 22px;
                font-weight: 600;
                letter-spacing: -0.5px;
                color: #111827;
                margin-top: 0;
                margin-bottom: 8px;
            }}
            .subtitle {{
                font-size: 13px;
                color: #6b7280;
                margin-bottom: 32px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .section-title {{
                font-size: 15px;
                font-weight: 600;
                color: #374151;
                border-bottom: 2px solid #f3f4f6;
                padding-bottom: 8px;
                margin-top: 36px;
                margin-bottom: 20px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .item {{
                margin-bottom: 28px;
            }}
            .item-title {{
                font-size: 16px;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 4px;
                line-height: 1.4;
            }}
            .item-date {{
                font-size: 12px;
                color: #9ca3af;
                margin-bottom: 12px;
            }}
            .lang-block {{
                background: #f9fafb;
                border-left: 3px solid #d1d5db;
                padding: 10px 14px;
                margin-top: 8px;
                border-radius: 0 6px 6px 0;
            }}
            .lang-label {{
                font-size: 11px;
                font-weight: 700;
                color: #4b5563;
                text-transform: uppercase;
                margin-bottom: 2px;
            }}
            .lang-resumo {{
                font-size: 13px;
                color: #4b5563;
                margin-bottom: 6px;
                line-height: 1.4;
            }}
            a {{
                color: #2563eb;
                text-decoration: none;
                font-size: 12px;
                font-weight: 500;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            .footer {{
                margin-top: 40px;
                font-size: 11px;
                color: #9ca3af;
                text-align: center;
                border-top: 1px solid #f3f4f6;
                padding-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Boletim Diplomático Diário</h1>
            <div class="subtitle">Monitoramento de Notas, Comunicados & Discursos</div>
    """

    for fonte, itens in relatorio.items():
        html += f'<div class="section-title">{fonte}</div>'
        if not itens:
            html += '<p style="font-size: 13px; color: #9ca3af;">Nenhum registro novo hoje.</p>'
            continue
            
        for item in itens:
            html += f"""
            <div class="item">
                <div class="item-title">{item['titulo']}</div>
                <div class="item-date">{item['data']}</div>
            """
            for lang, info in item['versoes'].items():
                html += f"""
                <div class="lang-block">
                    <div class="lang-label">[{lang.upper()}]</div>
                    <div class="lang-resumo">{info['resumo']}</div>
                    <a href="{info['link']}" target="_blank">Acessar versão oficial em {lang.upper()} &rarr;</a>
                </div>
                """
            html += "</div>"

    html += """
            <div class="footer">
                Gerado automaticamente pelo Agente Diplomático.
            </div>
        </div>
    </body>
    </html>
    """
    return html

def enviar_email(corpo_html):
    if not resend.api_key:
        print("Chave de API não configurada.")
        return

    params = {
        "from": "Agente Diplomático <onboarding@resend.dev>",
        "to": ["robertobastos.arq@gmail.com"],
        "subject": "Boletim Diplomático Diário — Notas & Discursos",
        "html": corpo_html,
    }

    try:
        resend.Emails.send(params)
        print("E-mail com discursos e notas enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

if __name__ == "__main__":
    print("Executando varredura expandida (Notas e Discursos)...")
    dados_relatorio = executar_varredura()
    html_final = montar_html_minimalista(dados_relatorio)
    enviar_email(html_final)
