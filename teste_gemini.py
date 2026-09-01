import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Erro: GEMINI_API_KEY não foi encontrada nas variáveis de ambiente.")
else:
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents='Responda em uma frase: A API do Gemini está pronta para analisar matérias do CACD?'
        )
        print("✅ Conexão bem-sucedida!")
        print("Resposta do Gemini:", response.text)
    except Exception as e:
        print("❌ Falha na conexão com a API:")
        print(e)