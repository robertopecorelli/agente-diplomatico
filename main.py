import os
import feedparser
import requests
import resend

# Configura a chave de API obtida de forma segura do GitHub Actions
resend.api_key = os.getenv("RESEND_API_KEY")

URL_FEED_BASE = "https://news.un.org/feed/subscribe/en/news/all/rss.xml"

def validar_idiomas_disponiveis(link_base):
    idiomas = ["pt", "en", "es", "fr"]
    idiomas_disponiveis = {}
    idioma_atual = None
    
    for lang in idiomas:
        if f"/{lang}/" in link_base:
            idioma_atual = lang
            break
            
    if not idioma_atual:
        return {"en": link_base}

    for lang in idiomas:
        url_candidata = link_base.replace(f"/{idioma_atual}/", f"/{lang}/")
        try:
            response = requests.head(url_candidata, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                idiomas_disponiveis[lang] = url_candidata
            else:
                response_get = requests.get(url_candidata, timeout=5)
                if response_get.status_code == 200:
                    idiomas_disponiveis[lang] = url_candidata
        except requests.RequestException:
            pass
            
    return idiomas_disponiveis

def executar_varredura():
    feed = feedparser.parse(URL_FEED_BASE)
    relatorio = []
    
    for entry in feed.entries[:3]: # Pega as 3 principais do dia
        versoes = validar_idiomas_disponiveis(entry.link)
        relatorio.append({
            "titulo": entry.title,
            "data": entry.get("published", "Data não informada"),
            "links": versoes
        })
    return relatorio

def montar_html_relatorio(comunicados):
    html = "<h2>📰 Relatório Diplomático Diário</h2><br>"
    for idx, item in enumerate(comunicados, 1):
        html += f"<b>{idx}. {item['titulo']}</b><br>"
        html += f"<small>📅 {item['data']}</small><br>"
        html += "<b>Links Oficiais:</b><ul>"
        for lang, url in item['links'].items():
            html += f"<li><a href='{url}'>[{lang.upper()}]</a></li>"
        html += "</ul><hr>"
    return html

def enviar_email(corpo_html):
    if not resend.api_key:
        print("Chave de API do Resend não configurada.")
        return

    params = {
        "from": "Agente Diplomático <onboarding@resend.dev>",
        "to": ["robertobastos.arq@gmail.com"],
        "subject": "Relatório Diplomático Diário - ONU / MRE",
        "html": corpo_html,
    }

    try:
        email = resend.Emails.send(params)
        print("E-mail enviado com sucesso via Resend!", email)
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

if __name__ == "__main__":
    print("Iniciando varredura...")
    comunicados = executar_varredura()
    
    if comunicados:
        relatorio_html = montar_html_relatorio(comunicados)
        enviar_email(relatorio_html)
    else:
        print("Nenhum comunicado encontrado hoje.")
