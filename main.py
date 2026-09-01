import streamlit as str_lit
import feedparser
from bs4 import BeautifulSoup
import requests
from datetime import date
import re
import stripe

# ==============================================================================
# 1. CONFIGURAÇÃO DE SEGREDOS E STRIPE
# ==============================================================================
STRIPE_SECRET_KEY = str_lit.secrets.get("STRIPE_SECRET_KEY", "sk_test_exemplo")
DOMAIN_URL = str_lit.secrets.get("DOMAIN_URL", "http://localhost:8501")

stripe.api_key = STRIPE_SECRET_KEY

# ==============================================================================
# 2. CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ==============================================================================
str_lit.set_page_config(
    page_title="Repositório Diplomático | Acervo CACD",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="auto"
)

# ==============================================================================
# 3. GERENCIAMENTO DE SESSÃO
# ==============================================================================
if "users_db" not in str_lit.session_state:
    str_lit.session_state["users_db"] = {
        "visitante": {"plan": "free", "access_count": 0, "last_date": str(date.today()), "email": ""}
    }

if "current_user" not in str_lit.session_state:
    str_lit.session_state["current_user"] = "visitante"

def verificar_reset_diario(username):
    user_data = str_lit.session_state["users_db"].get(username)
    if user_data:
        hoje_str = str(date.today())
        if user_data.get("last_date") != hoje_str:
            user_data["access_count"] = 0
            user_data["last_date"] = hoje_str

verificar_reset_diario(str_lit.session_state["current_user"])

