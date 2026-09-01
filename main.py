# ==============================================================================
# ESTILO VISUAL EDITORIAL & MINIMALISTA
# ==============================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Cinzel:wght@600;700&display=swap');

    /* Fundo limpo e neutro */
    html, body, [class*="stApp"] {
        background-color: #F8F9FA !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A;
    }

    /* Centralização e Card Editorial */
    .portal-card {
        max-width: 400px;
        margin: 50px auto 10px auto;
        background: #FFFFFF;
        padding: 40px 35px 30px 35px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.04), 0 8px 10px -6px rgba(15, 23, 42, 0.04);
        text-align: center;
    }

    .portal-brand {
        font-family: 'Cinzel', 'Playfair Display', serif;
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 3px;
        color: #0F172A;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .portal-tagline {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 2.5px;
        color: #64748B;
        text-transform: uppercase;
        margin-bottom: 28px;
    }

    /* Ajuste dos Rótulos e Inputs */
    .stTextInput > label {
        font-size: 12px !important;
        font-weight: 600 !important;
        color: #334155 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    .stTextInput > div > div > input {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        color: #0F172A !important;
        font-size: 14px !important;
        padding: 10px 14px !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #0F172A !important;
        box-shadow: 0 0 0 1px #0F172A !important;
    }

    /* Botão Principal em Bloco Escuro Estilo Editorial */
    .stButton > button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 12px !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        padding: 12px 20px !important;
        margin-top: 10px !important;
        transition: background-color 0.2s ease !important;
    }

    .stButton > button:hover {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
    }

    .portal-footer {
        margin-top: 25px;
        padding-top: 18px;
        border-top: 1px solid #F1F5F9;
        font-size: 11px;
        color: #94A3B8;
        display: flex;
        justify-content: space-between;
    }

    .portal-footer a {
        color: #475569;
        text-decoration: none;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)


# ==============================================================================
# MÓDULO DE AUTENTICAÇÃO
# ==============================================================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def autenticar():
    col1, col2, col3 = st.columns([1, 1.8, 1])
    
    with col2:
        st.markdown("""
            <div class="portal-card">
                <div class="portal-brand">REPOSITÓRIO DIPLOMÁTICO</div>
                <div class="portal-tagline">MRE & ONU • ACESSO RESTRITO</div>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_portal_form", clear_on_submit=False):
            username = st.text_input("E-mail / Usuário", placeholder="seu.usuario")
            password = st.text_input("Senha", type="password", placeholder="••••••••••••")
            
            submit_button = st.form_submit_button("ENTRAR NA PLATAFORMA", use_container_width=True)
            
            if submit_button:
                if username == "admin" and password == "diplomacia2026":
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")

        st.markdown("""
            <div class="portal-footer">
                <span>Acesso exclusivo</span>
                <span>Credenciais: <b>admin</b> / <b>diplomacia2026</b></span>
            </div>
        """, unsafe_allow_html=True)

if not st.session_state["authenticated"]:
    autenticar()
    st.stop()
