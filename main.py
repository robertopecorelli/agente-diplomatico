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
# 4. ESTILOS CSS (LAYOUT EDITORIAL E IMAGENS)
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
        padding: 40px;
        border-radius: 4px;
        border: 1px solid #E2DED6;
        margin-bottom: 30px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.02);
    }
    .article-container p {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 18px;
        color: #222222;
        line-height: 1.8;
        margin-bottom: 22px;
    }
    .article-container img {
        display: block;
        max-width: 100% !important;
        height: auto !important;
        max-height: 600px;
        object-fit: contain;
        background-color: #F9F9F9;
        border-radius: 4px;
        margin: 30px auto;
        border: 1px solid #E2DED6;
    }
    .badge {
        display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px;
        font-size: 10px; font-weight: 700; text-transform: uppercase; border-radius: 2px;
        font-family: 'Plus Jakarta Sans', sans-serif; margin-right: 6px; margin-bottom: 8px;
    }
    .badge-onu { background-color: #E8EEF5; color: #1D4ED8; border: 1px solid #BFDBFE; }
    .badge-mre { background-color: #F3F4F6; color: #374151; border: 1px solid #D1D5DB; }
    </style>
""", unsafe_allow_html=True)

def render_badge(categoria):
    if "onu" in categoria.lower(): return '<span class="badge badge-onu"><i class="fa-solid fa-globe"></i> ONU</span>'
    return '<span class="badge badge-mre"><i class="fa-solid fa-landmark"></i> MRE</span>'

# ==============================================================================
# 5. EXTRATOR ROBUSTO (BYPASS DE BLOQUEIO E LEITURA DE IDIOMAS)
# ==============================================================================
@str_lit.cache_data(ttl=3600)
def raspar_conteudo_e_idiomas(url, fallback_html):
    idiomas_disponiveis = {}
    conteudo_html = ""
    
    # Gerador inteligente de URLs para a ONU caso o site bloqueie a leitura
    if "news.un.org" in url:
        base_un = re.sub(r'news\.un\.org/[a-z]{2}/', 'news.un.org/{lang}/', url)
        idiomas_disponiveis = {
            "EN (Inglês)": base_un.format(lang="en"),
            "PT (Português)": base_un.format(lang="pt"),
            "ES (Espanhol)": base_un.format(lang="es"),
            "FR (Francês)": base_un.format(lang="fr"),
            "ZH (Chinês)": base_un.format(lang="zh"),
            "RU (Russo)": base_un.format(lang="ru")
        }

    try:
        # Headers avançados para não ser barrado como "bot"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        
        sessao = requests.Session()
        resposta = sessao.get(url, headers=headers, timeout=10)
        
        if resposta.status_code == 200:
            soup = BeautifulSoup(resposta.text, 'html.parser')
            
            # 1. Tenta capturar os idiomas oficiais nativos pelo hreflang do HTML
            for lang_link in soup.find_all('link', hreflang=True):
                lang_code = lang_link.get('hreflang').upper()
                lang_href = lang_link.get('href')
                if lang_code and lang_code != "X-DEFAULT":
                    idiomas_disponiveis[lang_code] = lang_href
            
            # 2. Busca exata do corpo do texto (Mapeado para Gov.br e UN News)
            corpo = (
                soup.find('div', class_='story-content') or # ONU News
                soup.find('div', id='content-core') or      # Gov.br / MRE
                soup.find('div', id='parent-fieldname-text') or 
                soup.find('article') or 
                soup.find('main')
            )
            
            if corpo:
                # Remove botões sociais, menus e lixos
                for lixo in corpo(["script", "style", "nav", "footer", "form", "aside", ".share-buttons", ".social-media"]):
                    lixo.extract()
                conteudo_html = str(corpo)
            else:
                # Busca genérica em parágrafos se tudo falhar
                paragrafos = soup.find_all('p')
                conteudo_html = "".join([str(p) for p in paragrafos if len(p.text) > 30])
                
    except Exception as e:
        print(f"Scrape falhou para {url}: {e}")

    # Fallback supremo: Se o HTML final for nulo ou muito pequeno, injeta o texto base do RSS
    if not conteudo_html or len(conteudo_html) < 200:
        conteudo_html = f"<div>{fallback_html}</div><br><p><em>*Conteúdo carregado via feed seguro. Para ver a versão original completa com formatação nativa, clique no botão de acesso abaixo.</em></p>"

    return conteudo_html, idiomas_disponiveis

# ==============================================================================
# 6. CARREGADOR DE FEEDS (COM FALLBACK HTML)
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
            # Pega o resumo limpo
            resumo = re.sub('<[^<]+?>', '', entry.get("summary", entry.get("description", "")))[:250] + "..."
            
            # Pega o texto completo embutido no RSS (Fallback essencial)
            conteudo_rss_html = ""
            if 'content' in entry:
                conteudo_rss_html = entry.content[0].value
            else:
                conteudo_rss_html = entry.get("summary", entry.get("description", ""))
            
            # Extração de imagem
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
# 7. ROTEAMENTO DA PÁGINA INTERNA (DETALHES DO DOCUMENTO)
# ==============================================================================
article_id_param = str_lit.query_params.get("article", None)

if article_id_param is not None:
    try:
        art_idx = int(article_id_param)
        artigo_atual = next((item for item in acervo_noticias if item["id"] == art_idx), None)
    except:
        artigo_atual = None

    if artigo_atual:
        # A Mágica Acontece Aqui: Extrai conteúdo e idiomas
        conteudo_limpo, idiomas_origem = raspar_conteudo_e_idiomas(artigo_atual['link'], artigo_atual['conteudo_rss'])
        
        # Barra superior de Voltar e Idiomas
        col_voltar, col_lang = str_lit.columns([3, 1])
        with col_voltar:
            if str_lit.button("← Voltar ao Repositório"):
                str_lit.query_params.clear()
                str_lit.rerun()
        
        with col_lang:
            if idiomas_origem:
                lista_langs = ["Original do Link"] + list(idiomas_origem.keys())
                lang_escolhida = str_lit.selectbox("🌐 Ler Oficial em outro Idioma:", lista_langs)
                
                # Se escolher outro idioma, recarrega a página direcionando pro link correto
                if lang_escolhida != "Original do Link" and lang_escolhida in idiomas_origem:
                    link_traduzido = idiomas_origem[lang_escolhida]
                    str_lit.markdown(f'<meta http-equiv="refresh" content="0; url={link_traduzido}">', unsafe_allow_html=True)
            else:
                str_lit.caption("🌐 Idioma Único (Origem)")

        str_lit.markdown("<br>", unsafe_allow_html=True)
        
        # Cabeçalho da Notícia
        str_lit.markdown(f"<div>{render_badge(artigo_atual['orgao'])}</div>", unsafe_allow_html=True)
        str_lit.markdown(f"<h1 style='font-family: Newsreader, serif; font-size: 40px; margin-top: 10px; margin-bottom: 25px;'>{artigo_atual['titulo']}</h1>", unsafe_allow_html=True)
        
        # Imagem de Capa em Alta Definição e Adaptada
        str_lit.markdown(f"""
            <div style="width: 100%; text-align: center; overflow: hidden; border-radius: 4px; margin-bottom: 30px; border: 1px solid #E2DED6; background-color: #1A1A1A;">
                <img src="{artigo_atual['imagem']}" style="max-width: 100%; max-height: 550px; object-fit: contain; margin: 0 auto;" alt="Capa" />
            </div>
        """, unsafe_allow_html=True)
        
        # Corpo da Matéria (Garantido que nunca mais ficará em branco)
        str_lit.markdown(f"""
            <div class="article-container">
                {conteudo_limpo}
            </div>
        """, unsafe_allow_html=True)
        
        str_lit.markdown("---")
        if str_lit.button("🔗 Ver / Acessar Link Oficial na Íntegra", use_container_width=True):
            str_lit.markdown(f'<meta http-equiv="refresh" content="0; url={artigo_atual["link"]}">', unsafe_allow_html=True)
            str_lit.rerun()

        str_lit.stop()

# ==============================================================================
# 8. HOME - ACERVO E GRID DE CONTEÚDO
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
