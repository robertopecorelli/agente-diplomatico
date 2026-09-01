import streamlit as st
import feedparser
from datetime import datetime, date
import re

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Repositório Diplomático | MRE & ONU",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. BANCO DE DADOS EM MEMÓRIA & ESTADOS DA SESSÃO
# ==============================================================================
# Estrutura do banco: {username: {"password": pwd, "plan": "free"/"premium", "access_count": 0, "last_date": "YYYY-MM-DD"}}
if "users_db" not in st.session_state:
    st.session_state["users_db"] = {
        "admin": {"password": "diplomacia2026", "plan": "premium", "access_count": 0, "last_date": str(date.today())},
        "leitor.gratis": {"password": "123", "plan": "free", "access_count": 3, "last_date": str(date.today())}
    }

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "current_user" not in st.session_state:
    st.session_state["current_user"] = None

if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"

if "show_plans_modal" not in st.session_state:
    st.session_state["show_plans_modal"] = False

if "selected_plan_checkout" not in st.session_state:
    st.session_state["selected_plan_checkout"] = "Premium Mensal (R$ 39,99/mês)"

# Reset diário do contador de acessos
def verificar_reset_diario(username):
    user_data = st.session_state["users_db"].get(username)
    if user_data:
        hoje_str = str(date.today())
        if user_data.get("last_date") != hoje_str:
            user_data["access_count"] = 0
            user_data["last_date"] = hoje_str

