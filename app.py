import urllib.parse
import requests
import streamlit as st

def gelismis_coklu_hedef_taramasi(urun_adi, marka_domain, api_key):
    # 4 Farklı koldan nokta atışı arama komutları (Google Dorks)
    queries = {
        "Resmi Web Sitesi": f'"{urun_adi}" site:{marka_domain}',
        "Pazaryerleri (Trendyol & Hepsiburada)": f'"{urun_adi}" site:trendyol.com OR site:hepsiburada.com',
        "Sosyal Medya (Instagram)": f'"{urun_adi}" site:instagram.com',
        "Tüketici Şikayetleri & Forumlar": f'"{urun_adi}" site:sikayetvar.com'
    }
    
    kategorize_sonuclar = {}
    
    for kategori, sorgu in queries.items():
        # SerpApi'ye sorguyu gönderiyoruz
        url = f"https://serpapi.com/search.json?q={urllib.parse.quote(sorgu)}&api_key={api_key}&engine=google&gl=tr&hl=tr&num=15"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            link_havuzu = []
            # Organik sonuçlardan başlık ve linkleri çekiyoruz
            if "organic_results" in data:
                for result in data["organic_results"]:
                    link_havuzu.append({
                        "baslik": result.get("title"),
                        "url": result.get("link")
                    })
            
            kategorize_sonuclar[kategori] = link_havuzu
            
        except Exception as e:
            st.error(f"{kategori} taramasında hata: {e}")
            
    return kategorize_sonuclar

# --- Streamlit Arayüzünde Test Etmek İçin ---
# Bu kısmı arayüzde bir butona bağlayabilirsiniz
# ornek_sonuclar = gelismis_coklu_hedef_taramasi("mamaaura çatlak ve selülit yağı", "mamaaura.com", st.secrets["SERPAPI_API_KEY"])
# st.json(ornek_sonuclar) # Sadece linkleri ve başlıkları ekrana basar