# ==============================================================================
# 4. ESTILOS CSS REFINADOS (LAYOUT EDITORIAL FIEL AOS PORTAIS)
# ==============================================================================
str_lit.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');

    html, body, [class*="stApp"] {
        background-color: #F7F5F0 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #1A1A1A !important;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Newsreader', serif !important;
        color: #1A1A1A !important;
        letter-spacing: -0.02em;
    }
    .article-container {
        background-color: #FFFFFF;
        padding: 50px;
        border-radius: 4px;
        border: 1px solid #E2DED6;
        margin-bottom: 20px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.02);
    }
    .article-container p {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 18px;
        color: #222222;
        line-height: 1.85;
        margin-bottom: 24px;
    }
    .article-container img, .article-container figure, .article-container picture {
        display: block;
        max-width: 100% !important;
        height: auto !important;
        margin: 30px auto;
        border-radius: 4px;
        border: 1px solid #E2DED6;
        background-color: #F9F9F9;
        object-fit: contain;
    }
    .article-container figcaption {
        font-size: 13px;
        color: #666666;
        text-align: center;
        margin-top: -15px;
        margin-bottom: 25px;
        font-style: italic;
    }
    .badge {
        display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px;
        font-size: 10px; font-weight: 700; text-transform: uppercase; border-radius: 2px;
        font-family: 'Plus Jakarta Sans', sans-serif; margin-right: 6px; margin-bottom: 8px;
    }
    .badge-onu { background-color: #E8EEF5; color: #1D4ED8; border: 1px solid #BFDBFE; }
    .badge-mre { background-color: #F3F4F6; color: #374151; border: 1px solid #D1D5DB; }
    
    .footer-original-link {
        font-size: 13px;
        color: #666666;
        text-align: center;
        margin-top: 30px;
        margin-bottom: 40px;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .footer-original-link a {
        color: #444444;
        text-decoration: underline;
        text-underline-offset: 3px;
    }
    .footer-original-link a:hover {
        color: #1A1A1A;
    }
    </style>
""", unsafe_allow_html=True)

def render_badge(categoria):
    if "onu" in categoria.lower(): return '<span class="badge badge-onu"><i class="fa-solid fa-globe"></i> ONU</span>'
    return '<span class="badge badge-mre"><i class="fa-solid fa-landmark"></i> MRE</span>'

# ==============================================================================
# 5. EXTRATOR PROFUNDO DE CONTEÚDO INTEGRAL E IDIOMAS NATIVOS
# ==============================================================================
@str_lit.cache_data(ttl=3600)
def raspar_conteudo_completo(url):
    idiomas_disponiveis = {}
    conteudo_html = ""
    
    # Mapeamento exato de URLs multilíngues da ONU News
    if "news.un.org" in url:
        base_un = re.sub(r'news\.un\.org/[a-z]{2}/', 'news.un.org/{lang}/', url)
        idiomas_disponiveis = {
            "Inglês (EN)": base_un.format(lang="en"),
            "Português (PT)": base_un.format(lang="pt"),
            "Espanhol (ES)": base_un.format(lang="es"),
            "Francês (FR)": base_un.format(lang="fr"),
            "Chinês (ZH)": base_un.format(lang="zh"),
            "Russo (RU)": base_un.format(lang="ru")
        }

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        
        resposta = requests.get(url, headers=headers, timeout=12)
        
        if resposta.status_code == 200:
            soup = BeautifulSoup(resposta.text, 'html.parser')
            
            # Captura os links multilíngues nativos reais inseridos pelo site via hreflang
            for lang_link in soup.find_all('link', hreflang=True):
                lang_code = lang_link.get('hreflang').upper()
                lang_href = lang_link.get('href')
                if lang_code and lang_code != "X-DEFAULT" and len(lang_code) <= 5:
                    idiomas_disponiveis[lang_code] = lang_href

            # Captura os seletores oficiais e profundos onde o texto e mídias completas residem
            corpo = (
                soup.find('div', class_='story-content') or 
                soup.find('div', class_='field-name-body') or
                soup.find('div', id='content-core') or      
                soup.find('div', id='parent-fieldname-text') or 
                soup.find('div', class_='node__content') or
                soup.find('article') or 
                soup.find('main')
            )
            
            if corpo:
                # Remove apenas elementos de navegação e rodapés irrelevantes
                for lixo in corpo(["script", "style", "nav", "footer", "form", "aside", "header", ".share-buttons", ".social-media"]):
                    lixo.extract()
                conteudo_html = str(corpo)
            else:
                # Seletor de contingência robusto: coleta todo o miolo rico de texto, figuras e gráficos
                elementos = soup.find_all(['p', 'h2', 'h3', 'img', 'figure', 'picture', 'blockquote', 'ul', 'ol'])
                container_dinamico = BeautifulSoup("<div></div>", "html.parser")
                div_pai = container_dinamico.div
                for el in elementos:
                    texto_el = el.get_text(strip=True).lower()
                    if any(termo in texto_el for termo in ["todos os direitos reservados", "política de privacidade", "cookies", "newsletter"]):
                        continue
                    div_pai.append(el)
                conteudo_html = str(div_pai)
                
    except Exception as e:
        print(f"Erro ao raspar {url}: {e}")

    return conteudo_html, idiomas_disponiveis

# ==============================================================================
# 6. CARREGADOR DE FEEDS DE NOTÍCIAS
# ==============================================================================
FONTES = {
    "MRE": ("https://www.gov.br/mre/pt-br/centrais-de-conteudo/notas-a-imprensa/RSS", "MRE"),
    "ONU": ("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "ONU")
}

@str_lit.cache_data(ttl=1800)
def carregar_noticias():
    itens = []
    idx_count = 0
    for nome, (url, orgao) in FONTES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            resumo = re.sub('<[^<]+?>', '', entry.get("summary", entry.get("description", "")))[:250] + "..."
            
            conteudo_rss_html = ""
            if 'content' in entry:
                conteudo_rss_html = entry.content[0].value
            else:
                conteudo_rss_html = entry.get("summary", entry.get("description", ""))

            raw_html = entry.get("summary", "") or entry.get("description", "")
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', raw_html)
            imagem_url = img_match.group(1) if img_match else "https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=1600&q=90"

            itens.append({
                "id": idx_count,
                "titulo": entry.title,
                "resumo": resumo,
                "conteudo_rss": conteudo_rss_html,
                "orgao": orgao,
                "imagem": imagem_url,
                "link": entry.link,
                "data": entry.get("published", "Data recente")
            })
            idx_count += 1
    return itens

acervo_noticias = carregar_noticias()

# ==============================================================================
# 7. ROTEAMENTO DA PÁGINA INTERNA (DETALHES)
# ==============================================================================
article_id_param = str_lit.query_params.get("article", None)

if article_id_param is not None:
    try:
        art_idx = int(article_id_param)
        artigo_atual = next((item for item in acervo_noticias if item["id"] == art_idx), None)
    except:
        artigo_atual = None

    if artigo_atual:
        # Extrai o conteúdo integral do site de origem com imagens, gráficos e formatação
        conteudo_extraido, idiomas_origem = raspar_conteudo_completo(artigo_atual['link'])
        
        # Garante que o texto completo seja renderizado com prioridade absoluta
        conteudo_final = conteudo_extraido if len(conteudo_extraido) > 150 else f"<div>{artigo_atual['conteudo_rss']}</div>"

        # Barra superior limpa com botão de Voltar e Menu de Idiomas Nativos
        col_voltar, col_lang = str_lit.columns([3, 1])
        with col_voltar:
            if str_lit.button("← Voltar ao Repositório"):
                str_lit.query_params.clear()
                str_lit.rerun()
        
        with col_lang:
            if idiomas_origem:
                lista_langs = ["Versão Atual (Origem)"] + list(idiomas_origem.keys())
                lang_escolhida = str_lit.selectbox("🌐 Idiomas Disponíveis:", lista_langs)
                if lang_escolhida != "Versão Atual (Origem)" and lang_escolhida in idiomas_origem:
                    link_traduzido = idiomas_origem[lang_escolhida]
                    str_lit.markdown(f'<meta http-equiv="refresh" content="0; url={link_traduzido}">', unsafe_allow_html=True)
            else:
                str_lit.caption("🌐 Idioma original")

        str_lit.markdown("<br>", unsafe_allow_html=True)
        
        # Cabeçalho, Órgão e Título Principal
        str_lit.markdown(f"<div>{render_badge(artigo_atual['orgao'])}</div>", unsafe_allow_html=True)
        str_lit.markdown(f"<h1 style='font-family: Newsreader, serif; font-size: 38px; margin-top: 10px; margin-bottom: 25px;'>{artigo_atual['titulo']}</h1>", unsafe_allow_html=True)
        
        # Imagem de Capa em Alta Resolução
        str_lit.markdown(f"""
            <div style="width: 100%; text-align: center; overflow: hidden; border-radius: 4px; margin-bottom: 30px; border: 1px solid #E2DED6; background-color: #1A1A1A;">
                <img src="{artigo_atual['imagem']}" style="max-width: 100%; max-height: 550px; object-fit: contain; margin: 0 auto;" alt="Capa" />
            </div>
        """, unsafe_allow_html=True)
        
        # Corpo Completo da Notícia com Gráficos, Fotos e Estrutura Original
        str_lit.markdown(f"""
            <div class="article-container">
                {conteudo_final}
            </div>
        """, unsafe_allow_html=True)
        
        # Link discreto e elegante no rodapé conforme solicitado
        str_lit.markdown(f"""
            <div class="footer-original-link">
                Publicação original disponível em <a href="{artigo_atual['link']}" target="_blank">{artigo_atual['orgao']}</a>
            </div>
        """, unsafe_allow_html=True)

        str_lit.stop()

# ==============================================================================
# 8. HOME / LISTAGEM DE NOTÍCIAS
# ==============================================================================
str_lit.markdown("""
    <div style="font-family: 'Newsreader', serif; font-size: 28px; font-weight: 600;">
        Repositório <span style="color: #666; font-style: italic;">Diplomático</span>
    </div>
    <hr style='border: none; border-top: 1px solid #1A1A1A; margin-bottom: 24px;'>
""", unsafe_allow_html=True)

if len(acervo_noticias) > 0:
    grid_cols = str_lit.columns(2)
    for idx, item in enumerate(acervo_noticias):
        with grid_cols[idx % 2]:
            str_lit.markdown(f"""
                <div style="background: #FFF; border-radius: 4px; border: 1px solid #E2DED6; margin-bottom: 12px; overflow: hidden;">
                    <img src="{item['imagem']}" style="width: 100%; height: 180px; object-fit: cover; background: #1A1A1A;" />
                    <div style="padding: 16px;">
                        {render_badge(item['orgao'])}
                        <div style="font-family: 'Newsreader', serif; font-size: 19px; font-weight: 600; margin-top: 8px; margin-bottom: 8px; color: #1A1A1A; line-height: 1.2;">
                            {item['titulo']}
                        </div>
                        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 13px; color: #666; line-height: 1.5;">
                            {item['resumo']}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if str_lit.button(f"📖 ABRIR CONTEÚDO", key=f"btn_{item['id']}", use_container_width=True):
                str_lit.query_params["article"] = str(item['id'])
                str_lit.rerun()