# ==============================================================================
# 3. ESTILOS CSS (PLANO PREMIUM, SIDEBAR E FEED)
# ==============================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Cinzel:wght@600;700;800&display=swap');

    html, body, [class*="stApp"] {
        background-color: #F8F9FA !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A;
    }

    /* Modal / Card de Preços Dividido (Réplica da Referência) */
    .plans-modal-container {
        display: flex;
        flex-direction: row;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #334155;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
        margin: 20px auto;
        max-width: 900px;
    }

    .plans-left-panel {
        background-color: #0F172A;
        color: #F8F9FA;
        padding: 40px;
        flex: 1.1;
    }

    .plans-right-panel {
        background-color: #FFFFFF;
        color: #0F172A;
        padding: 40px;
        flex: 1;
        border-left: 1px solid #E2E8F0;
    }

    .premium-title {
        font-family: 'Playfair Display', serif;
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 4px;
        color: #FFFFFF;
    }

    .premium-subtitle {
        font-size: 13px;
        color: #94A3B8;
        margin-bottom: 25px;
    }

    .feature-list {
        list-style: none;
        padding: 0;
        margin: 0 0 30px 0;
    }

    .feature-item {
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 10px;
        color: #E2E8F0;
    }

    .plan-card-dark {
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 15px;
        background: #1E293B;
        position: relative;
    }

    .plan-card-dark.active {
        border: 2px solid #D97706;
    }

    .plan-card-header {
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1.5px;
        color: #94A3B8;
        text-transform: uppercase;
    }

    .plan-price {
        font-size: 26px;
        font-weight: 800;
        color: #FFFFFF;
        margin: 4px 0;
    }

    .plan-price span {
        font-size: 14px;
        font-weight: 500;
        color: #94A3B8;
    }

    .plan-badge {
        position: absolute;
        top: 14px;
        right: 14px;
        background: #D97706;
        color: #FFFFFF;
        font-size: 9px;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .plan-desc {
        font-size: 11.5px;
        color: #94A3B8;
        line-height: 1.4;
    }

    .right-header {
        font-size: 20px;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 8px;
    }

    .right-sub {
        font-size: 12px;
        color: #64748B;
        line-height: 1.5;
        margin-bottom: 25px;
    }

    .selected-box {
        background-color: #F1F5F9;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 20px;
    }

    .selected-label {
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 1px;
        color: #64748B;
        text-transform: uppercase;
    }

    .selected-val {
        font-size: 15px;
        font-weight: 700;
        color: #0F172A;
    }

    /* Botão Dourado Premium */
    .btn-gold button {
        background-color: #D97706 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
    }

    /* Meter Diário na Sidebar */
    .usage-box {
        background-color: #F1F5F9;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 15px;
        border: 1px solid #E2E8F0;
    }

    .usage-title {
        font-size: 11px;
        font-weight: 700;
        color: #334155;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: flex;
        justify-content: space-between;
    }

    .usage-bar {
        height: 6px;
        background-color: #CBD5E1;
        border-radius: 3px;
        margin-top: 8px;
        overflow: hidden;
    }

    .usage-fill {
        height: 100%;
        background-color: #0F172A;
    }

    /* CSS de Topo e Feed */
    .top-bar {
        background-color: #0F172A;
        color: #F8F9FA;
        padding: 8px 20px;
        font-size: 11px;
        font-weight: 600;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #CBD5E1;
        margin-bottom: 20px;
        border-radius: 4px;
    }

    .portal-header {
        text-align: center;
        padding: 10px 0 20px 0;
        border-bottom: 1px solid #E2E8F0;
        margin-bottom: 25px;
    }

    .portal-header-title {
        font-family: 'Cinzel', serif;
        font-size: 32px;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: 4px;
        margin: 0;
    }

    .news-card {
        background: #FFFFFF;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        overflow: hidden;
        margin-bottom: 24px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }

    .card-body { padding: 20px; }
    .meta-tag { font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
    .card-title { font-family: 'Playfair Display', serif; font-size: 19px; font-weight: 700; color: #0F172A; line-height: 1.35; margin-bottom: 10px; }
    .card-date { font-size: 11px; color: #64748B; margin-bottom: 12px; }
    .card-excerpt { font-size: 13.5px; color: #334155; line-height: 1.55; margin-bottom: 14px; }
    
    .stImage img { max-height: 220px; object-fit: cover; width: 100%; border-bottom: 1px solid #E2E8F0; }
    .lang-link { display: block; text-align: center; background-color: #F8F9FA; padding: 5px; border-radius: 4px; font-size: 10.5px; font-weight: 700; color: #0F172A; text-decoration: none; border: 1px solid #CBD5E1; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. MÓDULO DE AUTENTICAÇÃO E TELA DE SELEÇÃO DE PLANOS
# ==============================================================================
def render_plans_modal(is_embedded=False):
    st.markdown("""
        <div class="plans-modal-container">
            <div class="plans-left-panel">
                <div class="premium-title">Seja Premium</div>
                <div class="premium-subtitle">Acesso ilimitado à inteligência.</div>
                <ul class="feature-list">
                    <li class="feature-item">✓ Notícias Ilimitadas</li>
                    <li class="feature-item">✓ Filtros de Região e Data</li>
                    <li class="feature-item">✓ Análises e recursos exclusivos</li>
                </ul>
                <div class="plan-card-dark active">
                    <div class="plan-card-header">PLANO MENSAL</div>
                    <div class="plan-price">R$ 39,99 <span>/mês</span></div>
                    <div class="plan-desc">Flexibilidade total para acompanhar a cobertura premium mês a mês.</div>
                </div>
                <div class="plan-card-dark">
                    <span class="plan-badge">MELHOR VALOR</span>
                    <div class="plan-card-header">PLANO ANUAL</div>
                    <div class="plan-price">R$ 399,90 <span>/ano</span></div>
                    <div class="plan-desc">Acesso prolongado com condição mais vantajosa para quem quer acompanhar o ano inteiro.</div>
                </div>
            </div>
            <div class="plans-right-panel">
                <div style="font-size: 11px; font-weight: 800; color: #64748B; letter-spacing: 1.5px; margin-bottom: 15px; text-transform: uppercase;">ASSINATURA PREMIUM</div>
                <div class="right-header">Crie sua conta primeiro</div>
                <div class="right-sub">Você pode criar sua conta agora ou seguir direto para o checkout do plano selecionado.</div>
                <div class="selected-box">
                    <div class="selected-label">PLANO SELECIONADO</div>
                    <div class="selected-val">Premium Mensal</div>
                    <div style="font-size: 12px; color: #64748B;">R$ 39,99 por mês</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def autenticar():
    col1, col2, col3 = st.columns([0.2, 2.6, 0.2])
    with col2:
        if st.session_state["auth_mode"] == "plans":
            render_plans_modal()
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                if st.button("CRIAR CONTA GRÁTIS (10 ACESSOS/DIA)", use_container_width=True):
                    st.session_state["auth_mode"] = "signup_free"
                    st.rerun()
            with p_col2:
                st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
                if st.button("ASSINAR PLANO SELECIONADO (R$ 39,99)", use_container_width=True):
                    st.session_state["auth_mode"] = "signup_premium"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state["auth_mode"] in ["signup_free", "signup_premium"]:
            plan_type = "free" if st.session_state["auth_mode"] == "signup_free" else "premium"
            st.markdown(f"### Criar Conta ({'Grátis' if plan_type == 'free' else 'Premium'})")
            with st.form("form_signup_plan"):
                new_user = st.text_input("Usuário / E-mail").strip()
                new_pass = st.text_input("Senha", type="password")
                submit = st.form_submit_button("CONCLUIR CADASTRO")
                if submit:
                    if new_user and new_pass:
                        st.session_state["users_db"][new_user] = {
                            "password": new_pass,
                            "plan": plan_type,
                            "access_count": 0,
                            "last_date": str(date.today())
                        }
                        st.session_state["authenticated"] = True
                        st.session_state["current_user"] = new_user
                        st.session_state["auth_mode"] = "login"
                        st.rerun()
                    else:
                        st.error("Preencha todos os campos.")
            if st.button("Voltar aos Planos"):
                st.session_state["auth_mode"] = "plans"
                st.rerun()

        else:
            st.markdown("### Acesso ao Portal")
            with st.form("form_login"):
                u_input = st.text_input("Usuário").strip()
                p_input = st.text_input("Senha", type="password")
                sub = st.form_submit_button("ENTRAR")
                if sub:
                    if u_input in st.session_state["users_db"] and st.session_state["users_db"][u_input]["password"] == p_input:
                        st.session_state["authenticated"] = True
                        st.session_state["current_user"] = u_input
                        verificar_reset_diario(u_input)
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("VER PLANOS & ASSINATURA", use_container_width=True):
                    st.session_state["auth_mode"] = "plans"
                    st.rerun()

if not st.session_state["authenticated"]:
    autenticar()
    st.stop()

# ==============================================================================
# 5. CARREGAMENTO E DADOS DE NOTÍCIAS
# ==============================================================================
FONTES = {
    "MRE (Notas à Imprensa)": ("https://www.gov.br/mre/pt-br/centrais-de-conteudo/notas-a-imprensa/RSS", "MRE", "Nota à Imprensa"),
    "MRE (Discursos Oficiais)": ("https://www.gov.br/mre/pt-br/centrais-de-conteudo/discursos/RSS", "MRE", "Discurso"),
    "ONU (Notícias Globais)": ("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "ONU", "Notícia"),
    "ONU (Declarações & Discursos)": ("https://news.un.org/feed/subscribe/en/news/topic/statements/feed.rss", "ONU", "Statement")
}

BASE_HISTORICA = [
    {
        "titulo": "Discurso do Brasil na Abertura da Conferência das Nações Unidas sobre Meio Ambiente (Rio-92)",
        "resumo": "Discurso histórico marcando a consolidação do conceito de Desenvolvimento Sustentável e a liderança diplomática brasileira na Eco-92.",
        "orgao": "MRE", "tipo": "Discurso", "fonte_nome": "Arquivo Histórico Itamaraty",
        "data_fmt": "03/06/1992", "ano": "1992", "imagem": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Rio_de_Janeiro_Earth_Summit_1992.jpg/800px-Rio_de_Janeiro_Earth_Summit_1992.jpg",
        "tema": "Meio Ambiente & Clima", "regiao": "América do Sul",
        "links": {"pt": "https://www.gov.br/mre/pt-br", "en": "https://www.gov.br/mre/en", "es": "https://www.gov.br/mre/es", "fr": "https://www.gov.br/mre/fr"}
    },
    {
        "titulo": "Resolução 678 do Conselho de Segurança da ONU sobre a Crise no Golfo Pérsico",
        "resumo": "Decisão histórica do Conselho de Segurança da ONU autorizando o uso de todos os meios necessários para restaurar a paz e segurança.",
        "orgao": "ONU", "tipo": "Statement", "fonte_nome": "UN Digital Library",
        "data_fmt": "29/11/1990", "ano": "1990", "imagem": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/UN_Security_Council_Chamber_2014.jpg/800px-UN_Security_Council_Chamber_2014.jpg",
        "tema": "Conselho de Segurança da ONU", "regiao": "Oriente Médio / Europa",
        "links": {"pt": "https://digitallibrary.un.org", "en": "https://digitallibrary.un.org", "es": "https://digitallibrary.un.org", "fr": "https://digitallibrary.un.org"}
    }
]

def classificar_conteudo(texto):
    texto_lc = texto.lower()
    if any(k in texto_lc for k in ["conselho de segurança", "csnu", "security council"]):
        tema = "Conselho de Segurança da ONU"
    elif any(k in texto_lc for k in ["brasil", "itamaraty", "mercosul"]):
        tema = "Política Externa Brasileira"
    elif any(k in texto_lc for k in ["clima", "meio ambiente", "cop", "amazônia"]):
        tema = "Meio Ambiente & Clima"
    else:
        tema = "Governança Global"

    if any(k in texto_lc for k in ["brasil", "américa do sul", "mercosul"]):
        regiao = "América do Sul"
    elif any(k in texto_lc for k in ["oriente médio", "gaza", "europa", "ucrânia"]):
        regiao = "Oriente Médio / Europa"
    else:
        regiao = "Global"

    return tema, regiao

@st.cache_data(ttl=1800)
def carregar_acervo_completo():
    todos = list(BASE_HISTORICA)
    for nome, (url, orgao, tipo) in FONTES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            resumo = re.sub('<[^<]+?>', '', entry.get("summary", entry.get("description", "")))[:170] + "..."
            tema, regiao = classificar_conteudo(entry.title + " " + resumo)
            todos.append({
                "titulo": entry.title, "resumo": resumo, "orgao": orgao, "tipo": tipo,
                "fonte_nome": nome, "data_fmt": "2026", "ano": "2026",
                "imagem": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/UN_Security_Council_Chamber_2014.jpg/800px-UN_Security_Council_Chamber_2014.jpg",
                "tema": tema, "regiao": regiao,
                "links": {"pt": entry.link, "en": entry.link, "es": entry.link, "fr": entry.link}
            })
    return todos

acervo = carregar_acervo_completo()

# ==============================================================================
# 6. MENU LATERAL E MEDIDOR DE LIMITE DE ACESSO
# ==============================================================================
usr_id = st.session_state["current_user"]
verificar_reset_diario(usr_id)
usr_data = st.session_state["users_db"][usr_id]

with st.sidebar:
    st.markdown(f"### 👤 {usr_id}")
    st.caption(f"Plano: **{usr_data['plan'].upper()}**")
    
    if usr_data["plan"] == "free":
        usados = usr_data["access_count"]
        pct = min(100, int((usados / 10) * 100))
        st.markdown(f"""
            <div class="usage-box">
                <div class="usage-title">
                    <span>Acessos Diários</span>
                    <span><b>{usados} / 10</b></span>
                </div>
                <div class="usage-bar">
                    <div class="usage-fill" style="width: {pct}%;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        if st.button("SEJA PREMIUM (ILIMITADO)", use_container_width=True):
            st.session_state["show_plans_modal"] = True
        st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("SAIR DA CONTA", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

    st.markdown("---")
    st.markdown("### 📍 Editorias & Filtros")
    busca = st.text_input("Palavra-chave", placeholder="Ex: CSNU, Gaza, COP")
    filtro_regiao = st.selectbox("Região Geográfica", ["Todas as Regiões", "América do Sul", "Oriente Médio / Europa", "Global"])
    filtro_tema = st.selectbox("Eixo Temático", ["Todos os Temas", "Conselho de Segurança da ONU", "Política Externa Brasileira", "Meio Ambiente & Clima", "Governança Global"])
    filtro_orgao = st.multiselect("Órgão / Fonte", ["MRE", "ONU"], default=["MRE", "ONU"])

# ==============================================================================
# 7. LOGICA DE EXIBIÇÃO E TRAVA DE PAYWALL (10 ACESSOS)
# ==============================================================================
st.markdown(f"""
    <div class="top-bar">
        <div>📅 {datetime.now().strftime('%A, %d de %B de %Y')}</div>
        <div>SESSÃO: {usr_id.upper()} ({usr_data['plan'].upper()})</div>
    </div>
    <div class="portal-header">
        <h1 class="portal-header-title">REPOSITÓRIO DIPLOMÁTICO</h1>
    </div>
""", unsafe_allow_html=True)

# Exibe modal de troca de plano se acionado pelo botão da sidebar
if st.session_state["show_plans_modal"]:
    render_plans_modal()
    if st.button("Fechar Modal de Planos"):
        st.session_state["show_plans_modal"] = False
        st.rerun()
    st.stop()

# Trava do Paywall se limite excedido
if usr_data["plan"] == "free" and usr_data["access_count"] >= 10:
    st.error("🔒 Você atingiu o limite de 10 acessos diários para contas gratuitas.")
    render_plans_modal()
    st.stop()

# Filtragem de Itens
itens = [i for i in acervo if i["orgao"] in filtro_orgao]
if busca: itens = [i for i in itens if busca.lower() in i["titulo"].lower() or busca.lower() in i["resumo"].lower()]
if filtro_regiao != "Todas as Regiões": itens = [i for i in itens if i["regiao"] == filtro_regiao]
if filtro_tema != "Todos os Temas": itens = [i for i in itens if i["tema"] == filtro_tema]

# Exibição do Feed
cols = st.columns(2)
for idx, item in enumerate(itens):
    with cols[idx % 2]:
        st.markdown('<div class="news-card">', unsafe_allow_html=True)
        if item["imagem"]: st.image(item["imagem"], use_container_width=True)
        st.markdown(f"""
            <div class="card-body">
                <div class="meta-tag">{item['orgao']} • {item['tipo']}</div>
                <div class="card-title">{item['titulo']}</div>
                <div class="card-date">Data: {item['data_fmt']} | Região: {item['regiao']}</div>
                <div class="card-excerpt">{item['resumo']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Registrar o acesso ao clicar no documento oficial
        l_cols = st.columns(4)
        for l_idx, (lang, link_url) in enumerate(item["links"].items()):
            with l_cols[l_idx]:
                if st.button(f"[{lang.upper()}]", key=f"btn_{idx}_{lang}"):
                    if usr_data["plan"] == "free":
                        usr_data["access_count"] += 1
                    st.markdown(f'<meta http-equiv="refresh" content="0; url={link_url}">', unsafe_allow_html=True)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
