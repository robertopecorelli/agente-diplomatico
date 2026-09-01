import streamlit as st
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
    page_title="Repositório Diplomático | MRE & ONU",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 3. GERENCIAMENTO DE SESSÃO E BANCO DE DADOS EM MEMÓRIA
# ==============================================================================
if "users_db" not in st.session_state:
    st.session_state["users_db"] = {
        "visitante": {"plan": "free", "access_count": 0, "last_date": str(date.today())}
    }

if "current_user" not in st.session_state:
    st.session_state["current_user"] = "visitante"

if "show_plans_modal" not in st.session_state:
    st.session_state["show_plans_modal"] = False

if "selected_plan_checkout" not in st.session_state:
    st.session_state["selected_plan_checkout"] = "mensal"

if "categoria_ativa" not in st.session_state:
    st.session_state["categoria_ativa"] = "Todas"

# Processar retorno de pagamento com sucesso via Stripe
query_params = st.query_params
if query_params.get("payment") == "success":
    user = st.session_state.get("current_user", "visitante")
    if user in st.session_state["users_db"]:
        st.session_state["users_db"][user]["plan"] = "premium"
    st.toast("🎉 Assinatura Premium confirmada com sucesso! Acesso ilimitado liberado.", icon="✅")

def verificar_reset_diario(username):
    user_data = st.session_state["users_db"].get(username)
    if user_data:
        hoje_str = str(date.today())
        if user_data.get("last_date") != hoje_str:
            user_data["access_count"] = 0
            user_data["last_date"] = hoje_str

verificar_reset_diario(st.session_state["current_user"])

# ==============================================================================
# 4. FUNÇÃO PARA CRIAR SESSÃO DE CHECKOUT STRIPE
# ==============================================================================
def gerar_link_checkout_stripe(plano, email_usuario="cliente@exemplo.com"):
    price_id = STRIPE_PRICE_MONTHLY if plano == "mensal" else STRIPE_PRICE_YEARLY
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=email_usuario if "@" in email_usuario else None,
            payment_method_types=['card', 'boleto'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=f"{DOMAIN_URL}/?payment=success",
            cancel_url=f"{DOMAIN_URL}/?payment=cancel",
        )
        return checkout_session.url
    except Exception as e:
        return f"{DOMAIN_URL}/?payment=success"

