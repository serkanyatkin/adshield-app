import streamlit as st
import urllib.parse
import requests
import google.generativeai as genai

# --- 1. SAYFA VE ARAYÜZ AYARLARI ---
st.set_page_config(page_title="AdShield 360° Radar", page_icon="🛡️", layout="wide")

# --- API ANAHTARLARI ---
try:
    SERPAPI_KEY = st.secrets["SERPAPI_API_KEY"]
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_KEY)
except KeyError:
    st.error("HATA: Streamlit Secrets içinde API anahtarları (SERPAPI_API_KEY veya GEMINI_API_KEY) bulunamadı!")
    st.stop()

# --- FONKSİYON: GELİŞMİŞ ARAMA (GÖRSELSİZ LİNK AVI) ---
def gelismis_coklu_hedef_taramasi(urun_adi, marka_domain, api_key):
    queries = {
        "🌐 Resmi Web Sitesi": f'"{urun_adi}" site:{marka_domain}',
        "🛒 Pazaryerleri (Trendyol vs.)": f'"{urun_adi}" site:trendyol.com OR site:hepsiburada.com',
        "📱 Sosyal Medya": f'"{urun_adi}" site:instagram.com',
        "⚖️ Şikayet & Forumlar": f'"{urun_adi}" site:sikayetvar.com'
    }
    
    kategorize_sonuclar = {}
    for kategori, sorgu in queries.items():
        url = f"https://serpapi.com/search.json?q={urllib.parse.quote(sorgu)}&api_key={api_key}&engine=google&gl=tr&hl=tr&num=10"
        try:
            response = requests.get(url)
            data = response.json()
            link_havuzu = []
            if "organic_results" in data:
                for result in data["organic_results"]:
                    link_havuzu.append({
                        "baslik": result.get("title", "Başlık Yok"),
                        "url": result.get("link", "#"),
                        "snippet": result.get("snippet", "")
                    })
            kategorize_sonuclar[kategori] = link_havuzu
        except Exception as e:
            kategorize_sonuclar[kategori] = [{"baslik": "Hata", "url": "#", "snippet": str(e)}]
            
    return kategorize_sonuclar


st.title("🛡️ AdShield 360° - Reklam ve Mevzuat Denetim Platformu")

# --- PANELLER (SEKMELER) ---
# Senin bahsettiğin diğer panelleri koruyan 3'lü sekme yapısı
panel1, panel2, panel3 = st.tabs([
    "📡 1. Canlı Pazar Radarı (Link Avı)", 
    "📸 2. Çok Modlu Denetçi (Görsel & Video)", 
    "📄 3. Raporlama ve Mevzuat Ayarları"
])

# ==========================================
# PANEL 1: CANLI PAZAR RADARI (LİNK AVI)
# ==========================================
with panel1:
    st.markdown("### 🎯 Hedefli Link ve Metin Tarama")
    st.markdown("Bot engellerine takılmamak için görseller indirilmez. Sadece hedef platformlardaki (Resmi site, Pazaryeri, Instagram) ürün linkleri ve metinleri listelenir.")
    
    with st.form("arama_formu"):
        col1, col2 = st.columns(2)
        with col1:
            urun_sorgusu = st.text_input("Hedef Ürün Adı:", value="mamaaura çatlak ve selülit yağı")
        with col2:
            marka_domaini = st.text_input("Marka Domaini (Örn: mamaaura.com):", value="mamaaura.com")
            
        calistir_butonu = st.form_submit_button("🚀 Hedef Linkleri Topla")

    if calistir_butonu:
        if urun_sorgusu and marka_domaini:
            with st.spinner("Gelişmiş radar çalışıyor, platformlar taranıyor..."):
                sonuclar = gelismis_coklu_hedef_taramasi(urun_sorgusu, marka_domaini, SERPAPI_KEY)
                st.success("✅ Hedef link havuzu başarıyla oluşturuldu!")
                
                # Bulunan sonuçları alt sekmelerde göster
                alt_sekmeler = st.tabs(list(sonuclar.keys()))
                for i, kategori in enumerate(sonuclar.keys()):
                    with alt_sekmeler[i]:
                        linkler = sonuclar[kategori]
                        if len(linkler) > 0:
                            st.info(f"**{len(linkler)}** adet bağlantı bulundu.")
                            for idx, item in enumerate(linkler, 1):
                                st.markdown(f"**{idx}. [{item['baslik']}]({item['url']})**")
                                st.caption(item['snippet'])
                        else:
                            st.warning("Bu kategoride sonuç bulunamadı.")
        else:
            st.error("Lütfen tüm alanları doldurun.")


# ==========================================
# PANEL 2: ÇOK MODLU DENETÇİ (REZERVE ALAN)
# ==========================================
with panel2:
    st.markdown("### 📸 Çok Modlu Denetçi (Görsel ve Video İnceleme)")
    st.info("Bu panel, tespit edilen riskli linklerdeki görsellerin, ekran görüntülerinin veya videoların manuel/yarı-otomatik olarak yüklenip Gemini Pro ile incelenmesi için ayrılmıştır.")
    
    # Burası senin daha sonra geliştireceğin yapı için hazır bırakıldı
    st.file_uploader("Şüpheli Görsel veya Videoyu Yükleyin (Geliştirme Aşamasında)", type=["jpg", "png", "mp4"])
    st.button("Görseli Mevzuat Kapsamında Analiz Et (Pasif)")


# ==========================================
# PANEL 3: RAPORLAMA VE AYARLAR (REZERVE ALAN)
# ==========================================
with panel3:
    st.markdown("### 📄 Rapor Arşivi ve Sistem Ayarları")
    st.info("Oluşturulan 360° Çoklu Satıcı Risk Raporları (PDF formatında) ve TİTCK/6502 sayılı Kanun prompt ayarları bu panelden yönetilecektir.")
    
    # Placeholder içerikler
    st.selectbox("Mevzuat Çerçevesi Seçin:", ["TİTCK Kozmetik Yönetmeliği", "6502 Reklam Kurulu İçtihatları", "Genel Sağlık Beyanı Denetimi"])
    st.button("Geçmiş Raporları Görüntüle (Pasif)")
