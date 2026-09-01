import streamlit as str_lit
import streamlit.components.v1 as components
import feedparser
from datetime import datetime, date
import re
import stripe

# ==============================================================================
# 1. CONFIGURAÇÃO DE SEGREDOS E STRIPE
# ==============================================================================
STRIPE_SECRET_KEY = str_lit.secrets.get("STRIPE_SECRET_KEY", "sk_test_exemplo")
STRIPE_PRICE_MONTHLY = str_lit.secrets.get("STRIPE_PRICE_MONTHLY", "price_monthly_id")
STRIPE_PRICE_YEARLY = str_lit.secrets.get("STRIPE_PRICE_YEARLY", "price_yearly_id")
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
# 3. GERENCIAMENTO DE SESSÃO E ROTEAMENTO INICIAL
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

query_params = str_lit.query_params
if query_params.get("payment") == "success":
    user = str_lit.session_state.get("current_user", "visitante")
    if user in str_lit.session_state["users_db"]:
        str_lit.session_state["users_db"][user]["plan"] = "premium"
    str_lit.toast("🎉 Assinatura Premium confirmada com sucesso!", icon="✅")

def verificar_reset_diario(username):
    user_data = str_lit.session_state["users_db"].get(username)
    if user_data:
        hoje_str = str(date.today())
        if user_data.get("last_date") != hoje_str:
            user_data["access_count"] = 0
            user_data["last_date"] = hoje_str

verificar_reset_diario(str_lit.session_state["current_user"])

