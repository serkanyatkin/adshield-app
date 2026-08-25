import streamlit as st
import urllib.parse
import requests

# --- 1. SAYFA VE ARAYÜZ AYARLARI ---
st.set_page_config(page_title="AdShield 360° Radar", page_icon="🛡️", layout="wide")
st.title("🛡️ AdShield 360° Çoklu Satıcı Radarı (Hedefli Link Avı)")
st.markdown("""
Bu test modülü; ürün görsellerini indirmeye çalışmadan (bot engellerine takılmadan) 
sadece pazar yerlerindeki, resmi sitedeki ve sosyal medyadaki **ilgili linkleri** saniyeler içinde tespit etmek için tasarlanmıştır.
""")

# --- 2. API ANAHTARI KONTROLÜ ---
try:
    SERPAPI_KEY = st.secrets["SERPAPI_API_KEY"]
except KeyError:
    st.error("HATA: Streamlit Secrets içinde 'SERPAPI_API_KEY' bulunamadı! Lütfen ayarları kontrol edin.")
    st.stop()

# --- 3. GELİŞMİŞ ARAMA FONKSİYONU ---
def gelismis_coklu_hedef_taramasi(urun_adi, marka_domain, api_key):
    # 4 Farklı koldan nokta atışı arama komutları (Google Dorks)
    queries = {
        "🌐 Resmi Web Sitesi Ağı": f'"{urun_adi}" site:{marka_domain}',
        "🛒 Pazaryerleri (Trendyol & Hepsiburada)": f'"{urun_adi}" site:trendyol.com OR site:hepsiburada.com',
        "📱 Sosyal Medya (Instagram)": f'"{urun_adi}" site:instagram.com',
        "⚖️ Tüketici Şikayetleri & Forumlar": f'"{urun_adi}" site:sikayetvar.com'
    }
    
    kategorize_sonuclar = {}
    
    for kategori, sorgu in queries.items():
        # SerpApi Google Arama Motoru İsteği
        url = f"https://serpapi.com/search.json?q={urllib.parse.quote(sorgu)}&api_key={api_key}&engine=google&gl=tr&hl=tr&num=10"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            link_havuzu = []
            if "organic_results" in data:
                for result in data["organic_results"]:
                    link_havuzu.append({
                        "baslik": result.get("title", "Başlık Bulunamadı"),
                        "url": result.get("link", "#")
                    })
            
            kategorize_sonuclar[kategori] = link_havuzu
            
        except Exception as e:
            st.error(f"{kategori} taramasında hata oluştu: {e}")
            
    return kategorize_sonuclar

# --- 4. KULLANICI KONTROL PANELİ ---
st.markdown("### 🎯 Tarama Kriterlerini Belirleyin")
with st.form("arama_formu"):
    col1, col2 = st.columns(2)
    with col1:
        urun_sorgusu = st.text_input("Hedef Ürün Adı:", value="mamaaura çatlak ve selülit yağı")
    with col2:
        marka_domaini = st.text_input("Markanın Resmi Web Sitesi (Domain):", value="mamaaura.com")
        
    calistir_butonu = st.form_submit_button("🚀 Hedef Linkleri Topla")

# --- 5. ARAMA TETİKLEME VE SONUÇLARI GÖSTERME ---
if calistir_butonu:
    if urun_sorgusu and marka_domaini:
        with st.spinner("Gelişmiş radar çalışıyor, platformlar taranıyor... (Bu işlem saniyeler sürer)"):
            sonuclar = gelismis_coklu_hedef_taramasi(urun_sorgusu, marka_domaini, SERPAPI_KEY)
            
            st.success("✅ Hedef link havuzu başarıyla oluşturuldu!")
            
            # Sonuçları sekmeler (tabs) halinde şık bir şekilde gösterelim
            sekme_isimleri = list(sonuclar.keys())
            sekmeler = st.tabs(sekme_isimleri)
            
            for i, kategori in enumerate(sekme_isimleri):
                with sekmeler[i]:
                    linkler = sonuclar[kategori]
                    if len(linkler) > 0:
                        st.info(f"Bu kategoride **{len(linkler)}** adet potansiyel riskli/incelenecek link bulundu.")
                        for idx, item in enumerate(linkler, 1):
                            st.markdown(f"**{idx}.** [{item['baslik']}]({item['url']})")
                    else:
                        st.warning("Bu kategoride herhangi bir indekslenmiş sonuç bulunamadı.")
    else:
        st.error("Lütfen hem ürün adını hem de domain adresini giriniz.")
