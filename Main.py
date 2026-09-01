import feedparser
import requests

# Feed principal de referência (ex: ONU News em Inglês)
URL_FEED_BASE = "https://news.un.org/feed/subscribe/en/news/all/rss.xml"

def validar_idiomas_disponiveis(link_base):
    """
    Testa se a mesma notícia possui versão oficial publicada 
    em Português, Inglês, Espanhol e Francês alterando a estrutura da URL.
    """
    idiomas = ["pt", "en", "es", "fr"]
    idiomas_disponiveis = {}
    
    # Identifica o padrão de idioma atual na URL de origem
    idioma_atual = None
    for lang in idiomas:
        if f"/{lang}/" in link_base:
            idioma_atual = lang
            break
            
    # Se a URL não seguir o padrão esperado, retorna ao menos a original
    if not idioma_atual:
        return {"en": link_base}

    # Testa a existência da página para cada um dos 4 idiomas oficiais
    for lang in idiomas:
        url_candidata = link_base.replace(f"/{idioma_atual}/", f"/{lang}/")
        
        try:
            # Usa requisição HEAD para verificar o status sem baixar a página inteira
            response = requests.head(url_candidata, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                idiomas_disponiveis[lang] = url_candidata
            else:
                # Fallback para GET caso o servidor bloqueie requisições HEAD
                response_get = requests.get(url_candidata, timeout=5)
                if response_get.status_code == 200:
                    idiomas_disponiveis[lang] = url_candidata
        except requests.RequestException:
            # Caso o link não exista (ex: erro 404 de tradução ausente) ou falha de rede
            pass
            
    return idiomas_disponiveis

def executar_varredura_diaria():
    print("Iniciando varredura dos canais oficiais...")
    feed = feedparser.parse(URL_FEED_BASE)
    
    relatorio_diario = []

    # Analisa as últimas 5 publicações do dia
    for entry in feed.entries[:5]:
        print(f"Verificando: {entry.title[:60]}...")
        
        # Mapeia quais idiomas possuem a versão oficial ativa
        versoes_encontradas = validar_idiomas_disponiveis(entry.link)
        
        relatorio_diario.append({
            "titulo": entry.title,
            "data": entry.get("published", "Data não informada"),
            "links_oficiais": versoes_encontradas
        })
        
    return relatorio_diario

if __name__ == "__main__":
    comunicados = executar_varredura_diaria()
    
    print("\n" + "="*50)
    print("RELATÓRIO DE DISCURSOS E NOTAS OFICIAIS NATIVAS")
    print("="*50)
    
    for item in comunicados:
        print(f"\n📌 Título: {item['titulo']}")
        print(f"📅 Publicação: {item['data']}")
        print("🔗 Links Oficiais Disponíveis por Idioma:")
        for lang, url in item['links_oficiais'].items():
            print(f"   - [{lang.upper()}]: {url}")
        print("-" * 50)