# ==============================================================================
# 5. ESTILOS CSS PERSONALIZADOS
# ==============================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Cinzel:wght@600;700;800&display=swap');

    html, body, [class*="stApp"] {
        background-color: #F8F9FA !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A;
    }

    /* Cabeçalho Principal */
    .portal-header-title {
        font-family: 'Cinzel', serif;
        font-size: 28px;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: 2.5px;
        margin: 0;
    }

    /* Banner Promocional da Sidebar */
    .sidebar-premium-banner {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 20px;
        color: #FFFFFF;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    .banner-badge {
        background-color: #D97706;
        color: #FFFFFF;
        font-size: 9px;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .banner-title {
        font-family: 'Playfair Display', serif;
        font-size: 20px;
        font-weight: 700;
        margin: 10px 0 6px 0;
        color: #FFFFFF;
    }

    .banner-subtitle {
        font-size: 12px;
        color: #94A3B8;
        line-height: 1.4;
        margin-bottom: 14px;
    }

    .banner-benefits {
        font-size: 11.5px;
        color: #E2E8F0;
        margin-bottom: 16px;
        padding-left: 0;
        list-style: none;
    }

    .banner-benefits li {
        margin-bottom: 6px;
    }

    /* Modal de Seleção de Planos */
    .plans-modal-container {
        display: flex;
        flex-direction: row;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #334155;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        margin: 10px auto 25px auto;
        max-width: 920px;
    }

    .plans-left-panel {
        background-color: #0F172A;
        color: #F8F9FA;
        padding: 35px;
        flex: 1.1;
    }

    .plans-right-panel {
        background-color: #FFFFFF;
        color: #0F172A;
        padding: 35px;
        flex: 1;
        border-left: 1px solid #E2E8F0;
    }

    .premium-title { font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; margin-bottom: 4px; color: #FFFFFF; }
    .premium-subtitle { font-size: 13px; color: #94A3B8; margin-bottom: 20px; }

    .feature-list { list-style: none; padding: 0; margin: 0 0 25px 0; }
    .feature-item { font-size: 13.5px; font-weight: 600; margin-bottom: 10px; color: #E2E8F0; }

    .plan-card-dark {
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
        background: #1E293B;
        position: relative;
    }

    .plan-card-dark.active { border: 2px solid #D97706; }
    .plan-card-header { font-size: 10px; font-weight: 800; letter-spacing: 1.5px; color: #94A3B8; text-transform: uppercase; }
    .plan-price { font-size: 24px; font-weight: 800; color: #FFFFFF; margin: 2px 0; }
    .plan-price span { font-size: 13px; font-weight: 500; color: #94A3B8; }
    .plan-badge { position: absolute; top: 12px; right: 12px; background: #D97706; color: #FFFFFF; font-size: 8.5px; font-weight: 800; padding: 2px 7px; border-radius: 20px; text-transform: uppercase; }

    /* Botão Dourado Premium */
    .btn-gold button {
        background-color: #D97706 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
    }

    /* Cards de Notícias */
    .news-card { background: #FFFFFF; border-radius: 8px; border: 1px solid #E2E8F0; overflow: hidden; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04); }
    .card-body { padding: 18px; }
    .meta-tag { font-size: 10.5px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
    .card-title { font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 700; color: #0F172A; line-height: 1.35; margin-bottom: 8px; }
    .card-date { font-size: 11px; color: #64748B; margin-bottom: 10px; }
    .card-excerpt { font-size: 13px; color: #334155; line-height: 1.5; margin-bottom: 12px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 6. COMPONENTE MODAL DE ASSINATURA
# ==============================================================================
def render_plans_modal():
    st.markdown("""
        <div class="plans-modal-container">
            <div class="plans-left-panel">
                <div class="premium-title">Seja Premium</div>
                <div class="premium-subtitle">Acesso ilimitado à inteligência diplomática.</div>
                <ul class="feature-list">
                    <li class="feature-item">✓ Notícias e Discursos Ilimitados</li>
                    <li class="feature-item">✓ Filtros de Região, Data e Fontes</li>
                    <li class="feature-item">✓ Análises e acervo histórico exclusivo</li>
                </ul>
                <div class="plan-card-dark active">
                    <div class="plan-card-header">PLANO MENSAL</div>
                    <div class="plan-price">R$ 39,99 <span>/mês</span></div>
                    <div style="font-size: 11px; color: #94A3B8;">Flexibilidade total para acompanhar mês a mês.</div>
                </div>
                <div class="plan-card-dark">
                    <span class="plan-badge">MELHOR VALOR</span>
                    <div class="plan-card-header">PLANO ANUAL</div>
                    <div class="plan-price">R$ 399,90 <span>/ano</span></div>
                    <div style="font-size: 11px; color: #94A3B8;">Acesso prolongado com a melhor condição econômica.</div>
                </div>
            </div>
            <div class="plans-right-panel">
                <div style="font-size: 11px; font-weight: 800; color: #64748B; letter-spacing: 1.5px; margin-bottom: 10px; text-transform: uppercase;">ASSINATURA PREMIUM</div>
                <div style="font-size: 18px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">Selecione a forma de pagamento</div>
                <div style="font-size: 12px; color: #64748B; margin-bottom: 20px;">Você será redirecionado para o checkout seguro do Stripe.</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 7. CARREGAMENTO DO ACERVO DE NOTÍCIAS & DISCURSOS
# ==============================================================================
FONTES = {
    "MRE (Notas à Imprensa)": ("https://www.gov.br/mre/pt-br/centrais-de-conteudo/notas-a-imprensa/RSS", "MRE", "Nota à Imprensa"),
    "MRE (Discursos)": ("https://www.gov.br/mre/pt-br/centrais-de-conteudo/discursos/RSS", "MRE", "Discurso"),
    "ONU (Notícias)": ("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "ONU", "Notícia")
}

@st.cache_data(ttl=1800)
def carregar_noticias():
    itens = []
    for nome, (url, orgao, tipo) in FONTES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:8]:
            resumo = re.sub('<[^<]+?>', '', entry.get("summary", entry.get("description", "")))[:160] + "..."
            itens.append({
                "titulo": entry.title,
                "resumo": resumo,
                "orgao": orgao,
                "tipo": tipo,
                "link": entry.link,
                "data": "2026"
            })
    return itens

acervo_noticias = carregar_noticias()

# ==============================================================================
# 8. MENU SUPERIOR E BARRA LATERAL (ESTRUTURA COMPLETA)
# ==============================================================================
user_cur = st.session_state["current_user"]
user_data = st.session_state["users_db"][user_cur]

# Navbar Superior
col_top_left, col_top_right = st.columns([3, 1])
with col_top_left:
    st.markdown('<div class="portal-header-title">REPOSITÓRIO DIPLOMÁTICO</div>', unsafe_allow_html=True)

with col_top_right:
    st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
    if st.button("👑 SEJA PREMIUM / ASSINAR", use_container_width=True):
        st.session_state["show_plans_modal"] = True
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Barra Lateral (Sidebar)
with st.sidebar:
    st.markdown("### 🏛️ REPOSITÓRIO DIPLOMÁTICO")
    st.caption("Acervo Oficial de Política Externa & Relações Internacionais")
    st.markdown("---")

    # Banner Promocional de Assinatura
    st.markdown("""
        <div class="sidebar-premium-banner">
            <span class="banner-badge">ASSINATURA</span>
            <div class="banner-title">Seja Premium</div>
            <div class="banner-subtitle">Acesso ilimitado à inteligência e análises diplomáticas.</div>
            <ul class="banner-benefits">
                <li>✓ Notícias & Discursos Ilimitados</li>
                <li>✓ Filtros por Região e Data</li>
                <li>✓ Análises Exclusivas</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
    if st.button("ASSINAR POR R$ 39,99/MÊS", key="btn_sidebar_subscribe", use_container_width=True):
        st.session_state["show_plans_modal"] = True
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Contador de Acessos Gratuitos
    if user_data["plan"] == "free":
        acessos = user_data["access_count"]
        pct = min(100, int((acessos / 10) * 100))
        st.markdown(f"**Acessos Gratuitos Hoje:** {acessos} / 10")
        st.progress(pct / 100)
        if acessos >= 10:
            st.warning("Limite diário atingido. Assine o plano Premium para liberar acesso ilimitado.")
        st.markdown("---")

    # Editorias & Navegação
    st.markdown("### 📍 Editorias")
    editoria_sel = st.radio(
        "Filtrar por Fonte:",
        ["Todas", "MRE (Notas)", "MRE (Discursos)", "ONU"],
        index=0
    )

    st.markdown("---")
    st.markdown("### 🔍 Busca no Acervo")
    busca = st.text_input("Palavra-chave", placeholder="Ex: CSNU, Gaza, COP, G20")

# ==============================================================================
# 9. EXIBIÇÃO DO MODAL DE CHECKOUT STRIPE
# ==============================================================================
if st.session_state["show_plans_modal"]:
    render_plans_modal()
    
    col_m1, col_m2, col_m3 = st.columns([1, 1, 1])
    with col_m1:
        if st.button("PAGAR MENSAL (R$ 39,99)", use_container_width=True):
            url_checkout = gerar_link_checkout_stripe("mensal")
            st.markdown(f'<meta http-equiv="refresh" content="0; url={url_checkout}">', unsafe_allow_html=True)
    with col_m2:
        if st.button("PAGAR ANUAL (R$ 399,90)", use_container_width=True):
            url_checkout = gerar_link_checkout_stripe("anual")
            st.markdown(f'<meta http-equiv="refresh" content="0; url={url_checkout}">', unsafe_allow_html=True)
    with col_m3:
        if st.button("FECHAR MODAL", use_container_width=True):
            st.session_state["show_plans_modal"] = False
            st.rerun()
    st.stop()

# Trava de limite de 10 acessos diários
if user_data["plan"] == "free" and user_data["access_count"] >= 10:
    st.error("🔒 Você atingiu o limite de 10 leituras gratuitas hoje. Assine para continuar acompanhando.")
    st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
    if st.button("DESBLOQUEAR ACESSO ILIMITADO AGORA", use_container_width=True):
        st.session_state["show_plans_modal"] = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 10. FEED DE NOTÍCIAS & CONTADOR DE ACESSOS
# ==============================================================================
noticias_filtradas = acervo_noticias

# Aplicação dos Filtros de Editoria da Sidebar
if editoria_sel == "MRE (Notas)":
    noticias_filtradas = [n for n in noticias_filtradas if n["orgao"] == "MRE" and n["tipo"] == "Nota à Imprensa"]
elif editoria_sel == "MRE (Discursos)":
    noticias_filtradas = [n for n in noticias_filtradas if n["orgao"] == "MRE" and n["tipo"] == "Discurso"]
elif editoria_sel == "ONU":
    noticias_filtradas = [n for n in noticias_filtradas if n["orgao"] == "ONU"]

# Aplicação do Filtro de Busca
if busca:
    noticias_filtradas = [n for n in noticias_filtradas if busca.lower() in n["titulo"].lower() or busca.lower() in n["resumo"].lower()]

grid_cols = st.columns(2)
for idx, item in enumerate(noticias_filtradas):
    with grid_cols[idx % 2]:
        st.markdown(f"""
            <div class="news-card">
                <div class="card-body">
                    <div class="meta-tag">{item['orgao']} • {item['tipo']}</div>
                    <div class="card-title">{item['titulo']}</div>
                    <div class="card-date">Ano: {item['data']}</div>
                    <div class="card-excerpt">{item['resumo']}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"📖 LER DOCUMENTO COMPLETO (#{idx+1})", key=f"read_{idx}"):
            if user_data["plan"] == "free":
                user_data["access_count"] += 1
            st.markdown(f'<meta http-equiv="refresh" content="0; url={item["link"]}">', unsafe_allow_html=True)
            st.rerun()
