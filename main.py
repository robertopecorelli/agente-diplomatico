import streamlit as st
import feedparser
from datetime import datetime
import re

# 1. Configuração da página em modo WIDE (Layout de Portal de Notícias)
st.set_page_config(
    page_title="UBIQUE DIPLOMÁTICO | MRE & ONU",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Injeção de CSS inspirada no Ubique News (Tipografia Editorial + Bento Grid)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Cinzel:wght@600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #f8fafc;
        color: #0f172a;
    }

    /* Top Utility Bar */
    .top-bar {
        background-color: #0b192c;
        color: #94a3b8;
        padding: 6px 20px;
        font-size: 11px;
        font-weight: 500;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #1e293b;
        letter-spacing: 0.5px;
        margin-bottom: 15px;
    }
    .top-bar-live {
        color: #38bdf8;
        font-weight: 600;
    }

    /* Portal Branding Header */
    .ubique-header {
        text-align: center;
        padding: 20px 0 10px 0;
        border-bottom: 2px solid #e2e8f0;
        margin-bottom: 25px;
    }
    .ubique-title {
        font-family: 'Cinzel', serif;
        font-size: 38px;
        font-weight: 700;
        color: #0b192c;
        letter-spacing: 2px;
        margin: 0;
        text-transform: uppercase;
    }
    .ubique-tagline {
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 2.5px;
        color: #64748b;
        margin-top: 6px;
        font-weight: 600;
    }

    /* Section & Period Headers */
    .section-badge {
        display: inline-block;
        background-color: #1e3a8a;
        color: #ffffff;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 12px;
    }
    .period-header {
        font-family: 'Playfair Display', serif;
        font-size: 22px;
        font-weight: 700;
        color: #0b192c;
        border-bottom: 2px solid #1e3a8a;
        padding-bottom: 6px;
        margin: 30px 0 20px 0;
    }

    /* Article Card - Ubique Style */
    .news-card {
        background: #ffffff;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        overflow: hidden;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        transition: all 0.2s ease-in-out;
    }
    .news-card:hover {
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
        border-color: #cbd5e1;
    }
    .card-body {
        padding: 20px;
    }
    .meta-tag {
        font-size: 10px;
        font-weight: 700;
        color: #1d4ed8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .card-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 19px;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.35;
        margin-bottom: 8px;
        text-decoration: none;
    }
    .card-date {
        font-size: 11px;
        color: #94a3b8;
        font-weight: 500;
        margin-bottom: 12px;
    }
    .card-excerpt {
        font-size: 13px;
        color: #475569;
        line-height: 1.5;
        margin-bottom: 16px;
    }
    .cacd-tag {
        background-color: #f1f5f9;
        border-left: 3px solid #2563eb;
        padding: 6px 10px;
        font-size: 11px;
        color: #334155;
        border-radius: 0 4px 4px 0;
        margin-bottom: 14px;
        font-weight: 500;
    }

    /* Image Container */
    .stImage img {
        border-radius: 8px 8px 0 0;
        max-height: 220px;
        object-fit: cover;
        width: 100%;
    }

    /* Sidebar Styling */
    .sidebar-title {
        font-family: 'Cinzel', serif;
        font-size: 16px;
        font-weight: 700;
        color: #0b192c;
        margin-bottom: 15px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Cabeçalho Topo (Data Atual + Transmissão)
data_hoje = datetime.now().strftime("%A, %d de %B de %Y").capitalize()
st.markdown(f"""
    <div class="top-bar">
        <div>📅 {data_hoje} | BRASÍLIA & NOVA YORK</div>
        <div class="top-bar-live">● MONITOR DIPLOMÁTICO EM TEMPO REAL</div>
    </div>
    <div class="ubique-header">
        <h1 class="ubique-title">UBIQUE DIPLOMÁTICO</h1>
        <div class="ubique-tagline">Portal de Inteligência Informativa • MRE & ONU</div>
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
    """Extrai imagens anexadas nos feeds ou no HTML do resumo."""
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if 'url' in media: return media['url']
    if hasattr(entry, 'media_thumbnail'):
        for thumb in entry.media_thumbnail:
            if 'url' in thumb: return thumb['url']
    
    texto = entry.get("summary", "") + "".join([c.get('value', '') for c in entry.get('content', [])])
    match = re.search(r'<img[^>]+src="([^">]+)"', texto)
    if match: return match.group(1)
    return None

def classificar_tema_cacd(texto):
    """Atribui eixos temáticos relevantes para estudo do CACD/RI."""
    texto_lc = texto.lower()
    if any(k in texto_lc for k in ["brasil", "itamaraty", "mercosul", "sul-americano", "bilateral"]):
        return "Política Externa Brasileira", "América do Sul"
    elif any(k in texto_lc for k in ["clima", "meio ambiente", "cop", "sustentav", "amazônia"]):
        return "Meio Ambiente & Clima", "Global"
    elif any(k in texto_lc for k in ["comércio", "tarif", "omc", "econôm", "exporta"]):
        return "Economia & Comércio", "Global"
    elif any(k in texto_lc for k in ["direitos humanos", "refugiad", "genocídi", "mulher"]):
        return "Direitos Humanos", "Global"
    elif any(k in texto_lc for k in ["conflito", "paz", "segurança", "ucrânia", "oriente médio", "gaza"]):
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

        for entry in feed.entries[:25]:
            resumo_bruto = entry.get("summary", entry.get("description", "Acesse o link oficial para a leitura completa."))
            resumo_limpo = re.sub('<[^<]+?>', '', resumo_bruto)
            if len(resumo_limpo) > 180:
                resumo_limpo = resumo_limpo[:177] + "..."

            link_base = entry.link
            imagem_url = extrair_imagem(entry)
            ano, mes_ano, data_formatada = parse_data_item(entry)
            tema, regiao = classificar_tema_cacd(entry.title + " " + resumo_limpo)

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

# Carrega os dados
with st.spinner("Conectando aos feeds do MRE & ONU..."):
    acervo = carregar_acervo()

# 5. BARRA LATERAL (Filtros Estilo Ubique News)
with st.sidebar:
    st.markdown('<div class="sidebar-title">🔍 Filtros de Inteligência</div>', unsafe_allow_html=True)
    
    busca = st.text_input("Buscar palavra-chave", placeholder="Ex: G20, Tarifas, Gaza, COP")
    
    filtro_orgao = st.multiselect(
        "Órgão / Fonte", 
        ["MRE", "ONU"], 
        default=["MRE", "ONU"]
    )
    
    filtro_tema = st.selectbox(
        "Eixo Temático",
        ["Todos os Temas", "Política Externa Brasileira", "Governança Global", "Economia & Comércio", "Segurança & Paz", "Direitos Humanos", "Meio Ambiente & Clima"]
    )
    
    filtro_ano = st.selectbox(
        "Época / Ano",
        ["Todos os Anos"] + sorted(list(set([i["ano"] for i in acervo])), reverse=True)
    )

    st.markdown("---")
    st.markdown("### 🎓 Conexão CACD")
    st.caption("Acompanhamento contínuo dos temas da agenda diplomática e política externa do Brasil.")

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

# 7. EXIBIÇÃO PRINCIPAL - GRID DIPLOMÁTICO
st.markdown(f'<div class="section-badge">Exibindo {len(itens_filtrados)} registros diplomáticos</div>', unsafe_allow_html=True)

# Agrupamento por Ano/Época
anos_disponiveis = sorted(list(set([i["ano"] for i in itens_filtrados])), reverse=True)

for ano in anos_disponiveis:
    st.markdown(f'<div class="period-header">📅 Acervo de {ano}</div>', unsafe_allow_html=True)
    itens_ano = [i for i in itens_filtrados if i["ano"] == ano]

    # Exibe em Grid de 2 Colunas para visual de Portal
    cols = st.columns(2)
    for idx, item in enumerate(itens_ano):
        col_atual = cols[idx % 2]
        
        with col_atual:
            st.markdown('<div class="news-card">', unsafe_allow_html=True)
            
            # Imagem do artigo (se houver)
            if item["imagem"]:
                try:
                    st.image(item["imagem"], use_container_width=True)
                except Exception:
                    pass
            
            st.markdown(f"""
                <div class="card-body">
                    <div class="meta-tag">{item['orgao']} • {item['tipo']}</div>
                    <div class="card-title">{item['titulo']}</div>
                    <div class="card-date">Publicado em: {item['data_fmt']} | {item['regiao']}</div>
                    <div class="cacd-tag">📌 <b>Tema CACD:</b> {item['tema']}</div>
                    <div class="card-excerpt">{item['resumo']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Botões multilíngues rápidos estilo Ubique
            st.markdown("<p style='font-size: 10px; font-weight:700; color:#64748b; margin-left:20px;'>LER EM OUTROS IDIOMAS:</p>", unsafe_allow_html=True)
            l_cols = st.columns(4)
            for l_idx, (lang, link_url) in enumerate(item["links"].items()):
                with l_cols[l_idx]:
                    st.markdown(f'<a href="{link_url}" target="_blank" style="display:block; text-align:center; background:#f1f5f9; padding:4px; border-radius:4px; font-size:11px; font-weight:700; color:#1e3a8a; text-decoration:none;">[{lang.upper()}]</a>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# 8. Rodapé Estilo Editorial
st.markdown("---")
st.markdown("""
    <div style="text-align: center; padding: 20px; color: #64748b; font-size: 12px;">
        <b>UBIQUE DIPLOMÁTICO</b> • Plataforma Independente de Atualização Geopolítica e Preparação Diplomática.<br>
        Dados extraídos automaticamente dos portais oficiais do Ministério das Relações Exteriores e Organização das Nações Unidas.
    </div>
""", unsafe_allow_html=True)
