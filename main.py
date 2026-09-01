import streamlit as st
import feedparser
from datetime import datetime
import re

# Configuração da página
st.set_page_config(
    page_title="Boletim Diplomático | MRE & ONU",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilização CSS Moderna, Minimalista e Polida
st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
    }
    h1 {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-weight: 700;
        letter-spacing: -0.8px;
        color: #0f172a;
    }
    .subtitle {
        font-size: 12px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 35px;
        font-weight: 600;
    }
    .periodo-header {
        font-size: 14px;
        font-weight: 700;
        color: #334155;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 6px;
        margin-top: 40px;
        margin-bottom: 20px;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }
    .card {
        background: #ffffff;
        padding: 0px;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.01);
        overflow: hidden;
        transition: transform 0.2s ease;
    }
    .card-content {
        padding: 24px;
    }
    .item-title {
        font-size: 18px;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 8px;
        line-height: 1.4;
    }
    .item-date {
        font-size: 12px;
        color: #94a3b8;
        margin-bottom: 16px;
        font-weight: 500;
    }
    .lang-container {
        display: flex;
        gap: 8px;
        margin-top: 16px;
    }
    .lang-box {
        background: #f1f5f9;
        border-left: 3px solid #cbd5e1;
        padding: 10px 12px;
        border-radius: 0 8px 8px 0;
        flex: 1;
    }
    .lang-label {
        font-size: 10px;
        font-weight: 800;
        color: #475569;
        letter-spacing: 0.5px;
    }
    .lang-text {
        font-size: 12px;
        color: #475569;
        margin: 4px 0 8px 0;
        line-height: 1.3;
    }
    .stImage img {
        border-top-left-radius: 14px;
        border-top-right-radius: 14px;
        max-height: 280px;
        object-fit: cover;
    }
    </style>
