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

if "selected_plan_checkout" not in st.session_state:
    st.session_state["selected_plan_checkout"] = "mensal"

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

def enviar_email_confirmacao(email_destino, nome_usuario):
    # Simulação do envio de e-mail de confirmação de cadastro
    st.toast(f"📧 E-mail de confirmação enviado com sucesso para: {email_destino}", icon="📩")

# ==============================================================================
# 4. ESTILOS CSS PERSONALIZADOS (PALETA DE CORES SOLICITADA)
# ==============================================================================
# Paleta:
# #F0E6D2 - Fundo geral (creme/pergaminho)
# #262626 - Grafite escuro (textos, títulos e barras de topo)
# #D19A7D - Terracota suave (bordas, realces e detalhes)
# #B76D4D - Terracota intenso (destaques principais, badges e botões)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Cinzel:wght@600;700;800&display=swap');

    html, body, [class*="stApp"] {
        background-color: #F0E6D2 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #262626 !important;
    }

    /* Sidebar Background */
    section[data-testid="stSidebar"] {
        background-color: #E6DC880 !important;
        background: #EAE0CB !important;
        border-right: 1px solid #D19A7D;
    }

    /* Cabeçalho Principal */
    .portal-header-title {
        font-family: 'Cinzel', serif;
        font-size: 28px;
        font-weight: 700;
        color: #262626;
        letter-spacing: 2.5px;
        margin: 0;
    }

    /* Banner Promocional da Sidebar */
    .sidebar-premium-banner {
        background: #262626;
        border: 1px solid #D19A7D;
        border-radius: 10px;
        padding: 20px;
        color: #F0E6D2;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }

    .banner-badge {
        background-color: #B76D4D;
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
        color: #F0E6D2;
    }

    .banner-subtitle {
        font-size: 12px;
        color: #D19A7D;
        line-height: 1.4;
        margin-bottom: 14px;
    }

    .banner-benefits {
        font-size: 11.5px;
        color: #F0E6D2;
        margin-bottom: 16px;
        padding-left: 0;
        list-style: none;
    }

    .banner-benefits li {
        margin-bottom: 6px;
    }

    /* Botão Terracota Intenso */
    .btn-terracota button {
        background-color: #B76D4D !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
        border-radius: 6px !important;
        transition: all 0.3s ease;
    }
    .btn-terracota button:hover {
        background-color: #9E583A !important;
    }

    /* Cards de Notícias */
    .news-card {
        background: #FFFFFF;
        border-radius: 8px;
        border: 1px solid #D19A7D;
        overflow: hidden;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(38, 38, 38, 0.05);
    }
    .card-body { padding: 18px; }
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
        font-size: 18px;
        font-weight: 700;
        color: #262626;
        line-height: 1.35;
        margin-bottom: 8px;
    }
    .card-date { font-size: 11px; color: #736B63; margin-bottom: 10px; }
    .card-excerpt { font-size: 13px; color: #333333; line-height: 1.5; margin-bottom: 12px; }

    /* Estilo da Modal de Cadastro (Replicando layout da imagem) */
    .register-container {
        background-color: #F0E6D2;
        border: 1px solid #D19A7D;
        border-radius: 12px;
        padding: 35px 30px;
        max-width: 520px;
        margin: 0 auto;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }
    .register-header-title {
        font-family: 'Cinzel', serif;
        font-size: 32px;
        font-weight: 700;
        color: #262626;
        text-align: center;
        margin-bottom: 4px;
    }
    .register-header-subtitle {
        font-size: 14px;
        color: #736B63;
        text-align: center;
        margin-bottom: 30px;
    }
    .register-section-title {
        font-size: 16px;
        font-weight: 700;
        color: #262626;
        margin-bottom: 4px;
    }
    .register-section-desc {
        font-size: 12.5px;
        color: #666666;
        margin-bottom: 20px;
    }
    .field-label {
        font-size: 11px;
        font-weight: 800;
        color: #262626;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. CARREGAMENTO E MOCK DE DADOS (COM REGIÕES E TEMAS)
# ==============================================================================
FONTES = {
    "MRE (Notas à Imprensa)": ("https://www.gov.br/mre/pt-br/centrais-de-conteudo/notas-a-imprensa/RSS", "MRE", "Nota à Imprensa"),
    "MRE (Discursos)": ("https://www.gov.br/mre/pt-br/centrais-de-conteudo/discursos/RSS", "MRE", "Discurso"),
    "ONU (Notícias)": ("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "ONU", "Notícia")
}

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
            
            # Atribuição dinâmica para testes dos filtros de Região e Tema
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
                "link": entry.link,
                "data": "2026"
            })
    return itens

acervo_noticias = carregar_noticias()

# ==============================================================================
# 6. TELA / MODAL DE CADASTRO (CÓPIA DA IMAGEM DE REFERÊNCIA)
# ==============================================================================
def render_registro():
    st.markdown("""
        <div class="register-header-title">Criar Conta</div>
        <div class="register-header-subtitle">Sua dose diária de inteligência.</div>
        <div class="register-section-title">Dados do cadastro</div>
        <div class="register-section-desc">Preencha suas informações básicas para criar sua conta no Repositório Diplomático.</div>
    """, unsafe_allow_html=True)

    with st.form("form_criar_conta", clear_on_submit=False):
        st.markdown('<div class="field-label">NOME COMPLETO</div>', unsafe_allow_html=True)
        nome = st.text_input("Nome Completo", placeholder="Seu nome completo", label_visibility="collapsed")

        st.markdown('<div class="field-label" style="margin-top:12px;">TELEFONE INTERNACIONAL</div>', unsafe_allow_html=True)
        col_ddi, col_num = st.columns([1.5, 2.5])
        with col_ddi:
            pais_codigo = st.selectbox("Código", ["🇧🇷 +55 Brasil", "🇺🇸 +1 EUA", "🇵🇹 +351 Portugal", "🇦🇷 +54 Argentina"], label_visibility="collapsed")
        with col_num:
            telefone = st.text_input("Telefone", placeholder="Digite o número", label_visibility="collapsed")
        
        st.caption("Selecione o país e digite o telefone local. O sistema salva o número já com o código internacional.")

        st.markdown('<div class="field-label" style="margin-top:12px;">E-MAIL</div>', unsafe_allow_html=True)
        email = st.text_input("E-mail", placeholder="seu@email.com", label_visibility="collapsed")

        st.markdown('<div class="field-label" style="margin-top:12px;">SENHA</div>', unsafe_allow_html=True)
        senha = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="btn-terracota">', unsafe_allow_html=True)
        btn_submit = st.form_submit_button("Criar Conta", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if btn_submit:
            if not nome or not email or not senha:
                st.error("Por favor, preencha todos os campos obrigatórios.")
            elif len(senha) < 6:
                st.warning("A senha deve conter no mínimo 6 caracteres.")
            else:
                # Registra usuário na sessão
                st.session_state["users_db"][email] = {
                    "plan": "free",
                    "access_count": 0,
                    "last_date": str(date.today()),
                    "nome": nome,
                    "telefone": f"{pais_codigo} {telefone}",
                    "email": email
                }
                st.session_state["current_user"] = email
                enviar_email_confirmacao(email, nome)
                st.success("Conta criada com sucesso! Verifique seu e-mail para confirmação.")
                st.session_state["show_register_modal"] = False
                st.rerun()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Já tem uma conta? Fazer Login", use_container_width=True):
            st.session_state["show_register_modal"] = False
            st.session_state["show_login_modal"] = True
            st.rerun()
    with col_b:
        if st.button("Continuar na versão gratuita", use_container_width=True):
            st.session_state["show_register_modal"] = False
            st.rerun()

# ==============================================================================
# 7. MENU SUPERIOR E BARRA LATERAL
# ==============================================================================
user_cur = st.session_state["current_user"]
user_data = st.session_state["users_db"].get(user_cur, {"plan": "free", "access_count": 0})

# Navbar Superior
col_top_left, col_top_mid, col_top_right = st.columns([2.5, 1, 1])
with col_top_left:
    st.markdown('<div class="portal-header-title">REPOSITÓRIO DIPLOMÁTICO</div>', unsafe_allow_html=True)

with col_top_mid:
    if user_cur == "visitante":
        if st.button("👤 Criar Conta / Entrar", use_container_width=True):
            st.session_state["show_register_modal"] = True
            st.rerun()
    else:
        st.write(f"Olá, **{user_data.get('nome', user_cur)}**")

with col_top_right:
    st.markdown('<div class="btn-terracota">', unsafe_allow_html=True)
    if st.button("👑 SEJA PREMIUM", use_container_width=True):
        st.session_state["show_plans_modal"] = True
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Exibição Condicional do Modal de Cadastro
if st.session_state["show_register_modal"]:
    render_registro()
    st.stop()

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
                <li>✓ Filtros por Região e Tema</li>
                <li>✓ Análises Exclusivas</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="btn-terracota">', unsafe_allow_html=True)
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

    # NOVOS FILTROS SOLICITADOS: REGIÕES E TEMAS (UBIQUE NEWS PATTERN)
    st.markdown("### 🌐 Filtros do Acervo")
    
    editoria_sel = st.selectbox(
        "Fonte / Órgão:",
        ["Todas", "MRE (Notas)", "MRE (Discursos)", "ONU"]
    )

    regiao_sel = st.selectbox(
        "Filtrar por Região:",
        ["Todas as Regiões", "América do Sul", "América do Norte", "Europa", "Ásia", "África", "Oriente Médio", "Global"]
    )

    tema_sel = st.selectbox(
        "Filtrar por Tema:",
        ["Todos os Temas", "Segurança & Defesa", "Economia & Comércio", "Meio Ambiente & Clima", "Direitos Humanos", "Cooperação Internacional"]
    )

    st.markdown("---")
    st.markdown("### 🔍 Busca")
    busca = st.text_input("Palavra-chave", placeholder="Ex: CSNU, Gaza, COP, G20")

# ==============================================================================
# 8. FEED DE NOTÍCIAS COM FILTROS APLICADOS
# ==============================================================================
noticias_filtradas = acervo_noticias

# Filtro de Fonte
if editoria_sel == "MRE (Notas)":
    noticias_filtradas = [n for n in noticias_filtradas if n["orgao"] == "MRE" and n["tipo"] == "Nota à Imprensa"]
elif editoria_sel == "MRE (Discursos)":
    noticias_filtradas = [n for n in noticias_filtradas if n["orgao"] == "MRE" and n["tipo"] == "Discurso"]
elif editoria_sel == "ONU":
    noticias_filtradas = [n for n in noticias_filtradas if n["orgao"] == "ONU"]

# Filtro de Região
if regiao_sel != "Todas as Regiões":
    noticias_filtradas = [n for n in noticias_filtradas if n["regiao"] == regiao_sel]

# Filtro de Tema
if tema_sel != "Todos os Temas":
    noticias_filtradas = [n for n in noticias_filtradas if n["tema"] == tema_sel]

# Filtro de Busca por Palavra-Chave
if busca:
    noticias_filtradas = [n for n in noticias_filtradas if busca.lower() in n["titulo"].lower() or busca.lower() in n["resumo"].lower()]

grid_cols = st.columns(2)
for idx, item in enumerate(noticias_filtradas):
    with grid_cols[idx % 2]:
        st.markdown(f"""
            <div class="news-card">
                <div class="card-body">
                    <div class="meta-tag">{item['orgao']} • {item['tipo']} | 🌍 {item['regiao']}</div>
                    <div class="card-title">{item['titulo']}</div>
                    <div style="font-size:11px; font-weight:700; color:#262626; margin-bottom:6px;">🏷️ Tema: {item['tema']}</div>
                    <div class="card-excerpt">{item['resumo']}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"📖 LER DOCUMENTO COMPLETO (#{idx+1})", key=f"read_{idx}"):
            if user_data["plan"] == "free":
                user_data["access_count"] += 1
            st.markdown(f'<meta http-equiv="refresh" content="0; url={item["link"]}">', unsafe_allow_html=True)
            st.rerun()
