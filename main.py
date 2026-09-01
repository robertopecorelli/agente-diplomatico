import streamlit as st
import streamlit.components.v1 as components
import feedparser
from datetime import datetime, date
import re
import stripe

# ==============================================================================
# 1. CONFIGURAÇÃO DE SEGREDOS E STRIPE
# ==============================================================================
STRIPE_SECRET_KEY = st.secrets.get("STRIPE_SECRET_KEY", "sk_test_exemplo")
STRIPE_PRICE_MONTHLY = st.secrets.get("STRIPE_PRICE_MONTHLY", "price_monthly_id")
STRIPE_PRICE_YEARLY = st.secrets.get("STRIPE_PRICE_YEARLY", "price_yearly_id")
DOMAIN_URL = st.secrets.get("DOMAIN_URL", "http://localhost:8501")

stripe.api_key = STRIPE_SECRET_KEY

# ==============================================================================
# 2. CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Repositório Diplomático | Acervo CACD",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="auto"
)

# ==============================================================================
# 3. GERENCIAMENTO DE SESSÃO
# ==============================================================================
if "users_db" not in st.session_state:
    st.session_state["users_db"] = {
        "visitante": {"plan": "free", "access_count": 0, "last_date": str(date.today()), "email": ""}
    }

if "current_user" not in st.session_state:
    st.session_state["current_user"] = "visitante"

if "show_plans_modal" not in st.session_state:
    st.session_state["show_plans_modal"] = False

if "show_register_modal" not in st.session_state:
    st.session_state["show_register_modal"] = False

query_params = st.query_params
if query_params.get("payment") == "success":
    user = st.session_state.get("current_user", "visitante")
    if user in st.session_state["users_db"]:
        st.session_state["users_db"][user]["plan"] = "premium"
    st.toast("🎉 Assinatura Premium confirmada com sucesso!", icon="✅")

def verificar_reset_diario(username):
    user_data = st.session_state["users_db"].get(username)
    if user_data:
        hoje_str = str(date.today())
        if user_data.get("last_date") != hoje_str:
            user_data["access_count"] = 0
            user_data["last_date"] = hoje_str

verificar_reset_diario(st.session_state["current_user"])

def enviar_email_confirmacao(email_destino, nome_usuario):
    st.toast(f"📧 E-mail de confirmação enviado para: {email_destino}", icon="📩")

# ==============================================================================
# 4. ESTILOS CSS PERSONALIZADOS (ESTÉTICA EDITORIAL + BADGES/ÍCONES)
# ==============================================================================
st.markdown("""
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

    /* SISTEMA DE TAGS / BADGES ESTILO EDITORIAL COM CORES E ÍCONES */
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
    }
    .card-excerpt { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 13.5px; color: #666666; line-height: 1.6; margin-bottom: 14px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. GERADOR DE BADGES HTML COM ÍCONES MODERNOS E MINIMALISTAS
# ==============================================================================
def render_badge(categoria):
    cat_lower = categoria.lower()
    if "onu" in cat_lower:
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

# ==============================================================================
# 6. EXTRATOR E CARREGAMENTO DE FEED
# ==============================================================================
FONTES = {
    "MRE (Notas)": ("https://www.gov.br/mre/pt-br/centrais-de-conteudo/notas-a-imprensa/RSS", "MRE", "Nota à Imprensa"),
    "ONU (Notícias)": ("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "ONU", "Notícia")
}

FALLBACK_IMAGES = [
    "
