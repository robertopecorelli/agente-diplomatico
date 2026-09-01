import streamlit as st
import feedparser
import requests

# Configuração da página para um layout limpo e moderno
st.set_page_config(
    page_title="Boletim Diplomático | MRE & ONU",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilização CSS minimalista
st.markdown("""
    <style>
    .main {
        background-color: #fafafa;
    }
    h1 {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-weight: 600;
        letter-spacing: -0.5px;
        color: #111827;
    }
    .subtitle {
        font-size: 13px;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 30px;
    }
    .card {
        background: #ffffff;
        padding: 24px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .item-title {
        font-size: 17px;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 6px;
    }
    .item-date {
        font-size: 12px;
        color: #9ca3af;
        margin-bottom: 14px;
    }
    .lang-box {
        background: #f9fafb;
        border-left: 3px solid #d1d5db;
        padding: 10px 14px;
        margin-top: 10px;
        border-radius: 0 6px 6px 0;
    }
    .lang-label {
        font-size: 11px;
        font-weight: 700;
        color: #4b5563;
        text-transform: uppercase;
    }
    .lang-text {
        font-size: 13px;
        color: #4b5563;
        margin: 4px 0 8px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Fontes oficiais monitoradas (ONU dividida em Notícias e Discursos)
FONTES = {
    "MRE (Notícias e Notas)": "https://www.gov.br/mre/pt-br/centrais-de-conteudo/noticias/RSS",
    "MRE (Discursos)": "https://www.gov.br/mre/pt-br/centrais-de-conteudo/discursos/RSS",
    "ONU (Notícias)": "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
    "ONU (Discursos / Statements)": "https://news.un.org/feed/subscribe/en/news/topic/statements/feed.rss"
}

@st.cache_data(ttl=3600)
def carregar_dados():
    relatorio_geral = {}
    for nome_fonte, url_rss in FONTES.items():
        feed = feedparser.parse(url_rss)
        itens_fonte = []
        for entry in feed.entries[:5]: # Traz os 5 mais recentes por fonte
            resumo = entry.get("summary", "Resumo não disponível.")
            link_base = entry.link
            
            idiomas = ["pt", "en", "es", "fr"]
            dados_idiomas = {}
            idioma_atual = next((l for l in idiomas if f"/{l}/" in link_base), "en")
            
            for lang in idiomas:
                url_candidata = link_base.replace(f"/{idioma_atual}/", f"/{lang}/")
                dados_idiomas[lang] = {
                    "link": url_candidata, 
                    "resumo": resumo if lang == idioma_atual else "Disponível no link oficial correspondente."
                }
                
            itens_fonte.append({
                "titulo": entry.title,
                "data": entry.get("published", "Data recente"),
                "versoes": dados_idiomas
            })
        relatorio_geral[nome_fonte] = itens_fonte
    return relatorio_geral

# Título do Dashboard
st.markdown("<h1>Boletim Diplomático On-line</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Monitoramento em tempo real • MRE & ONU</div>", unsafe_allow_html=True)

with st.spinner("Buscando atualizações dos portais oficiais..."):
    dados = carregar_dados()

# Abas limpas para navegação (agora com MRE Notas, MRE Discursos, ONU Notícias e ONU Discursos)
abas = st.tabs(list(FONTES.keys()))

for i, (nome_fonte, itens) in enumerate(dados.items()):
    with abas[i]:
        st.markdown("<br>", unsafe_allow_html=True)
        if not itens:
            st.info("Nenhum registro encontrado no momento.")
        for item in itens:
            st.markdown(f"""
                <div class="card">
                    <div class="item-title">{item['titulo']}</div>
                    <div class="item-date">📅 {item['data']}</div>
            """, unsafe_allow_html=True)
            
            cols = st.columns(len(item['versoes']))
            for idx, (lang, info) in enumerate(item['versoes'].items()):
                with cols[idx]:
                    st.markdown(f"""
                        <div class="lang-box">
                            <div class="lang-label">[{lang.upper()}]</div>
                            <div class="lang-text">{info['resumo'][:100]}...</div>
                            <a href="{info['link']}" target="_blank" style="font-size: 11px; color: #2563eb; text-decoration: none;">Acessar &rarr;</a>
                        </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

# Rodapé minimalista
st.markdown("<br><hr style='border:0; border-top:1px solid #e5e7eb;'><p style='text-align: center; color: #9ca3af; font-size: 11px;'>Atualizado via Agente Diplomático Automatizado</p>", unsafe_allow_html=True)
