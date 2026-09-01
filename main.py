import streamlit as str_lit
import feedparser
from bs4 import BeautifulSoup
import requests
from datetime import date
import re

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA STREAMLIT & LAYOUT SIMÉTRICO
# ==============================================================================
str_lit.set_page_config(
    page_title="Ubique News | Acervo e Inteligência para o CACD",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="auto"
)

# ==============================================================================
# 2. GERENCIAMENTO DE SESSÃO E ROTEAMENTO
# ==============================================================================
if "users_db" not in str_lit.session_state:
    str_lit.session_state["users_db"] = {
        "visitante": {"plan": "free", "access_count": 0, "last_date": str(date.today()), "email": ""}
    }

if "current_user" not in str_lit.session_state:
    str_lit.session_state["current_user"] = "visitante"

if "show_plans_modal" not in str_lit.session_state:
    str_lit.session_state["show_plans_modal"] = False

if "show_register_modal" not in str_lit.session_state:
    str_lit.session_state["show_register_modal"] = False

# ==============================================================================
# 3. ESTILOS CSS REFINADOS (GRID SIMÉTRICO E LEITURA IMersiva)
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

    section[data-testid="stSidebar"] {
        background-color: #EFECE6 !important;
        border-right: 1px solid #E2DED6;
    }

    /* CARDS SIMÉTRICOS E IDÊNTICOS EM ALTURA */
    .news-card {
        background: #FFFFFF;
        border-radius: 6px;
        border: 1px solid #E2DED6;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 480px;
        overflow: hidden;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
    }
    .card-img-container {
        width: 100%;
        height: 180px;
        min-height: 180px;
        overflow: hidden;
        background-color: #1A1A1A;
        position: relative;
    }
    .card-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .card-body { 
        padding: 16px; 
        display: flex;
        flex-direction: column;
        flex-grow: 1;
        justify-content: flex-start;
    }
    .card-title {
        font-family: 'Newsreader', serif;
        font-size: 18px;
        font-weight: 600;
        color: #1A1A1A;
        line-height: 1.25;
        margin-bottom: 8px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .card-excerpt { 
        font-family: 'Plus Jakarta Sans', sans-serif; 
        font-size: 13px; 
        color: #666666; 
        line-height: 1.45; 
        margin-bottom: 10px;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    /* BADGES */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 3px 8px;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        border-radius: 2px;
        margin-right: 4px;
        margin-bottom: 6px;
    }
    .badge-onu { background-color: #E8EEF5; color: #1D4ED8; border: 1px solid #BFDBFE; }
    .badge-mre { background-color: #F3F4F6; color: #374151; border: 1px solid #D1D5DB; }
    .badge-noticias { background-color: #FEF3C7; color: #B45309; border: 1px solid #FDE68A; }
    .badge-notas { background-color: #DCFCE7; color: #15803D; border: 1px solid #BBF7D0; }

    /* CONTEÚDO EDITORIAL DA PÁGINA INTERNA (COMPLETO) */
    .article-container {
        background-color: #FFFFFF;
        padding: 40px;
        border-radius: 6px;
        border: 1px solid #E2DED6;
        margin-bottom: 30px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.02);
    }
    .article-container p {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 17px;
        color: #222222;
        line-height: 1.9;
        margin-bottom: 22px;
    }
    .article-container img, .article-container figure {
        display: block;
        max-width: 100% !important;
        height: auto !important;
        max-height: 500px;
        object-fit: contain;
        background-color: #F8F8F8;
        border-radius: 4px;
        margin: 25px auto;
        border: 1px solid #E2DED6;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. FUNÇÕES DE SUPORTE E RENDERIZAÇÃO
# ==============================================================================
def render_badge(categoria):
    cat = categoria.lower()
    if "onu" in cat:
        return '<span class="badge badge-onu"><i class="fa-solid fa-globe"></i> ONU</span>'
    elif "mre" in cat:
        return '<span class="badge badge-mre"><i class="fa-solid fa-landmark"></i> MRE</span>'
    elif "notícia" in cat or "noticia" in cat:
        return '<span class="badge badge-noticias"><i class="fa-solid fa-newspaper"></i> Notícia</span>'
    else:
        return '<span class="badge badge-notas"><i class="fa-solid fa-file-lines"></i> Nota</span>'

# ==============================================================================
# 5. CARREGAMENTO INTELIGENTE E ANTI-DUPLICAÇÃO DOS FEEDS
# ==============================================================================
FONTES = [
    ("https://www.gov.br/mre/pt-br/centrais-de-conteudo/notas-a-imprensa/RSS", "MRE", "Nota à Imprensa"),
    ("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "ONU", "Notícia")
]

FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80"
]

@str_lit.cache_data(ttl=900)
def carregar_noticias():
    itens = []
    urls_vistas = set()
    regioes_lista = ["Global", "América do Sul", "Europa", "Oriente Médio"]
    temas_origem = ["Governança Global", "Segurança e Paz", "Direito Internacional", "Economia e Comércio"]

    idx_count = 0
    for url_feed, orgao, tipo_base in FONTES:
        try:
            feed = feedparser.parse(url_feed)
            for entry in feed.entries:
                link_artigo = entry.get("link", "")
                if not link_artigo or link_artigo in urls_vistas:
                    continue  # Evita duplicatas exatas
                
                urls_vistas.add(link_artigo)

                # Extração profunda do conteúdo completo (prioriza content:encoded)
                raw_content = ""
                if 'content' in entry and len(entry.content) > 0:
                    raw_content = entry.content[0].get('value', '')
                if not raw_content or len(raw_content.strip()) < 50:
                    raw_content = entry.get("summary", "") or entry.get("description", "")

                soup = BeautifulSoup(raw_content, "html.parser")
                
                # Gera resumo limpo para o card
                resumo_limpo = soup.get_text().strip()
                if len(resumo_limpo) > 220:
                    resumo_limpo = resumo_limpo[:220] + "..."
                if not resumo_limpo:
                    resumo_limpo = "Consulte o texto completo e os desdobramentos oficiais diretamente no repositório institucional."

                # Extração de imagem do feed ou do corpo HTML
                imagem_url = FALLBACK_IMAGES[idx_count % len(FALLBACK_IMAGES)]
                if 'media_content' in entry and len(entry.media_content) > 0:
                    imagem_url = entry.media_content[0].get('url', imagem_url)
                else:
                    img_tag = soup.find('img')
                    if img_tag and img_tag.get('src'):
                        imagem_url = img_tag['src']

                itens.append({
                    "id": idx_count,
                    "titulo": entry.get("title", "Sem Título"),
                    "resumo": resumo_limpo,
                    "conteudo_completo": raw_content if len(raw_content) > 50 else f"<p>{resumo_limpo}</p>",
                    "orgao": orgao,
                    "tipo": tipo_base,
                    "tema": temas_origem[idx_count % len(temas_origem)],
                    "regiao": regioes_lista[idx_count % len(regioes_lista)],
                    "imagem": imagem_url,
                    "link": link_artigo,
                    "data": entry.get("published", "Data recente")
                })
                idx_count += 1
        except Exception:
            continue
    return itens

acervo_noticias = carregar_noticias()
temas_disponiveis = sorted(list(set([item["tema"] for item in acervo_noticias])))

# ==============================================================================
# 6. ROTEAMENTO DA PÁGINA DE LEITURA DETALHADA
# ==============================================================================
article_id_param = str_lit.query_params.get("article", None)

if article_id_param is not None:
    try:
        art_idx = int(article_id_param)
        artigo_atual = next((item for item in acervo_noticias if item["id"] == art_idx), None)
    except:
        artigo_atual = None

    if artigo_atual:
        if str_lit.button("← Voltar ao Acervo Principal", use_container_width=False):
            str_lit.query_params.clear()
            str_lit.rerun()

        str_lit.markdown("<br>", unsafe_allow_html=True)
        str_lit.markdown(f"<div>{render_badge(artigo_atual['orgao'])}{render_badge(artigo_atual['tipo'])}</div>", unsafe_allow_html=True)
        str_lit.markdown(f"<div style='font-size: 13px; color: #555555; margin-top: 6px; font-weight: 500;'>🏷️ Tema: {artigo_atual['tema']} &nbsp;|&nbsp; 📍 {artigo_atual['regiao']} &nbsp;|&nbsp; 📅 {artigo_atual['data']}</div>", unsafe_allow_html=True)
        
        str_lit.markdown(f"<h1 style='font-family: Newsreader, serif; font-size: 36px; margin-top: 15px; margin-bottom: 20px; line-height: 1.2;'>{artigo_atual['titulo']}</h1>", unsafe_allow_html=True)
        
        str_lit.markdown(f"""
            <div style="width: 100%; max-height: 480px; text-align: center; overflow: hidden; border-radius: 6px; margin-bottom: 25px; border: 1px solid #E2DED6; background-color: #1A1A1A;">
                <img src="{artigo_atual['imagem']}" style="max-width: 100%; height: auto; object-fit: contain; margin: 0 auto;" alt="Capa da Matéria" />
            </div>
        """, unsafe_allow_html=True)
        
        str_lit.markdown(f"""
            <div class="article-container">
                {artigo_atual['conteudo_completo']}
            </div>
        """, unsafe_allow_html=True)
        
        str_lit.markdown("---")
        str_lit.markdown(f"""
            <div style="margin-top: 20px; margin-bottom: 40px;">
                <a href="{artigo_atual['link']}" target="_blank" style="display: block; background-color: #1A1A1A; color: #F7F5F0; padding: 14px 24px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; border-radius: 4px; text-decoration: none; text-align: center;">
                    🔗 Acessar Publicação Oficial Completa na Origem &nbsp;<i class="fa-solid fa-arrow-up-right-from-square"></i>
                </a>
            </div>
        """, unsafe_allow_html=True)

        str_lit.stop()

# ==============================================================================
# 7. LAYOUT PRINCIPAL (HOME / ACERVO SIMÉTRICO)
# ==============================================================================
user_cur = str_lit.session_state["current_user"]
user_data = str_lit.session_state["users_db"].get(user_cur, {"plan": "free", "access_count": 0})

col_title, col_top_actions = str_lit.columns([2.5, 1.5])

with col_title:
    str_lit.markdown("""
        <div style="font-family: 'Newsreader', serif; font-size: 28px; font-weight: 600; letter-spacing: -0.03em; margin: 0;">
            <span style="color: #1A1A1A;">Ubique</span> <span style="color: #666666; font-style: italic;">News</span>
        </div>
        <div style="font-size: 11px; color: #777777; text-transform: uppercase; letter-spacing: 0.15em; margin-top: 2px;">
            sua dose diária de inteligência para o CACD
        </div>
    """, unsafe_allow_html=True)

with col_top_actions:
    c_btn1, c_btn2 = str_lit.columns(2)
    with c_btn1:
        if str_lit.button("Conta", key="top_acc", use_container_width=True):
            str_lit.session_state["show_register_modal"] = True
            str_lit.rerun()
    with c_btn2:
        if str_lit.button("Assinar", key="top_sub", use_container_width=True):
            str_lit.session_state["show_plans_modal"] = True
            str_lit.rerun()

str_lit.markdown("<hr style='border: none; border-top: 1px solid #1A1A1A; margin-top: 12px; margin-bottom: 24px;'>", unsafe_allow_html=True)

# ==============================================================================
# 8. BARRA LATERAL DE FILTRAGEM
# ==============================================================================
with str_lit.sidebar:
    str_lit.markdown("### 🏛️ UBIQUE NEWS")
    str_lit.caption("Painel de Inteligência Informativa")
    str_lit.markdown("---")

    categoria_sel = str_lit.selectbox("Categoria / Órgão:", ["Todas", "ONU", "MRE"])
    tema_sel = str_lit.selectbox("Tema:", ["Todos os Temas"] + temas_disponiveis)
    regiao_sel = str_lit.selectbox("Região:", ["Todas as Regiões", "Global", "América do Sul", "Europa", "Oriente Médio"])
    busca = str_lit.text_input("🔍 Busca por palavra-chave", placeholder="Ex: COP, ONU, Comércio")

# ==============================================================================
# 9. FILTRAGEM DE ITENS
# ==============================================================================
noticias_filtradas = acervo_noticias

if categoria_sel == "ONU":
    noticias_filtradas = [n for n in noticias_filtradas if n["orgao"] == "ONU"]
elif categoria_sel == "MRE":
    noticias_filtradas = [n for n in noticias_filtradas if n["orgao"] == "MRE"]

if tema_sel != "Todos os Temas":
    noticias_filtradas = [n for n in noticias_filtradas if n["tema"] == tema_sel]

if regiao_sel != "Todas as Regiões":
    noticias_filtradas = [n for n in noticias_filtradas if n["regiao"] == regiao_sel]

if busca:
    noticias_filtradas = [n for n in noticias_filtradas if busca.lower() in n["titulo"].lower() or busca.lower() in n["resumo"].lower()]

# ==============================================================================
# 10. GRADE DE EXIBIÇÃO SIMÉTRICA (2 COLUNAS IDÊNTICAS COM BOTÕES ALINHADOS)
# ==============================================================================
str_lit.markdown("### 📰 Notícias & Análises Estratégicas")

if len(noticias_filtradas) > 0:
    for i in range(0, len(noticias_filtradas), 2):
        row_cols = str_lit.columns(2)
        
        # Primeiro card da linha
        with row_cols[0]:
            item1 = noticias_filtradas[i]
            str_lit.markdown(f"""
                <div class="news-card">
                    <div class="card-img-container">
                        <img src="{item1['imagem']}" class="card-img" alt="Capa" />
                    </div>
                    <div class="card-body">
                        <div>{render_badge(item1['orgao'])}{render_badge(item1['tipo'])}</div>
                        <div style="font-size: 11px; color: #555555; margin-bottom: 6px; font-weight: 600;">🏷️ {item1['tema']} | 📍 {item1['regiao']}</div>
                        <div class="card-title">{item1['titulo']}</div>
                        <div class="card-excerpt">{item1['resumo']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if str_lit.button("📖 ABRIR NOTÍCIA COMPLETA", key=f"btn_{item1['id']}", use_container_width=True):
                str_lit.query_params["article"] = str(item1['id'])
                str_lit.rerun()

        # Segundo card da linha (se existir)
        if i + 1 < len(noticias_filtradas):
            with row_cols[1]:
                item2 = noticias_filtradas[i + 1]
                str_lit.markdown(f"""
                    <div class="news-card">
                        <div class="card-img-container">
                            <img src="{item2['imagem']}" class="card-img" alt="Capa" />
                        </div>
                        <div class="card-body">
                            <div>{render_badge(item2['orgao'])}{render_badge(item2['tipo'])}</div>
                            <div style="font-size: 11px; color: #555555; margin-bottom: 6px; font-weight: 600;">🏷️ {item2['tema']} | 📍 {item2['regiao']}</div>
                            <div class="card-title">{item2['titulo']}</div>
                            <div class="card-excerpt">{item2['resumo']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                if str_lit.button("📖 ABRIR NOTÍCIA COMPLETA", key=f"btn_{item2['id']}", use_container_width=True):
                    str_lit.query_params["article"] = str(item2['id'])
                    str_lit.rerun()
        else:
            with row_cols[1]:
                str_lit.markdown("<div style='height: 480px;'></div>", unsafe_allow_html=True)
else:
    str_lit.info("Nenhum item encontrado com os filtros selecionados.")