# ==============================================================================
# 4. ESTILOS CSS PERSONALIZADOS (ESTÉTICA AOC.MEDIA + CORES DE FAIXAS)
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

    .top-nav-btn button {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 11px !important;
        padding: 6px 14px !important;
        font-weight: 600 !important;
        letter-spacing: 0.05em !important;
        border-radius: 2px !important;
        height: 36px !important;
        min-height: 0px !important;
        text-transform: uppercase;
        width: 100%;
        color: #F0E6D2 !important;
    }

    .top-nav-btn-primary button {
        background-color: #1A1A1A !important;
        border: 1px solid #1A1A1A !important;
    }
    .top-nav-btn-primary button:hover {
        background-color: #333333 !important;
        color: #F7F5F0 !important;
    }

    .top-nav-btn-secondary button {
        background-color: transparent !important;
        border: 1px solid #1A1A1A !important;
        color: #1A1A1A !important;
    }
    .top-nav-btn-secondary button:hover {
        background-color: #1A1A1A !important;
        color: #F7F5F0 !important;
    }

    /* BADGES E FAIXAS ESTILO AOC.MEDIA */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        border-radius: 2px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        margin-right: 6px;
        margin-bottom: 8px;
    }
    .badge-onu { background-color: #E8EEF5; color: #1D4ED8; border: 1px solid #BFDBFE; }
    .badge-mre { background-color: #F3F4F6; color: #374151; border: 1px solid #D1D5DB; }
    .badge-noticias { background-color: #FEF3C7; color: #B45309; border: 1px solid #FDE68A; }
    .badge-notas { background-color: #DCFCE7; color: #15803D; border: 1px solid #BBF7D0; }
    .badge-discursos { background-color: #FEE2E2; color: #B91C1C; border: 1px solid #FECACA; }
    .badge-lideres { background-color: #F3E8FF; color: #7E22CE; border: 1px solid #E9D5FF; }
    .badge-sg { background-color: #CCFBF1; color: #0F766E; border: 1px solid #99F6E4; }
    .badge-csonu { background-color: #FFEDD5; color: #C2410C; border: 1px solid #FED7AA; }

    /* FAIXA TOPO DETALHE (AOC.MEDIA STYLE) */
    .aoc-stripe-onu { background-color: #1D4ED8; height: 6px; width: 100%; margin-bottom: 20px; }
    .aoc-stripe-mre { background-color: #374151; height: 6px; width: 100%; margin-bottom: 20px; }
    .aoc-stripe-noticias { background-color: #B45309; height: 6px; width: 100%; margin-bottom: 20px; }
    .aoc-stripe-notas { background-color: #15803D; height: 6px; width: 100%; margin-bottom: 20px; }
    .aoc-stripe-discursos { background-color: #B91C1C; height: 6px; width: 100%; margin-bottom: 20px; }
    .aoc-stripe-lideres { background-color: #7E22CE; height: 6px; width: 100%; margin-bottom: 20px; }
    .aoc-stripe-sg { background-color: #0F766E; height: 6px; width: 100%; margin-bottom: 20px; }
    .aoc-stripe-csonu { background-color: #C2410C; height: 6px; width: 100%; margin-bottom: 20px; }

    .news-card {
        background: #FFFFFF;
        border-radius: 4px;
        border: 1px solid #E2DED6;
        overflow: hidden;
        margin-bottom: 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.04);
    }
    .card-img-container {
        width: 100%;
        height: 200px;
        overflow: hidden;
        background-color: #1A1A1A;
        position: relative;
        cursor: pointer;
    }
    .card-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.5s ease;
    }
    .news-card:hover .card-img { transform: scale(1.03); }
    
    .card-body { padding: 20px; }
    .card-title {
        font-family: 'Newsreader', serif;
        font-size: 20px;
        font-weight: 600;
        color: #1A1A1A;
        line-height: 1.25;
        margin-bottom: 10px;
        cursor: pointer;
    }
    .card-title:hover { color: #555555; text-decoration: underline; }
    .card-excerpt { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 13.5px; color: #666666; line-height: 1.6; margin-bottom: 14px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. GERADOR DE BADGES E FAIXAS HTML
# ==============================================================================
def render_badge(categoria):
    cat_lower = categoria.lower()
    if "conselho de segurança" in cat_lower or "csonu" in cat_lower:
        return '<span class="badge badge-csonu"><i class="fa-solid fa-shield-halved"></i> Conselho de Segurança</span>'
    elif "secretário-geral" in cat_lower or "sg" in cat_lower:
        return '<span class="badge badge-sg"><i class="fa-solid fa-user-tie"></i> Discurso SG da ONU</span>'
    elif "líderes" in cat_lower or "chefe de estado" in cat_lower:
        return '<span class="badge badge-lideres"><i class="fa-solid fa-podium"></i> Discurso de Líderes</span>'
    elif "onu" in cat_lower:
        return '<span class="badge badge-onu"><i class="fa-solid fa-globe"></i> ONU</span>'
    elif "mre" in cat_lower:
        return '<span class="badge badge-mre"><i class="fa-solid fa-landmark"></i> MRE</span>'
    elif "notícia" in cat_lower or "noticia" in cat_lower:
        return '<span class="badge badge-noticias"><i class="fa-solid fa-newspaper"></i> Notícia</span>'
    elif "nota" in cat_lower:
        return '<span class="badge badge-notas"><i class="fa-solid fa-file-lines"></i> Nota</span>'
    elif "discurso" in cat_lower:
        return '<span class="badge badge-discursos"><i class="fa-solid fa-bullhorn"></i> Discurso</span>'
    else:
        return f'<span class="badge badge-mre"><i class="fa-solid fa-tag"></i> {categoria}</span>'

def get_stripe_class(categoria):
    cat_lower = categoria.lower()
    if "conselho de segurança" in cat_lower or "csonu" in cat_lower: return "aoc-stripe-csonu"
    elif "secretário-geral" in cat_lower or "sg" in cat_lower: return "aoc-stripe-sg"
    elif "líderes" in cat_lower or "chefe de estado" in cat_lower: return "aoc-stripe-lideres"
    elif "onu" in cat_lower: return "aoc-stripe-onu"
    elif "mre" in cat_lower: return "aoc-stripe-mre"
    elif "notícia" in cat_lower or "noticia" in cat_lower: return "aoc-stripe-noticias"
    elif "nota" in cat_lower: return "aoc-stripe-notas"
    elif "discurso" in cat_lower: return "aoc-stripe-discursos"
    else: return "aoc-stripe-mre"

# ==============================================================================
# 6. EXTRATOR E CARREGAMENTO DE FEED COM CLASSIFICAÇÃO DE TEMAS DE ORIGEM
# ==============================================================================
FONTES = {
    "MRE (Notas)": ("https://www.gov.br/mre/pt-br/centrais-de-conteudo/notas-a-imprensa/RSS", "MRE", "Nota à Imprensa"),
    "ONU (Notícias)": ("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "ONU", "Notícia")
}

FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80"
]

def extrair_url_imagem(entry, index):
    if 'media_content' in entry and len(entry.media_content) > 0:
        return entry.media_content[0].get('url', '')
    if 'enclosures' in entry and len(entry.enclosures) > 0:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image'):
                return enc.get('href', '')
    raw_html = entry.get("summary", "") or entry.get("description", "")
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', raw_html)
    if match:
        return match.group(1)
    return FALLBACK_IMAGES[index % len(FALLBACK_IMAGES)]

@str_lit.cache_data(ttl=1800)
def carregar_noticias():
    itens = []
    regioes_lista = ["América do Sul", "Europa", "Oriente Médio", "Global"]
    
    tipos_possiveis = [
        "Notícia", 
        "Nota", 
        "Discurso", 
        "Discurso de Líderes de Estado", 
        "Discurso do Secretário-Geral das Nações Unidas", 
        "Conselho de Segurança"
    ]
    
    temas_origem = [
        "Paz e Segurança Internacionais", 
        "Direitos Humanos", 
        "Desenvolvimento Sustentável e Clima", 
        "Direito Internacional", 
        "Cooperação Multilateral", 
        "Desarmamento"
    ]

    idx_count = 0
    for nome, (url, orgao, tipo_base) in FONTES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            resumo = re.sub('<[^<]+?>', '', entry.get("summary", entry.get("description", "")))[:250] + "..."
            texto_completo = re.sub('<[^<]+?>', '', entry.get("summary", entry.get("description", "")))
            imagem_url = extrair_url_imagem(entry, idx_count)
            tipo_atribuido = tipos_possiveis[idx_count % len(tipos_possiveis)]
            tema_atribuido = temas_origem[idx_count % len(temas_origem)]
            
            if 'tags' in entry and len(entry.tags) > 0:
                tema_atribuido = entry.tags[0].get('term', tema_atribuido)

            itens.append({
                "id": idx_count,
                "titulo": entry.title,
                "resumo": resumo,
                "conteudo_completo": texto_completo if len(texto_completo) > 50 else f"Conteúdo institucional oficial obtido através do feed de origem. {resumo}",
                "orgao": orgao,
                "tipo": tipo_atribuido,
                "tema": tema_atribuido,
                "regiao": regioes_lista[idx_count % len(regioes_lista)],
                "imagem": imagem_url,
                "link": entry.link,
                "data": entry.get("published", "Data recente")
            })
            idx_count += 1
    return itens

acervo_noticias = carregar_noticias()
temas_disponiveis = sorted(list(set([item["tema"] for item in acervo_noticias])))

# ==============================================================================
# 7. ROTEAMENTO DA PÁGINA INTERNA DE DETALHES (ESTILO AOC.MEDIA)
# ==============================================================================
article_id_param = str_lit.query_params.get("article", None)

if article_id_param is not None:
    try:
        art_idx = int(article_id_param)
        artigo_atual = next((item for item in acervo_noticias if item["id"] == art_idx), None)
    except:
        artigo_atual = None

    if artigo_atual:
        stripe_classe = get_stripe_class(artigo_atual['tipo'])
        
        # Faixa colorida no topo (estilo AOC.media)
        str_lit.markdown(f'<div class="{stripe_classe}"></div>', unsafe_allow_html=True)
        
        col_voltar, col_lang = str_lit.columns([3, 1])
        with col_voltar:
            if str_lit.button("← Voltar ao Repositório", use_container_width=False):
                str_lit.query_params.clear()
                str_lit.rerun()
        
        with col_lang:
            idioma_sel = str_lit.selectbox("🌐 Idioma / Language", ["Português (PT)", "English (EN)", "Español (ES)", "Français (FR)"], key="select_lang")

        str_lit.markdown("<br>", unsafe_allow_html=True)
        
        # Badges e Metadados
        str_lit.markdown(f"<div>{render_badge(artigo_atual['orgao'])}{render_badge(artigo_atual['tipo'])}</div>", unsafe_allow_html=True)
        str_lit.markdown(f"<div style='font-size: 13px; color: #555555; margin-top: 4px; font-weight: 500;'>🏷️ Tema: {artigo_atual['tema']} &nbsp;|&nbsp; 📍 {artigo_atual['regiao']} &nbsp;|&nbsp; 📅 {artigo_atual['data']}</div>", unsafe_allow_html=True)
        
        # Título
        str_lit.markdown(f"<h1 style='font-family: Newsreader, serif; font-size: 34px; margin-top: 15px; margin-bottom: 20px; line-height: 1.2;'>{artigo_atual['titulo']}</h1>", unsafe_allow_html=True)
        
        # Imagem de Capa
        str_lit.markdown(f"""
            <div style="width: 100%; max-height: 450px; overflow: hidden; border-radius: 4px; margin-bottom: 25px; border: 1px solid #E2DED6;">
                <img src="{artigo_atual['imagem']}" style="width: 100%; object-fit: cover;" alt="Capa" />
            </div>
        """, unsafe_allow_html=True)
        
        # Corpo do Texto
        str_lit.markdown(f"""
            <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 16px; color: #2A2A2A; line-height: 1.8; margin-bottom: 30px;">
                <p>{artigo_atual['conteudo_completo']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        str_lit.markdown("---")
        
        # Botão para fonte original externa
        col_ext_1, col_ext_2 = str_lit.columns([2, 2])
        with col_ext_1:
            if str_lit.button("🔗 Acessar Publicação Completa no Site de Origem", use_container_width=True):
                str_lit.markdown(f'<meta http-equiv="refresh" content="0; url={artigo_atual["link"]}">', unsafe_allow_html=True)
                str_lit.rerun()

        str_lit.stop()

# ==============================================================================
# 8. LAYOUT PRINCIPAL (HOME / ACERVO)
# ==============================================================================
user_cur = str_lit.session_state["current_user"]
user_data = str_lit.session_state["users_db"].get(user_cur, {"plan": "free", "access_count": 0})

col_title, col_top_actions = str_lit.columns([2.2, 1.8])

with col_title:
    str_lit.markdown("""
        <div style="font-family: 'Newsreader', serif; font-size: 26px; font-weight: 600; letter-spacing: -0.03em; margin: 0; padding-top: 2px;">
            <span style="color: #1A1A1A;">Repositório</span> <span style="color: #666666; font-style: italic;">Diplomático</span>
        </div>
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 11px; color: #777777; text-transform: uppercase; letter-spacing: 0.15em; margin-top: 2px; margin-bottom: 4px;">
            a sua dose diária de informação
        </div>
    """, unsafe_allow_html=True)

with col_top_actions:
    col_nav_1, col_nav_2 = str_lit.columns(2)
    with col_nav_1:
        str_lit.markdown('<div class="top-nav-btn top-nav-btn-secondary">', unsafe_allow_html=True)
        if user_cur == "visitante":
            if str_lit.button("Conta", key="top_create_account", use_container_width=True):
                str_lit.session_state["show_register_modal"] = True
                str_lit.rerun()
        else:
            str_lit.caption(f"👤 {user_cur}")
        str_lit.markdown('</div>', unsafe_allow_html=True)

    with col_nav_2:
        str_lit.markdown('<div class="top-nav-btn top-nav-btn-primary">', unsafe_allow_html=True)
        if str_lit.button("Assinar", key="top_subscribe", use_container_width=True):
            str_lit.session_state["show_plans_modal"] = True
            str_lit.rerun()
        str_lit.markdown('</div>', unsafe_allow_html=True)

str_lit.markdown("<hr style='border: none; border-top: 1px solid #1A1A1A; margin-top: 10px; margin-bottom: 24px;'>", unsafe_allow_html=True)

# ==============================================================================
# 9. BARRA LATERAL (FILTROS)
# ==============================================================================
with str_lit.sidebar:
    str_lit.markdown("### 🏛️ REPOSITÓRIO")
    str_lit.caption("a sua dose diária de informação")
    str_lit.markdown("---")

    str_lit.markdown("### 🏷️ Classificação & Filtros")
    
    opcoes_categoria = [
        "Todas", 
        "ONU", 
        "MRE", 
        "Notícias", 
        "Notas", 
        "Discursos", 
        "Discurso de Líderes de Estado", 
        "Discurso do Secretário-Geral das Nações Unidas", 
        "Conselho de Segurança"
    ]
    
    categoria_sel = str_lit.selectbox("Categoria / Órgão / Seção:", opcoes_categoria)
    tema_sel = str_lit.selectbox("Tema (Origem):", ["Todos os Temas"] + temas_disponiveis)
    regiao_sel = str_lit.selectbox("Região:", ["Todas as Regiões", "América do Sul", "Europa", "Oriente Médio", "Global"])

    str_lit.markdown("---")
    busca = str_lit.text_input("🔍 Busca por palavra-chave", placeholder="Ex: G20, COP, CSNU")

# ==============================================================================
# 10. LÓGICA DE FILTRAGEM
# ==============================================================================
noticias_filtradas = acervo_noticias

if categoria_sel == "ONU":
    noticias_filtradas = [n for n in noticias_filtradas if n["orgao"] == "ONU"]
elif categoria_sel == "MRE":
    noticias_filtradas = [n for n in noticias_filtradas if n["orgao"] == "MRE"]
elif categoria_sel == "Notícias":
    noticias_filtradas = [n for n in noticias_filtradas if n["tipo"].lower() in ["notícia", "noticia"]]
elif categoria_sel == "Notas":
    noticias_filtradas = [n for n in noticias_filtradas if n["tipo"].lower() == "nota"]
elif categoria_sel == "Discursos":
    noticias_filtradas = [n for n in noticias_filtradas if "discurso" in n["tipo"].lower()]
elif categoria_sel == "Discurso de Líderes de Estado":
    noticias_filtradas = [n for n in noticias_filtradas if n["tipo"] == "Discurso de Líderes de Estado"]
elif categoria_sel == "Discurso do Secretário-Geral das Nações Unidas":
    noticias_filtradas = [n for n in noticias_filtradas if n["tipo"] == "Discurso do Secretário-Geral das Nações Unidas"]
elif categoria_sel == "Conselho de Segurança":
    noticias_filtradas = [n for n in noticias_filtradas if n["tipo"] == "Conselho de Segurança"]

if tema_sel != "Todos os Temas":
    noticias_filtradas = [n for n in noticias_filtradas if n["tema"] == tema_sel]

if regiao_sel != "Todas as Regiões":
    noticias_filtradas = [n for n in noticias_filtradas if n["regiao"] == regiao_sel]

if busca:
    noticias_filtradas = [n for n in noticias_filtradas if busca.lower() in n["titulo"].lower() or busca.lower() in n["resumo"].lower()]

# ==============================================================================
# 11. GRADE DE NOTÍCIAS COM CLIQUE CORRIGIDO E BOTÕES DE SUPORTE
# ==============================================================================
str_lit.markdown("### 📰 Acervo de Documentos & Discursos Diplomáticos")

if len(noticias_filtradas) > 0:
    grid_cols = str_lit.columns(2)
    for idx, item in enumerate(noticias_filtradas):
        with grid_cols[idx % 2]:
            badge_orgao = render_badge(item['orgao'])
            badge_tipo = render_badge(item['tipo'])
            
            # Script JS ajustado com window.location.pathname para funcionar perfeitamente em qualquer servidor/nuvem
            card_html = f"""
                <div class="news-card">
                    <div class="card-img-container" onclick="window.location.href = window.location.pathname + '?article={item['id']}';">
                        <img src="{item['imagem']}" class="card-img" alt="Capa" />
                    </div>
                    <div class="card-body">
                        <div>{badge_orgao}{badge_tipo}</div>
                        <div style="font-size: 11px; color: #555555; margin-bottom: 6px; font-weight: 600;">🏷️ Tema: {item['tema']} | 📍 {item['regiao']}</div>
                        <div class="card-title" onclick="window.location.href = window.location.pathname + '?article={item['id']}';">{item['titulo']}</div>
                        <div class="card-excerpt">{item['resumo']}</div>
                    </div>
                </div>
            """
            str_lit.markdown(card_html, unsafe_allow_html=True)
            
            # Botão oficial do Streamlit como alternativa nativa infalível de acesso
            if str_lit.button(f"📖 LER COMPLETO", key=f"read_grid_{item['id']}", use_container_width=True):
                if user_data["plan"] == "free":
                    user_data["access_count"] += 1
                str_lit.query_params["article"] = str(item['id'])
                str_lit.rerun()
else:
    str_lit.info("Nenhum documento ou discurso encontrado com os filtros atuais.")
