import streamlit as st
import google.generativeai as genai
from apify_client import ApifyClient
from serpapi import GoogleSearch
import json
import re

# API Yapılandırmaları (Çevresel değişkenlerden çekilmesi önerilir)
GEMINI_API_KEY = "SİZİN_GEMINI_API_ANAHTARINIZ"
APIFY_API_TOKEN = "SİZİN_APIFY_API_ANAHTARINIZ"
SERPAPI_API_KEY = "SİZİN_SERPAPI_API_ANAHTARINIZ"

genai.configure(api_key=GEMINI_API_KEY)

# Kozmetik Sektörüne Özel Optimize Edilmiş Sistem Komutu
SYSTEM_PROMPT = """
Sen, Ticaret Bakanlığı Reklam Kurulu mevzuatına hakim, kozmetik ürün reklamları üzerine uzmanlaşmış bir hukuki denetim asistanısın.
Görevin, sunulan kozmetik reklam metnini inceleyerek mevzuata aykırılıkları tespit etmektir. 
Özellikle şu ihlallere odaklan:
1. Hastalıkları tedavi edici (endikasyon belirten) ilaç algısı yaratan sağlık beyanları.
2. "Bilimsel olarak kanıtlanmıştır", "%100 etkili" gibi bağımsız klinik test gerektiren ispatlanmamış mutlak iddialar.

Lütfen SADECE aşağıdaki JSON formatında yanıt ver:
{
  "uyumluluk_durumu": "Başarılı" veya "İhlal Tespit Edildi",
  "ihlal_kategorisi": ["Örn: Sağlık Beyanı İhlali", "İspatlanmamış İddia"],
  "riskli_ifadeler": ["İhlale konu olan doğrudan alıntılar"],
  "hukuki_gerekce": ["Mevzuata dayalı kısa açıklama"],
  "duzeltme_onerisi": ["Metnin yasal hale getirilmesi için somut öneri"]
}
"""

def clean_and_filter_text(text):
    """Web ve arama sonuçlarından gelen ham metindeki menü, footer ve anlamsız verileri filtreler."""
    if not text:
        return ""
    lines = text.split('\n')
    # 20 karakterden kısa satırları ve sadece sembol içeren (navigasyon/UI) kısımları ele
    filtered_lines = [
        line.strip() for line in lines 
        if len(line.strip()) > 20 and not re.match(r'^[^a-zA-Z0-9ğüşöçİĞÜŞÖÇ]+$', line.strip())
    ]
    return " ".join(filtered_lines)

def analyze_with_gemini(text_to_analyze):
    """Optimize edilmiş prompt ile Gemini analizini başlatır."""
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    response = model.generate_content(f"{SYSTEM_PROMPT}\n\nİncelenecek Kozmetik Reklam Metni:\n{text_to_analyze}")
    return response.text

st.set_page_config(page_title="AdShield | Kozmetik Denetim", page_icon="🛡️", layout="wide")

st.title("🛡️ AdShield: Kozmetik Reklam Uyumluluk Denetimi")

st.sidebar.header("Veri Toplama Araçları")
veri_kaynagi = st.sidebar.radio("Analiz Edilecek Veri Kaynağı:", ["Manuel Metin Girişi", "Web Sayfası (Apify)", "Arama Motoru (SerpApi)"])

ad_text = ""
raw_text = ""

if veri_kaynagi == "Manuel Metin Girişi":
    ad_text = st.text_area("Kozmetik reklam metnini veya senaryosunu buraya yapıştırın:", height=200)

elif veri_kaynagi == "Web Sayfası (Apify)":
    target_url = st.text_input("Taranacak kozmetik ürün URL'sini girin:")
    if st.button("Apify ile İçerik Çek"):
        with st.spinner("Apify üzerinden sayfa verisi alınıyor..."):
            client = ApifyClient(APIFY_API_TOKEN)
            run = client.actor("apify/web-scraper").call(run_input={"startUrls": [{"url": target_url}]})
            dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
            if dataset_items:
                raw_text = dataset_items[0].get('text', '')
                ad_text = clean_and_filter_text(raw_text)
                st.success("Veri başarıyla çekildi ve filtrelendi!")
                st.text_area("Filtrelenmiş Analiz Verisi:", value=ad_text, height=150)

elif veri_kaynagi == "Arama Motoru (SerpApi)":
    search_query = st.text_input("Kozmetik ürün veya kampanya araması yapın:")
    if st.button("SerpApi ile Ara"):
        with st.spinner("Arama sonuçları getiriliyor ve filtreleniyor..."):
            params = {
              "engine": "google",
              "q": search_query,
              "api_key": SERPAPI_API_KEY,
              "gl": "tr",
              "hl": "tr"
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            organic_results = results.get("organic_results", [])
            
            raw_text = " ".join([res.get("snippet", "") for res in organic_results[:5]])
            ad_text = clean_and_filter_text(raw_text)
            
            st.success("Arama tamamlandı!")
            st.info(f"Filtrelenmiş Arama Özetleri:\n{ad_text}")

if st.button("Denetimi Başlat", type="primary") and ad_text:
    with st.spinner("Gemini API üzerinden hukuki denetim yapılıyor..."):
        try:
            result = analyze_with_gemini(ad_text)
            cleaned_result = result.replace("```json", "").replace("```", "").strip()
            parsed_json = json.loads(cleaned_result)
            
            st.subheader("📊 Analiz Sonucu")
            
            if parsed_json.get("uyumluluk_durumu") == "İhlal Tespit Edildi":
                st.error(f"Durum: {parsed_json.get('uyumluluk_durumu')}")
            else:
                st.success(f"Durum: {parsed_json.get('uyumluluk_durumu')}")
                
            st.json(parsed_json)
            
        except Exception as e:
            st.error(f"Bir hata oluştu: {str(e)}")
elif st.button("Denetimi Başlat") and not ad_text:
    st.warning("Lütfen analiz edilecek bir metin girin veya veri kaynaklarından içerik çekin.")
