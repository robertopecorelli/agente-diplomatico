import streamlit as st
import feedparser
from datetime import datetime
import re

# 1. Configuração da página
st.set_page_config(
    page_title="Repositório Diplomático | MRE & ONU",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Injeção de CSS com a Paleta Personalizada (#F0E6D2, #262626, #D19A7D, #B76D4D)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Cinzel:wght@600;700&display=swap');

    /* Estilo Global e Fundo */
    html, body, [class*="stApp"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #F0E6D2 !important;
        color: #262626;
    }

    /* Barra Superior Informativa */
    .top-bar {
        background-color: #262626;
        color: #F0E6D2;
        padding: 8px 20px;
        font-size: 11px;
        font-weight: 600;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #D19A7D;
        letter-spacing: 0.5px;
        margin-bottom: 20px;
        border-radius: 4px;
    }
    .top-bar-live {
        color: #D19A7D;
        font-weight: 700;
    }

    /* Cabeçalho do Repositório Diplomático */
    .portal-header {
        text-align: center;
        padding: 10px 0 20px 0;
        border-bottom: 2px solid #D19A7D;
        margin-bottom: 30px;
    }
    .portal-title {
        font-family: 'Cinzel', serif;
        font-size: 38px;
        font-weight: 700;
        color: #262626;
        letter-spacing: 3px;
        margin: 0;
        text-transform: uppercase;
    }
    .portal-tagline {
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #B76D4D;
        margin-top: 8px;
        font-weight: 700;
    }

    /* Badges e Divisores de Época */
    .section-badge {
        display: inline-block;
        background-color: #B76D4D;
        color: #ffffff;
        font-size: 11px;
        font-weight: 700;
        padding: 5px 14px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 16px;
    }
    .period-header {
        font-family: 'Playfair Display', serif;
        font-size: 24px;
        font-weight: 700;
        color: #262626;
        border-bottom: 2px solid #B76D4D;
        padding-bottom: 6px;
        margin: 35px 0 20px 0;
    }

    /* Cartão da Notícia / Nota / Discurso */
    .news-card {
        background: #ffffff;
        border-radius: 12px;
        border: 1px solid #D19A7D;
        overflow: hidden;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(38, 38, 38, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .news-card:hover {
        box-shadow: 0 8px 20px rgba(183, 109, 77, 0.15);
        border-color: #B76D4D;
    }
    .card-body {
        padding: 22px;
    }
    .meta-tag {
        font-size: 11px;
        font-weight: 800;
        color: #B76D4D;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    .card-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 20px;
        font-weight: 700;
        color: #262626;
        line-height: 1.35;
        margin-bottom: 10px;
    }
    .card-date {
        font-size: 11px;
        color: #666666;
        font-weight: 500;
        margin-bottom: 14px;
    }
    .card-excerpt {
        font-size: 13.5px;
        color: #262626;
        line-height: 1.55;
        margin-bottom: 16px;
    }
    .cacd-tag {
        background-color: #F0E6D2;
        border-left: 4px solid #B76D4D;
        padding: 8px 12px;
        font-size: 11.5px;
        color: #262626;
        border-radius: 0 4px 4px 0;
        margin-bottom: 16px;
        font-weight: 600;
    }

    /* Ajuste da Imagem no topo do cartão */
    .stImage img {
        border-radius: 0px;
        max-height: 250px;
        object-fit: cover;
        width: 100%;
        border-bottom: 1px solid #D19A7D;
    }

    /* Botões de Idioma */
    .lang-link {
        display: block;
        text-align: center;
        background-color: #F0E6D2;
        padding: 6px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        color: #262626;
        text-decoration: none;
        border: 1px solid #D19A7D;
        transition: all 0.2s ease;
    }
    .lang-link:hover {
        background-color: #B76D4D;
        color: #ffffff;
        border-color: #B76D4D;
    }

    /* Estilização da Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 2px solid #D19A7D;
    }
    .sidebar-title {
        font-family: 'Cinzel', serif;
        font-size: 16px;
        font-weight: 700;
        color: #262626;
        margin-bottom: 15px;
        border-bottom: 2px solid #B76D4D;
        padding-bottom: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Cabeçalho Principal
data_hoje = datetime.now().strftime("%A, %d de %B de %Y").capitalize()
st.markdown(f"""
    <div class="top-bar">
        <div>📅 {data_hoje} | BRASÍLIA & NOVA YORK</div>
        <div class="top-bar-live">● BASE ATUALIZADA EM TEMPO REAL</div>
    </div>
    <div class="portal-header">
        <h1 class="portal-title">REPOSITÓRIO DIPLOMÁTICO</h1>
        <div class="portal-tagline">Acervo Informativo • Notícias, Notas e Discursos do MRE & ONU</div>
    </div>
""", unsafe_allow_html=True)

# 4. Fontes RSS Oficiais
FONTES = {
    "MRE (Notas à Imprensa)": ("https://www.gov.br/mre/pt-br/centrais-de-conteudo/notas-a-imprensa/RSS", "MRE", "Nota à Imprensa"),
    "MRE (Discursos Oficiais)": ("https://www.gov.br/mre/pt-br/centrais-de-conteudo/discursos/RSS", "MRE", "Discurso"),
    "ONU (Notícias Globais)": ("https://news.un.org/feed/subscribe/en/news/all/rss.xml", "ONU", "Notícia"),
    "ONU (Declarações & Discursos)": ("https://news.un.org/feed/subscribe/en/news/topic/statements/feed.rss", "ONU", "Statement")
}

def extrair_imagem(entry):
    """Extrai imagens anexadas nos feeds RSS ou no corpo HTML do resumo/conteúdo."""
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if isinstance(media, dict) and 'url' in media:
                return media['url']
                
    if hasattr(entry, 'media_thumbnail'):
        for thumb in entry.media_thumbnail:
            if isinstance(thumb, dict) and 'url' in thumb:
                return thumb['url']

    if hasattr(entry, 'enclosures'):
        for enc in entry.enclosures:
            if hasattr(enc, 'type') and 'image' in enc.type:
                return enc.href
            elif isinstance(enc, dict) and enc.get('type', '').startswith('image'):
                return enc.get('href')

    texto_busca = entry.get("summary", "") + " " + entry.get("description", "")
    if hasattr(entry, 'content'):
        for c in entry.content:
            texto_busca += " " + c.get('value', '')

    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', texto_busca, re.IGNORECASE)
    if match:
        return match.group(1)

    return None

def classificar_tema(texto):
    """Classifica o item em eixos temáticos diplomáticos com inclusão do Conselho de Segurança."""
    texto_lc = texto.lower()
    
    # 1. Prioridade para Conselho de Segurança da ONU
    if any(k in texto_lc for k in ["conselho de segurança", "csnu", "security council", "unsc"]):
        return "Conselho de Segurança da ONU", "Global / ONU"
    elif any(k in texto_lc for k in ["brasil", "itamaraty", "mercosul", "sul-americano", "bilateral", "palácio"]):
        return "Política Externa Brasileira", "América do Sul"
    elif any(k in texto_lc for k in ["clima", "meio ambiente", "cop", "sustentav", "amazônia", "carbono"]):
        return "Meio Ambiente & Clima", "Global"
    elif any(k in texto_lc for k in ["comércio", "tarif", "omc", "econôm", "exporta", "acordo"]):
        return "Economia & Comércio", "Global"
    elif any(k in texto_lc for k in ["direitos humanos", "refugiad", "genocídi", "mulher", "humanitá"]):
        return "Direitos Humanos", "Global"
    elif any(k in texto_lc for k in ["conflito", "paz", "segurança", "ucrânia", "oriente médio", "gaza", "armas"]):
        return "Segurança & Paz", "Oriente Médio / Europa"
    return "Governança Global", "Global"

def parse_data_item(entry):
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6])
            return dt.strftime("%Y"), dt.strftime("%b / %Y"), dt.strftime("%d/%m/%Y")
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            dt = datetime(*entry.updated_parsed[:6])
            return dt.strftime("%Y"), dt.strftime("%b / %Y"), dt.strftime("%d/%m/%Y")
    except Exception:
        pass
    return "2026", "Recentes", "Data Recente"

@st.cache_data(ttl=1800)
def carregar_acervo():
    todos_itens = []
    for nome_fonte, (url_rss, orgao, tipo_doc) in FONTES.items():
        feed = feedparser.parse(url_rss)
        
        if not feed.entries and orgao == "MRE":
            feed = feedparser.parse("https://www.gov.br/mre/pt-br/assuntos/noticias/RSS")

        # Processa TODOS os registros disponibilizados pelos feeds sem limitação
        for entry in feed.entries:
            resumo_bruto = entry.get("summary", entry.get("description", "Consulte a publicação na íntegra através do link oficial."))
            resumo_limpo = re.sub('<[^<]+?>', '', resumo_bruto)
            if len(resumo_limpo) > 180:
                resumo_limpo = resumo_limpo[:177] + "..."

            link_base = entry.link
            imagem_url = extrair_imagem(entry)
            ano, mes_ano, data_formatada = parse_data_item(entry)
            tema, regiao = classificar_tema(entry.title + " " + resumo_limpo)

            idiomas = ["pt", "en", "es", "fr"]
            dados_idiomas = {}
            idioma_atual = next((l for l in idiomas if f"/{l}/" in link_base), "pt" if orgao == "MRE" else "en")

            for lang in idiomas:
                dados_idiomas[lang] = link_base.replace(f"/{idioma_atual}/", f"/{lang}/")

            item_obj = {
                "titulo": entry.title,
                "resumo": resumo_limpo,
                "orgao": orgao,
                "tipo": tipo_doc,
                "fonte_nome": nome_fonte,
                "data_fmt": data_formatada,
                "ano": ano,
                "mes_ano": mes_ano,
                "imagem": imagem_url,
                "tema": tema,
                "regiao": regiao,
                "links": dados_idiomas
            }
            todos_itens.append(item_obj)
    return todos_itens

# Carregamento de dados
with st.spinner("Atualizando acervo diplomático..."):
    acervo = carregar_acervo()

# 5. BARRA LATERAL (Filtros de Pesquisa)
with st.sidebar:
    st.markdown('<div class="sidebar-title">🔍 Filtros do Repositório</div>', unsafe_allow_html=True)
    
    busca = st.text_input("Buscar palavra-chave", placeholder="Ex: CSNU, G20, Tarifas, Gaza, COP")
    
    filtro_orgao = st.multiselect(
        "Órgão / Origem", 
        ["MRE", "ONU"], 
        default=["MRE", "ONU"]
    )
    
    filtro_tema = st.selectbox(
        "Eixo Temático",
        [
            "Todos os Temas", 
            "Conselho de Segurança da ONU", 
            "Política Externa Brasileira", 
            "Governança Global", 
            "Economia & Comércio", 
            "Segurança & Paz", 
            "Direitos Humanos", 
            "Meio Ambiente & Clima"
        ]
    )
    
    filtro_ano = st.selectbox(
        "Época / Ano",
        ["Todos os Anos"] + sorted(list(set([i["ano"] for i in acervo])), reverse=True)
    )

    st.markdown("---")
    st.markdown("### 🎓 Acervo Diplomático")
    st.caption("Organização contínua dos discursos, notícias e notas do Ministério das Relações Exteriores e da Organização das Nações Unidas.")

# 6. FILTRAGEM DOS DADOS
itens_filtrados = acervo

if busca:
    itens_filtrados = [i for i in itens_filtrados if busca.lower() in i["titulo"].lower() or busca.lower() in i["resumo"].lower()]

if filtro_orgao:
    itens_filtrados = [i for i in itens_filtrados if i["orgao"] in filtro_orgao]

if filtro_tema != "Todos os Temas":
    itens_filtrados = [i for i in itens_filtrados if i["tema"] == filtro_tema]

if filtro_ano != "Todos os Anos":
    itens_filtrados = [i for i in itens_filtrados if i["ano"] == filtro_ano]

# 7. EXIBIÇÃO EM GRID E DIVISÃO POR ÉPOCAS
st.markdown(f'<div class="section-badge">Exibindo {len(itens_filtrados)} registros cadastrados</div>', unsafe_allow_html=True)

anos_disponiveis = sorted(list(set([i["ano"] for i in itens_filtrados])), reverse=True)

for ano in anos_disponiveis:
    st.markdown(f'<div class="period-header">📅 Registros do Ano de {ano}</div>', unsafe_allow_html=True)
    itens_ano = [i for i in itens_filtrados if i["ano"] == ano]

    # Grid em 2 colunas para navegação fluida
    cols = st.columns(2)
    for idx, item in enumerate(itens_ano):
        col_atual = cols[idx % 2]
        
        with col_atual:
            st.markdown('<div class="news-card">', unsafe_allow_html=True)
            
            # Exibição de Imagens e Fotos oficiais
            if item["imagem"]:
                try:
                    st.image(item["imagem"], use_container_width=True)
                except Exception:
                    pass
            
            st.markdown(f"""
                <div class="card-body">
                    <div class="meta-tag">{item['orgao']} • {item['tipo']}</div>
                    <div class="card-title">{item['titulo']}</div>
                    <div class="card-date">Data oficial: {item['data_fmt']} | {item['regiao']}</div>
                    <div class="cacd-tag">📌 <b>Tema:</b> {item['tema']}</div>
                    <div class="card-excerpt">{item['resumo']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Links multilíngues estilizados
            st.markdown("<p style='font-size: 10px; font-weight:700; color:#B76D4D; margin-left:22px; text-transform:uppercase;'>Acessar documento oficial:</p>", unsafe_allow_html=True)
            l_cols = st.columns(4)
            for l_idx, (lang, link_url) in enumerate(item["links"].items()):
                with l_cols[l_idx]:
                    st.markdown(f'<a href="{link_url}" target="_blank" class="lang-link">[{lang.upper()}]</a>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# 8. Rodapé Oficial
st.markdown("---")
st.markdown("""
    <div style="text-align: center; padding: 20px; color: #262626; font-size: 12px; font-weight: 500;">
        <b>REPOSITÓRIO DIPLOMÁTICO</b> • Acervo de Inteligência Informativa e Pesquisa Diplomática.<br>
        Sincronizado diretamente com os canais oficiais do Ministério das Relações Exteriores do Brasil e da Organização das Nações Unidas.
    </div>
""", unsafe_allow_html=True)
