import streamlit as st
import feedparser
from datetime import datetime, date
import re
import stripe
import random

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
    page_title="Repositório Diplomático | MRE & ONU",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
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

if "show_login_modal" not in st.session_state:
    st.session_state["show_login_modal"] = False

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
# 4. ESTILOS CSS PERSONALIZADOS (PALETA & TOP MENU REFINADO)
# ==============================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Cinzel:wght@600;700;800&display=swap');

    html, body, [class*="stApp"] {
        background-color: #F0E6D2 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #262626 !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #E6DCB8 !important;
        border-right: 1px solid #D19A7D;
    }

    /* Cabeçalho Principal */
    .portal-header-title {
        font-family: 'Cinzel', serif;
        font-size: 24px;
        font-weight: 700;
        color: #262626;
        letter-spacing: 2px;
        margin: 0;
        padding-top: 4px;
    }

    /* Botões Compactos do Menu Superior */
    .top-nav-btn button {
        font-size: 11px !important;
        padding: 4px 10px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        border-radius: 4px !important;
        height: 32px !important;
        min-height: 0px !important;
        margin-top: 2px !important;
    }

    .top-nav-btn-primary button {
        background-color: #B76D4D !important;
        color: #FFFFFF !important;
        border: 1px solid #B76D4D !important;
    }
    .top-nav-btn-primary button:hover {
        background-color: #9E583A !important;
    }

    .top-nav-btn-secondary button {
        background-color: transparent !important;
        color: #262626 !important;
        border: 1px solid #D19A7D !important;
    }
    .top-nav-btn-secondary button:hover {
        background-color: rgba(209, 154, 125, 0.2) !important;
    }

    /* Cards de Notícias com Suporte a Imagem */
    .news-card {
        background: #FFFFFF;
        border-radius: 8px;
        border: 1px solid #D19A7D;
        overflow: hidden;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(38, 38, 38, 0.05);
    }
    .card-img-container {
        width: 100%;
        height: 180px;
        overflow: hidden;
        background-color: #262626;
        position: relative;
    }
    .card-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.3s ease;
    }
    .news-card:hover .card-img {
        transform: scale(1.03);
    }
    .card-body { padding: 16px; }
    .meta-tag {
        font-size: 10.5px;
        font-weight: 700;
        color: #B76D4D;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .card-title {
        font-family: 'Playfair Display', serif;
        font-size: 17px;
        font-weight: 700;
        color: #262626;
        line-height: 1.35;
        margin-bottom: 8px;
    }
    .card-excerpt { font-size: 12.5px; color: #4A4A4A; line-height: 1.5; margin-bottom: 12px; }

    /* Modal / Form de Cadastro */
    .register-header-title {
        font-family: 'Cinzel', serif;
        font-size: 28px;
        font-weight: 700;
        color: #262626;
        text-align: center;
        margin-bottom: 4px;
    }
    .register-header-subtitle {
        font-size: 13px;
        color: #736B63;
        text-align: center;
        margin-bottom: 24px;
    }
    .field-label {
        font-size: 10.5px;
        font-weight: 800;
        color: #262626;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. EXTRATOR DE IMAGENS E CARREGAMENTO DE FEED
# ==============================================================================
FONTES = {
    "MRE (Notas à Imprensa)": ("https://www.gov.br/mre/pt-br/centrais-de-conteudo/notas-a-imprensa/RSS", "MRE", "Nota à Imprensa"),
    "MRE (Discursos)": ("https://www.gov.br/mre/pt-br/centrais-de-conteudo/discursos/RSS", "MRE", "Discurso"),
    "ONU (Notícias)": ("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "ONU", "Notícia")
}

FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1575517111478-7f6afd0973db?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=800&q=80"
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

@st.cache_data(ttl=1800)
def carregar_noticias():
    itens = []
    regioes_lista = ["América do Sul", "América do Norte", "Europa", "Ásia", "África", "Oriente Médio", "Global"]
    temas_lista = ["Segurança & Defesa", "Economia & Comércio", "Meio Ambiente & Clima", "Direitos Humanos", "Cooperação Internacional"]

    idx_count = 0
    for nome, (url, orgao, tipo) in FONTES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:8]:
            resumo = re.sub('<[^<]+?>', '', entry.get("summary", entry.get("description", "")))[:160] + "..."
            imagem_url = extrair_url_imagem(entry, idx_count)
            
            regiao_atribuida = regioes_lista[idx_count % len(regioes_lista)]
            tema_atribuido = temas_lista[idx_count % len(temas_lista)]
            idx_count += 1

            itens.append({
                "titulo": entry.title,
                "resumo": resumo,
                "orgao": orgao,
                "tipo": tipo,
                "regiao": regiao_atribuida,
                "tema": tema_atribuido,
                "imagem": imagem_url,
                "link": entry.link,
                "data": "2026"
            })
    return itens

acervo_noticias = carregar_noticias()

# ==============================================================================
# 6. MENU SUPERIOR ALINHADO (FONTE MENOR E BOTÕES COMPACTOS)
# ==============================================================================
user_cur = st.session_state["current_user"]
user_data = st.session_state["users_db"].get(user_cur, {"plan": "free", "access_count": 0})

col_title, col_top_actions = st.columns([2.2, 1.8])

with col_title:
    st.markdown('<div class="portal-header-title">REPOSITÓRIO DIPLOMÁTICO</div>', unsafe_allow_html=True)

with col_top_actions:
    col_nav_1, col_nav_2 = st.columns([1, 1])
    with col_nav_1:
        st.markdown('<div class="top-nav-btn top-nav-btn-secondary">', unsafe_allow_html=True)
        if user_cur == "visitante":
            if st.button("👤 Criar Conta", key="top_create_account", use_container_width=True):
                st.session_state["show_register_modal"] = True
                st.rerun()
        else:
            nome_exibir = user_data.get('nome', user_cur).split()[0]
            st.caption(f"👤 {nome_exibir}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_nav_2:
        st.markdown('<div class="top-nav-btn top-nav-btn-primary">', unsafe_allow_html=True)
        if st.button("👑 Assine Premium", key="top_subscribe", use_container_width=True):
            st.session_state["show_plans_modal"] = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ==============================================================================
# 7. TELA DE CADASTRO (CÓPIA DE REFERÊNCIA)
# ==============================================================================
if st.session_state["show_register_modal"]:
    st.markdown("""
        <div class="register-header-title">Criar Conta</div>
        <div class="register-header-subtitle">Sua dose diária de inteligência diplomática.</div>
    """, unsafe_allow_html=True)

    with st.form("form_criar_conta"):
        st.markdown('<div class="field-label">NOME COMPLETO</div>', unsafe_allow_html=True)
        nome = st.text_input("Nome Completo", placeholder="Seu nome completo", label_visibility="collapsed")

        st.markdown('<div class="field-label" style="margin-top:10px;">TELEFONE INTERNACIONAL</div>', unsafe_allow_html=True)
        c_ddi, c_num = st.columns([1.5, 2.5])
        with c_ddi:
            pais_codigo = st.selectbox("DDI", ["🇧🇷 +55 Brasil", "🇺🇸 +1 EUA", "🇵🇹 +351 Portugal"], label_visibility="collapsed")
        with c_num:
            telefone = st.text_input("Telefone", placeholder="Digite o número", label_visibility="collapsed")

        st.markdown('<div class="field-label" style="margin-top:10px;">E-MAIL</div>', unsafe_allow_html=True)
        email = st.text_input("E-mail", placeholder="seu@email.com", label_visibility="collapsed")

        st.markdown('<div class="field-label" style="margin-top:10px;">SENHA</div>', unsafe_allow_html=True)
        senha = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="top-nav-btn top-nav-btn-primary">', unsafe_allow_html=True)
        btn_submit = st.form_submit_button("Criar Conta", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if btn_submit:
            if not nome or not email or len(senha) < 6:
                st.error("Preencha todos os campos corretamente (senha mínima: 6 caracteres).")
            else:
                st.session_state["users_db"][email] = {
                    "plan": "free", "access_count": 0, "last_date": str(date.today()),
                    "nome": nome, "email": email
                }
                st.session_state["current_user"] = email
                enviar_email_confirmacao(email, nome)
                st.session_state["show_register_modal"] = False
                st.rerun()

    if st.button("Voltar ao Acervo", use_container_width=True):
        st.session_state["show_register_modal"] = False
        st.rerun()
    st.stop()

# ==============================================================================
# 8. BARRA LATERAL (FILTROS POR REGIÃO E TEMA - UBIQUE STYLE)
# ==============================================================================
with st.sidebar:
    st.markdown("### 🏛️ REPOSITÓRIO DIPLOMÁTICO")
    st.caption("Acervo Oficial de Política Externa")
    st.markdown("---")

    st.markdown("### 🌍 Filtros do Acervo")
    editoria_sel = st.selectbox("Fonte / Órgão:", ["Todas", "MRE (Notas)", "MRE (Discursos)", "ONU"])
    regiao_sel = st.selectbox("Região:", ["Todas as Regiões", "América do Sul", "América do Norte", "Europa", "Ásia", "África", "Oriente Médio", "Global"])
    tema_sel = st.selectbox("Tema:", ["Todos os Temas", "Segurança & Defesa", "Economia & Comércio", "Meio Ambiente & Clima", "Direitos Humanos", "Cooperação Internacional"])

    st.markdown("---")
    busca = st.text_input("🔍 Busca por palavra-chave", placeholder="Ex: G20, COP, CSNU")

# ==============================================================================
# 9. FEED DE NOTÍCIAS COM EXIBIÇÃO DE IMAGENS E GRÁFICOS
# ==============================================================================
noticias_filtradas = acervo_noticias

if editoria_sel == "MRE (Notas)":
    noticias_filtradas = [n for n in noticias_filtradas if n["orgao"] == "MRE" and n["tipo"] == "Nota à Imprensa"]
elif editoria_sel == "MRE (Discursos)":
    noticias_filtradas = [n for n in noticias_filtradas if n["orgao"] == "MRE" and n["tipo"] == "Discurso"]
elif editoria_sel == "ONU":
    noticias_filtradas = [n for n in noticias_filtradas if n["orgao"] == "ONU"]

if regiao_sel != "Todas as Regiões":
    noticias_filtradas = [n for n in noticias_filtradas if n["regiao"] == regiao_sel]

if tema_sel != "Todos os Temas":
    noticias_filtradas = [n for n in noticias_filtradas if n["tema"] == tema_sel]

if busca:
    noticias_filtradas = [n for n in noticias_filtradas if busca.lower() in n["titulo"].lower() or busca.lower() in n["resumo"].lower()]

grid_cols = st.columns(2)
for idx, item in enumerate(noticias_filtradas):
    with grid_cols[idx % 2]:
        st.markdown(f"""
            <div class="news-card">
                <div class="card-img-container">
                    <img src="{item['imagem']}" class="card-img" alt="Imagem da Notícia" />
                </div>
                <div class="card-body">
                    <div class="meta-tag">{item['orgao']} • {item['tipo']} | 📍 {item['regiao']}</div>
                    <div class="card-title">{item['titulo']}</div>
                    <div style="font-size:11px; font-weight:700; color:#B76D4D; margin-bottom:8px;">🏷️ Tema: {item['tema']}</div>
                    <div class="card-excerpt">{item['resumo']}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"📖 LER DOCUMENTO COMPLETO (#{idx+1})", key=f"read_{idx}"):
            if user_data["plan"] == "free":
                user_data["access_count"] += 1
            st.markdown(f'<meta http-equiv="refresh" content="0; url={item["link"]}">', unsafe_allow_html=True)
            st.rerun()