""", unsafe_allow_html=True)

# Fontes oficiais monitoradas
FONTES = {
    "MRE (Notícias e Notas)": "https://www.gov.br/mre/pt-br/centrais-de-conteudo/notas-a-imprensa/RSS",
    "MRE (Discursos)": "https://www.gov.br/mre/pt-br/centrais-de-conteudo/discursos/RSS",
    "ONU (Notícias)": "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
    "ONU (Discursos / Statements)": "https://news.un.org/feed/subscribe/en/news/topic/statements/feed.rss"
}

def extrair_imagem(entry):
    """Varre os campos do feed (summary, content, media_content) para encontrar uma URL de imagem válida."""
    # 1. Tenta via media_content (muito comum em feeds modernos)
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if 'url' in media:
                return media['url']
                
    # 2. Tenta via media_thumbnail
    if hasattr(entry, 'media_thumbnail'):
        for thumb in entry.media_thumbnail:
            if 'url' in thumb:
                return thumb['url']

    # 3. Procura tags <img> dentro do corpo do texto (summary ou content)
    texto_completo = ""
    if hasattr(entry, 'summary'):
        texto_completo += entry.summary
    if hasattr(entry, 'content'):
        for c in entry.content:
            texto_completo += c.get('value', '')
            
    match = re.search(r'<img[^>]+src="([^">]+)"', texto_completo)
    if match:
        return match.group(1)
        
    return None

def parse_data_item(entry):
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6])
            return dt.strftime("%Y"), dt.strftime("%B / %Y")
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            dt = datetime(*entry.updated_parsed[:6])
            return dt.strftime("%Y"), dt.strftime("%B / %Y")
    except Exception:
        pass
    return "Recentes / Outros", "Recentes"

@st.cache_data(ttl=3600)
def carregar_dados():
    relatorio_geral = {}
    for nome_fonte, url_rss in FONTES.items():
        feed = feedparser.parse(url_rss)
        
        if not feed.entries and "MRE" in nome_fonte:
            feed = feedparser.parse("https://www.gov.br/mre/pt-br/assuntos/noticias/RSS")

        itens_por_periodo = {}
        
        for entry in feed.entries[:20]: 
            resumo = entry.get("summary", entry.get("description", "Resumo oficial disponível no link."))
            # Remove tags HTML básicas do resumo para manter o visual limpo
            resumo_limpo = re.sub('<[^<]+?>', '', resumo)
            if len(resumo_limpo) > 150:
                resumo_limpo = resumo_limpo[:147] + "..."
                
            link_base = entry.link
            imagem_url = extrair_imagem(entry)
            ano, mes_ano = parse_data_item(entry)
            
            idiomas = ["pt", "en", "es", "fr"]
            dados_idiomas = {}
            idioma_atual = next((l for l in idiomas if f"/{l}/" in link_base), "en")
            
            for lang in idiomas:
                url_candidata = link_base.replace(f"/{idioma_atual}/", f"/{lang}/")
                dados_idiomas[lang] = {
                    "link": url_candidata, 
                    "resumo": resumo_limpo if lang == idioma_atual else "Disponível no link oficial correspondente."
                }
                
            item_obj = {
                "titulo": entry.title,
                "data_texto": entry.get("published", entry.get("updated", "Data recente")),
                "imagem": imagem_url,
                "versoes": dados_idiomas
            }
            
            if ano not in itens_por_periodo:
                itens_por_periodo[ano] = []
            itens_por_periodo[ano].append(item_obj)
            
        relatorio_geral[nome_fonte] = itens_por_periodo
    return relatorio_geral

# Título do Dashboard
st.markdown("<h1>Boletim Diplomático</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Painel Geopolítico • MRE & ONU</div>", unsafe_allow_html=True)

with st.spinner("Carregando acervo e mídias oficiais..."):
    dados = carregar_dados()

# Abas de navegação limpas
abas = st.tabs(list(FONTES.keys()))

for i, (nome_fonte, periodos) in enumerate(dados.items()):
    with abas[i]:
        st.markdown("<br>", unsafe_allow_html=True)
        if not periodos:
            st.info("Nenhum registro encontrado no canal oficial no momento.")
            continue
            
        anos_ordenados = sorted([a for a in periodos.keys() if a.isdigit()], reverse=True)
        if "Recentes / Outros" in periodos:
            anos_ordenados.append("Recentes / Outros")
            
        for ano in anos_ordenados:
            st.markdown(f'<div class="periodo-header">📅 {ano}</div>', unsafe_allow_html=True)
            
            for item in periodos[ano]:
                # Contêiner principal do Cartão Moderno
                st.markdown('<div class="card">', unsafe_allow_html=True)
                
                # Se houver imagem oficial na notícia/nota, exibe no topo do cartão
                if item['imagem']:
                    try:
                        st.image(item['imagem'], use_container_width=True)
                    except Exception:
                        pass
                
                st.markdown('<div class="card-content">', unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="item-title">{item['titulo']}</div>
                    <div class="item-date">Publicação: {item['data_texto']}</div>
                """, unsafe_allow_html=True)
                
                # Exibição dos blocos multilíngues lado a lado de forma compacta
                cols = st.columns(len(item['versoes']))
                for idx, (lang, info) in enumerate(item['versoes'].items()):
                    with cols[idx]:
                        st.markdown(f"""
                            <div class="lang-box">
                                <div class="lang-label">[{lang.upper()}]</div>
                                <div class="lang-text">{info['resumo']}</div>
                                <a href="{info['link']}" target="_blank" style="font-size: 11px; color: #2563eb; text-decoration: none; font-weight: 600;">Abrir &rarr;</a>
                            </div>
                        """, unsafe_allow_html=True)
                
                st.markdown('</div></div>', unsafe_allow_html=True)

# Rodapé minimalista
st.markdown("<br><hr style='border:0; border-top:1px solid #e2e8f0;'><p style='text-align: center; color: #94a3b8; font-size: 11px;'>Atualizado via Agente Diplomático Automatizado</p>", unsafe_allow_html=True)
