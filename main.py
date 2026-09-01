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
    page_title="Ubique News | Repositório Diplomático",
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
# 4. ESTILOS CSS PERSONALIZADOS (ESTÉTICA EDITORIAL AOC MEDIA)
# ==============================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&display=swap');

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

    /* Estilo de cabeçalho minimalista editorial */
    .portal-header-container {
        border-bottom: 1px solid #1A1A1A;
        padding-bottom: 16px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }

    @media (max-width: 768px) {
        .portal-title {
            font-size: 24px !important;
        }
        .top-nav-btn button {
            font-size: 9px !important;
            padding: 2px 4px !important;
        }
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
        color: #F0E6D2 !important;
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

    /* Cards estilo Magazine / AOC Media */
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
    .meta-tag {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 10px;
        font-weight: 700;
        color: #555555;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 8px;
    }
    .card-title {
        font-family: 'Newsreader', serif;
        font-size: 20px;
        font-weight: 600;
        color: #1A1A1A;
        line-height: 1.25;
        margin-bottom: 10px;
    }
    .card-excerpt { 
        font-family: 'Plus Jakarta Sans', sans-serif; 
        font-size: 13.5px; 
        color: #666666; 
        line-height: 1.6; 
        margin-bottom: 14px; 
    }

    .register-header-title { font-family: 'Newsreader', serif; font-size: 32px; font-weight: 600; color: #1A1A1A; text-align: center; margin-bottom: 4px; }
    .register-header-subtitle { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 13px; color: #666666; text-align: center; margin-bottom: 24px; }
    .field-label { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 10px; font-weight: 700; color: #1A1A1A; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 6px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. EXTRATOR DE IMAGENS E CARREGAMENTO DE FEED
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

@st.cache_data(ttl=1800)
def carregar_noticias():
    itens = []
    regioes_lista = ["América do Sul", "Europa", "Oriente Médio", "Global"]
    temas_lista = ["Segurança & Defesa", "Economia & Comércio", "Cooperação Internacional"]

    idx_count = 0
    for nome, (url, orgao, tipo) in FONTES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:8]:
            resumo = re.sub('<[^<]+?>', '', entry.get("summary", entry.get("description", "")))[:160] + "..."
            imagem_url = extrair_url_imagem(entry, idx_count)
            
            itens.append({
                "titulo": entry.title,
                "resumo": resumo,
                "orgao": orgao,
                "tipo": tipo,
                "regiao": regioes_lista[idx_count % len(regioes_lista)],
                "tema": temas_lista[idx_count % len(temas_lista)],
                "imagem": imagem_url,
                "link": entry.link,
                "data": "2026"
            })
            idx_count += 1
    return itens

acervo_noticias = carregar_noticias()

# ==============================================================================
# 6. MENU SUPERIOR COM ESTILO EDITORIAL
# ==============================================================================
user_cur = st.session_state["current_user"]
user_data = st.session_state["users_db"].get(user_cur, {"plan": "free", "access_count": 0})

col_title, col_top_actions = st.columns([2.5, 1.5])

with col_title:
    st.markdown("""
        <div class="portal-title" style="font-family: 'Newsreader', serif; font-size: 28px; font-weight: 600; letter-spacing: -0.03em; margin: 0; padding-top: 2px;">
            <span style="color: #1A1A1A;">Ubique</span> <span style="color: #666666; font-style: italic;">News</span>
        </div>
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 11px; color: #777777; text-transform: uppercase; letter-spacing: 0.15em; margin-top: 2px; margin-bottom: 4px;">
            a sua dose diária de informação
        </div>
    """, unsafe_allow_html=True)

with col_top_actions:
    col_nav_1, col_nav_2 = st.columns(2)
    with col_nav_1:
        st.markdown('<div class="top-nav-btn top-nav-btn-secondary">', unsafe_allow_html=True)
        if user_cur == "visitante":
            if st.button("Entrar", key="top_create_account", use_container_width=True):
                st.session_state["show_register_modal"] = True
                st.rerun()
        else:
            nome_exibir = user_data.get('nome', user_cur).split()[0]
            st.caption(f"👤 {nome_exibir}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_nav_2:
        st.markdown('<div class="top-nav-btn top-nav-btn-primary">', unsafe_allow_html=True)
        if st.button("Assinar", key="top_subscribe", use_container_width=True):
            st.session_state["show_plans_modal"] = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr style='border: none; border-top: 1px solid #1A1A1A; margin-top: 10px; margin-bottom: 24px;'>", unsafe_allow_html=True)

# ==============================================================================
# 7. TELA DE CADASTRO E LOGIN
# ==============================================================================
if st.session_state["show_register_modal"]:
    st.markdown("""
        <div class="register-header-title">Ubique News</div>
        <div class="register-header-subtitle">a sua dose diária de informação.</div>
    """, unsafe_allow_html=True)

    with st.form("form_criar_conta"):
        st.markdown('<div class="field-label">NOME COMPLETO</div>', unsafe_allow_html=True)
        nome = st.text_input("Nome Completo", placeholder="Seu nome completo", label_visibility="collapsed")

        st.markdown('<div class="field-label" style="margin-top:12px;">TELEFONE INTERNACIONAL</div>', unsafe_allow_html=True)
        c_ddi, c_num = st.columns([1.5, 2.5])
        with c_ddi:
            pais_codigo = st.selectbox("DDI", ["🇧🇷 +55", "🇺🇸 +1", "🇵🇹 +351"], label_visibility="collapsed")
        with c_num:
            telefone = st.text_input("Telefone", placeholder="Número", label_visibility="collapsed")

        st.markdown('<div class="field-label" style="margin-top:12px;">E-MAIL</div>', unsafe_allow_html=True)
        email = st.text_input("E-mail", placeholder="seu@email.com", label_visibility="collapsed")

        st.markdown('<div class="field-label" style="margin-top:12px;">SENHA</div>', unsafe_allow_html=True)
        senha = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="top-nav-btn top-nav-btn-primary">', unsafe_allow_html=True)
        btn_submit = st.form_submit_button("Criar Conta e Entrar", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if btn_submit:
            if not nome or not email or len(senha) < 6:
                st.error("Preencha todos os campos corretamente.")
            else:
                st.session_state["users_db"][email] = {
                    "plan": "free", "access_count": 0, "last_date": str(date.today()),
                    "nome": nome, "email": email
                }
                st.session_state["current_user"] = email
                enviar_email_confirmacao(email, nome)
                st.session_state["show_register_modal"] = False
                st.rerun()

    if st.button("Voltar à Página Inicial", use_container_width=True):
        st.session_state["show_register_modal"] = False
        st.rerun()
    st.stop()

# ==============================================================================
# 8. BARRA LATERAL (FILTROS)
# ==============================================================================
with st.sidebar:
    st.markdown("### 🏛️ UBIQUE NEWS")
    st.caption("a sua dose diária de informação")
    st.markdown("---")

    st.markdown("### 🌍 Filtros de Geopolítica")
    editoria_sel = st.selectbox("Fonte / Órgão:", ["Todas", "MRE (Notas)", "ONU"])
    regiao_sel = st.selectbox("Região:", ["Todas as Regiões", "América do Sul", "Europa", "Oriente Médio", "Global"])
    tema_sel = st.selectbox("Tema:", ["Todos os Temas", "Segurança & Defesa", "Economia & Comércio", "Cooperação Internacional"])

    st.markdown("---")
    busca = st.text_input("🔍 Busca por palavra-chave", placeholder="Ex: G20, COP, CSNU")

# ==============================================================================
# 9. LÓGICA DE FILTRAGEM
# ==============================================================================
noticias_filtradas = acervo_noticias

if editoria_sel == "MRE (Notas)":
    noticias_filtradas = [n for n in noticias_filtradas if n["orgao"] == "MRE"]
elif editoria_sel == "ONU":
    noticias_filtradas = [n for n in noticias_filtradas if n["orgao"] == "ONU"]

if regiao_sel != "Todas as Regiões":
    noticias_filtradas = [n for n in noticias_filtradas if n["regiao"] == regiao_sel]
if tema_sel != "Todos os Temas":
    noticias_filtradas = [n for n in noticias_filtradas if n["tema"] == tema_sel]
if busca:
    noticias_filtradas = [n for n in noticias_filtradas if busca.lower() in n["titulo"].lower() or busca.lower() in n["resumo"].lower()]

# ==============================================================================
# 10. CARROSSEL DE DESTAQUES & GRADE DE NOTÍCIAS (ESTILO AOC MEDIA)
# ==============================================================================
if len(noticias_filtradas) > 0:
    slides_js = ""
    for item in noticias_filtradas[:4]:
        titulo_limpo = item['titulo'].replace('"', '\\"')
        slides_js += f"""
          {{
            image: "{item['imagem']}",
            tag: "{item['orgao']} • {item['tipo']} | 📍 {item['regiao']}",
            title: "{titulo_limpo}"
          }},
        """

    carousel_html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&family=Newsreader:ital,opsz,wght@0,6..72,600;1,6..72,400&display=swap');
      body {{ margin: 0; background: transparent; font-family: 'Plus Jakarta Sans', sans-serif; }}
      .carousel {{
        position: relative;
        width: 100%;
        height: 400px;
        overflow: hidden;
        border-radius: 4px;
        border: 1px solid #E2DED6;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
      }}
      @media (max-width: 768px) {{
        .carousel {{ height: 280px; }}
        .slide-title {{ font-size: 18px !important; }}
        .content {{ padding: 20px !important; }}
      }}
      .slides {{
        display: flex;
        width: 100%;
        height: 100%;
        transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
      }}
      .slide {{
        min-width: 100%;
        height: 100%;
        background-size: cover;
        background-position: center;
        position: relative;
        display: flex;
        align-items: flex-end;
      }}
      .overlay {{
        position: absolute;
        bottom: 0; left: 0; right: 0; top: 0;
        background: linear-gradient(to top, rgba(26,26,26,0.92) 0%, rgba(26,26,26,0.3) 55%, transparent 100%);
      }}
      .content {{
        position: relative;
        z-index: 2;
        padding: 35px;
        color: #F7F5F0;
        width: 100%;
        box-sizing: border-box;
      }}
      .tag {{
        background-color: #1A1A1A;
        color: #F7F5F0;
        font-size: 10px;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 2px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        display: inline-block;
        margin-bottom: 10px;
        border: 1px solid rgba(255,255,255,0.2);
      }}
      .slide-title {{
        font-family: 'Newsreader', serif;
        font-size: 26px;
        font-weight: 600;
        color: #F7F5F0 !important;
        margin: 0;
        line-height: 1.2;
      }}
      .dots {{
        position: absolute;
        bottom: 16px;
        right: 24px;
        z-index: 10;
        display: flex;
        gap: 6px;
      }}
      .dot {{
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: rgba(247, 245, 240, 0.4);
        cursor: pointer;
        transition: background 0.3s, transform 0.3s;
      }}
      .dot.active {{
        background: #F7F5F0;
        transform: scale(1.3);
      }}
    </style>
    </head>
    <body>
      <div class="carousel">
        <div class="slides" id="slidesContainer"></div>
        <div class="dots" id="dotsContainer"></div>
      </div>

      <script>
        const slidesData = [
          {slides_js}
        ];

        const container = document.getElementById('slidesContainer');
        const dotsContainer = document.getElementById('dotsContainer');
        let currentIndex = 0;
        let intervalId;

        slidesData.forEach((item, index) => {{
          const slide = document.createElement('div');
          slide.className = 'slide';
          slide.style.backgroundImage = `url('${{item.image}}')`;
          slide.innerHTML = `
            <div class="overlay"></div>
            <div class="content">
              <span class="tag">${{item.tag}}</span>
              <div class="slide-title">${{item.title}}</div>
            </div>
          `;
          container.appendChild(slide);

          const dot = document.createElement('div');
          dot.className = 'dot' + (index === 0 ? ' active' : '');
          dot.addEventListener('click', () => {{
            currentIndex = index;
            updateCarousel();
            resetTimer();
          }});
          dotsContainer.appendChild(dot);
        }});

        function updateCarousel() {{
          container.style.transform = `translateX(-${{currentIndex * 100}}%)`;
          const dots = document.querySelectorAll('.dot');
          dots.forEach((dot, idx) => {{
            dot.classList.toggle('active', idx === currentIndex);
          }});
        }}

        function nextSlide() {{
          currentIndex = (currentIndex + 1) % slidesData.length;
          updateCarousel();
        }}

        function startTimer() {{
          intervalId = setInterval(nextSlide, 5000);
        }}

        function resetTimer() {{
          clearInterval(intervalId);
          startTimer();
        }}

        startTimer();
      </script>
    </body>
    </html>
    """
    
    components.html(carousel_html_code, height=415)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Notícias em Destaque & Análises")

    grid_cols = st.columns(2)
    for idx, item in enumerate(noticias_filtradas):
        with grid_cols[idx % 2]:
            st.markdown(f"""
                <div class="news-card">
                    <div class="card-img-container">
                        <img src="{item['imagem']}" class="card-img" alt="Capa" />
                    </div>
                    <div class="card-body">
                        <div class="meta-tag">{item['orgao']} • {item['tipo']} | 📍 {item['regiao']}</div>
                        <div class="card-title">{item['titulo']}</div>
                        <div style="font-family:'Plus Jakarta Sans', sans-serif; font-size:11px; font-weight:600; color:#555555; margin-bottom:8px;">🏷️ Eixo: {item['tema']}</div>
                        <div class="card-excerpt">{item['resumo']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"LER MATÉRIA COMPLETA", key=f"read_grid_{idx}", use_container_width=True):
                if user_data["plan"] == "free":
                    user_data["access_count"] += 1
                st.markdown(f'<meta http-equiv="refresh" content="0; url={item["link"]}">', unsafe_allow_html=True)
                st.rerun()
else:
    st.info("Nenhuma notícia encontrada com os filtros atuais.")
