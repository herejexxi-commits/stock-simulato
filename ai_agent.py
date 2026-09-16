import google.generativeai as genai

def generate_stock_analysis(api_key: str, symbol: str, company_name: str, price: float, news_headlines: list) -> str:
    """
    Se conecta a la API de Google Gemini para generar un reporte
    de análisis rápido sobre un activo financiero basado en noticias recientes.
    """
    if not api_key:
        return "⚠️ No se ha proporcionado una API Key de Gemini. Por favor configúrala en la pestaña de Ajustes de Cuenta."
    
    try:
        genai.configure(api_key=api_key)
        
        # El API requiere explícitamente el uso de gemini-3.6-flash para nuevos usuarios
        model = genai.GenerativeModel('gemini-3.6-flash')
        
        news_text = "\n".join([f"- {title} (Fuente: {source})" for title, source in news_headlines])
        if not news_text:
            news_text = "No se encontraron noticias recientes para este activo."
            
        prompt = f"""
Eres un analista financiero experto. Se te ha pedido un reporte rápido y objetivo sobre la acción: {symbol} ({company_name}).
El precio actual de cotización estimado es de ${price} USD.

Aquí tienes los titulares de noticias más recientes de la empresa:
{news_text}

Con base en esta información:
1. Dame un breve resumen de qué sentimiento general transmiten estas noticias (positivo, negativo, o neutral) y por qué.
2. Identifica los principales riesgos o catalizadores a corto plazo.
3. Concluye en un párrafo si las noticias recientes podrían tener un impacto significativo en el precio de la acción en los próximos días.

Mantén tu respuesta estructurada, profesional, clara, y enfocada solo en la información proporcionada.
"""
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"❌ Hubo un error al comunicarse con la IA de Gemini: {str(e)}"
