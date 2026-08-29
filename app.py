import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime
import os
import glob
import re
import requests
import io
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import textwrap
import time
import json
import base64

st.set_page_config(
    page_title="AdShield | Reklam Mevzuatı & Risk Denetim Platformu",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------- CANLI KUYRUK YÖNETİMİ (UPSTASH REST API) -----------------
def eklenti_verisini_getir():
    """Upstash Redis üzerinden eklentiden gelen en son görsel ve URL verisini çeker."""
    try:
        u_url = st.secrets.get("UPSTASH_REDIS_REST_URL")
        u_token = st.secrets.get("UPSTASH_REDIS_REST_TOKEN")
        if not u_url or not u_token:
            return None
            
        headers = {"Authorization": f"Bearer {u_token}"}
        res = requests.get(f"{u_url}/get/adshield_latest", headers=headers, timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            raw_result = data.get("result")
            if raw_result:
                # Veriyi aldıktan sonra kuyruktan temizle
                requests.get(f"{u_url}/del/adshield_latest", headers=headers, timeout=3)
                
                # Çift stringify sorununu çözen akıllı parse işlemi
                parsed = json.loads(raw_result)
                if isinstance(parsed, str):
                    parsed = json.loads(parsed)
                return parsed
    except Exception as e:
        print(f"Kuyruk okuma hatası: {e}")
    return None

# Sayfa İçi Akıllı Kaydırma Fonksiyonu
def trigger_scroll(position="top"):
    components.html(f"""
    <script>
        setTimeout(() => {{
            try {{
                const p = window.parent;
                const doc = p ? p.document : document;
                const container = doc.querySelector('[data-testid="stAppViewContainer"]') || 
                                  doc.querySelector('section.main') || 
                                  doc.documentElement || 
                                  doc.body;
                if ("{position}" === "bottom") {{
                    if (container) container.scrollTo({{ top: container.scrollHeight + 3000, behavior: 'smooth' }});
                }} else if ("{position}" === "top") {{
                    if (container) container.scrollTo({{ top: 0, behavior: 'smooth' }});
                }}
            }} catch(e) {{}}
        }}, 200);
    </script>
    """, height=0, width=0)

# Kurumsal Tema Stilleri
st.markdown("""
<div id="page-top-anchor"></div>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .block-container { max-width: 1200px !important; padding-top: 1.2rem !important; margin: 0 auto !important; }
    .firm-header { background-color: #5D728B; padding: 18px 26px; border-radius: 6px; color: #ffffff; display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; box-shadow: 0 4px 14px rgba(93, 114, 139, 0.18); }
    .firm-title { font-family: 'Cinzel', serif; font-size: 19px; letter-spacing: 1.5px; font-weight: 700; }
    .firm-subtitle { font-size: 11px; letter-spacing: 1px; color: #DCE4EC; margin-top: 2px; }
    .firm-badge { background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255, 255, 255, 0.3); color: #ffffff; font-size: 11px; font-weight: 600; padding: 5px 12px; border-radius: 4px; }
    .mode-header-title { text-align: center; font-family: 'Cinzel', serif; font-size: 13.5px; letter-spacing: 1.5px; color: #2C3848; font-weight: 700; margin-bottom: 10px; text-transform: uppercase; }
    div[data-testid="stRadio"] > div[role="radiogroup"] { display: flex; justify-content: center; gap: 14px; width: 100%; margin-bottom: 10px; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label { flex: 1; background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 6px; padding: 12px 18px; cursor: pointer; text-align: center; display: flex; align-items: center; justify-content: center; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover { border-color: #5D728B; background: #F8FAFC; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) { border-color: #5D728B !important; background-color: #F1F5F9 !important; box-shadow: 0 0 0 1px #5D728B, 0 3px 8px rgba(93, 114, 139, 0.12) !important; font-weight: 600 !important; color: #1E293B !important; }
    .section-heading { font-family: 'Cinzel', serif; font-size: 13.5px; letter-spacing: 1px; color: #2C3848; font-weight: 700; margin-bottom: 12px; border-bottom: 2px solid #E2E8F0; padding-bottom: 5px; }
    .stButton button[kind="primary"] { background-color: #5D728B !important; color: #ffffff !important; border-radius: 4px !important; border: 1px solid #4D6076 !important; padding: 10px 20px !important; font-weight: 600 !important; width: 100%; transition: all 0.2s ease; }
    .stButton button[kind="primary"]:hover { background-color: #4A5E74 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="firm-header" lang="tr">
    <div>
        <div class="firm-title">ADSHIELD COMPLIANCE</div>
        <div class="firm-subtitle">Reklam Kurulu İçtihat & Kurumsal Risk Denetim Sistemi</div>
    </div>
    <div class="firm-badge">Kurumsal Regülasyon & Denetim Motoru</div>
</div>
""", unsafe_allow_html=True)

try:
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    serpapi_key = st.secrets.get("SERPAPI_API_KEY", None)
except Exception:
    api_key = None
    serpapi_key = None

with st.sidebar:
    st.header("Sistem Ayarları")
    api_key = st.text_input("Gemini API Key:", value=api_key or "", type="password")
    serpapi_key = st.text_input("SerpApi Key:", value=serpapi_key or "", type="password")
    st.caption("ℹ️ Canlı Upstash Redis bulut köprüsü aktiftir.")

def optimize_image(img, max_dimension=2500):
    img = img.convert("RGB")
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return img

TARGET_MODEL = "gemini-3.6-flash"

def get_working_model(system_instruction=None):
    if not api_key:
        raise Exception("API anahtarı bulunamadı.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name=TARGET_MODEL, system_instruction=system_instruction)

def generate_multi_role_synthesis_stream(contents, system_instruction_base, is_danisan):
    if not api_key:
        raise Exception("API anahtarı bulunamadı.")
    genai.configure(api_key=api_key)
    
    rapor_turu_adi = "Mevzuat Uyum ve Revizyon Raporu" if is_danisan else "Piyasa İhlal ve Şikayet Raporu"
    
    single_master_prompt = f"""
{system_instruction_base}

GÖREVİN: Aşağıdaki materyali tek seferde, eşzamanlı olarak hem KATI BİR MEVZUAT BAŞDENETÇİSİ hem de KIDEMLİ BİR HAKSIZ REKABET AVUKATI şapkalarıyla incelemek ve bana doğrudan KUSURSUZ, HARMANLANMIŞ BİR {rapor_turu_adi} üretmektir.

KESİN KURALLAR:
1. "KİME:", "HAZIRLAYAN:", "KONU:" gibi bürokratik giriş antetlerini ASLA KULLANMA. 
2. Emsal Kararlarda "L'Oreal", "La Roche-Posay" tekrarlarından kaçın.
3. Raporu şık bir Markdown düzeninde oluştur.
4. Görsel üzerinde ambalaj, mg, enjektör gibi "tıbbi cihaz" işaretleri varsa asla kozmetik muamelesi yapma, Yönetmelik m. 15 üzerinden doğrudan tıbbi cihaz ihlali olarak denetle.
"""
    payload = [single_master_prompt] + contents
    model = get_working_model()
    
    for attempt in range(2):
        try:
            response = model.generate_content(payload, stream=False, generation_config=genai.types.GenerationConfig(temperature=0.0))
            if response and response.text:
                words = response.text.split(' ')
                for i in range(0, len(words), 6):
                    yield ' '.join(words[i:i+6]) + ' '
                    time.sleep(0.04) 
                return 
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                if attempt < 1:
                    yield "\n\n> ⏳ **[Google Limit Koruması]** Sistem duraklatıldı, 15 saniye içinde devam edecek...\n\n"
                    time.sleep(15)
                    continue 
                else:
                    yield "\n\n🚨 **API KOTASI TÜKENDİ**"
                    return
            yield f"\nSentezleme hatası: {err_str}"
            return

def tekil_sorgu_at(kategori, sorgu, api_key_val):
    url = f"https://serpapi.com/search.json?q={urllib.parse.quote(sorgu)}&api_key={api_key_val}&engine=google&gl=tr&hl=tr&num=20"
    try:
        response = requests.get(url, timeout=20)
        data = response.json()
        if "error" in data:
            return kategori, [{"baslik": "⚠️ API HATASI", "url": "#", "snippet": data['error']}]
        link_havuzu = []
        for result in data.get("organic_results", []):
            link = result.get("link", "")
            title = result.get("title", "Başlık Belirtilmemiş")
            snippet = result.get("snippet", "")
            url_lower = link.lower()
            yasakli = ["/giris", "/hesabim", "/sepetim", "auth", "login", "/sr?q=", "/sr", "/ara?q", "kategori", "/magaza/", "tum-urunler", "/search", "/arama"]
            if not link.startswith("http") or any(y in url_lower for y in yasakli): continue
            link_havuzu.append({"baslik": title, "url": link, "snippet": snippet})
        return kategori, link_havuzu
    except Exception as e:
        return kategori, [{"baslik": "⚠️ HATA", "url": "#", "snippet": str(e)}]

def gelismis_coklu_hedef_taramasi(urun_adi, marka_domain, api_key_val):
    if not api_key_val or not urun_adi.strip(): return {}
    t = urun_adi.strip()
    queries = {
        "📸 Instagram": f'site:instagram.com/p/ {t}',
        "🛒 Pazaryeri Ürünleri": f'(site:trendyol.com OR site:hepsiburada.com) {t} -inurl:sr -inurl:ara -inurl:kategori -inurl:magaza',
        "📦 Diğer E-Ticaret": f'{t} sipariş OR satın al -inurl:arama -inurl:search -inurl:kategori'
    }
    kategorize_sonuclar = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(tekil_sorgu_at, kat, q, api_key_val) for kat, q in queries.items()]
        for f in futures:
            kat, sonuclar = f.result()
            gorulenler = set()
            tekil_list = []
            for item in sonuclar:
                if item["url"] not in gorulenler:
                    gorulenler.add(item["url"])
                    tekil_list.append(item)
            kategorize_sonuclar[kat] = tekil_list
    return kategorize_sonuclar

def get_relevant_emsaller(metin, sektor, top_k=2):
    return "Emsal karar havuzu aktif.", ["1. Emsal Karar Özeti (Örnek)"]

def generate_content_safe_text(contents):
    if not api_key:
        return "API anahtarı eksik."
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name=TARGET_MODEL)
    res = model.generate_content(contents)
    return res.text if res else "Hata."

# Session States
for k in ["rapor_sonucu", "dilekce_sonucu", "chat_history", "analiz_gorselleri", "radar_link_sonuclari", "eklenti_img", "eklenti_url"]:
    if k not in st.session_state: st.session_state[k] = None

st.markdown('<div class="mode-header-title" lang="tr">İnceleme Modunu Seçiniz</div>', unsafe_allow_html=True)
mod_secimi = st.radio("Denetim Modu", [
    "Kurumsal Kampanya Taslağı Uyum Denetimi (İç Denetim & Revizyon Modu)",
    "Piyasa ve Rakip Reklam İncelemesi (Haksız Rekabet & Şikayet Modu)",
    "360° Çoklu Satıcı ve Pazar Radarı (Hedefli Ürün Linki Tespiti)"
], horizontal=True, label_visibility="collapsed")

is_danisan = "İç Denetim" in mod_secimi
is_radar = "360° Çoklu Satıcı" in mod_secimi

sol_kolon, sag_kolon = st.columns([1, 1.25], gap="large")

if not is_radar:
    with sol_kolon:
        with st.container(border=True):
            st.markdown(f'<div class="section-heading" lang="tr">1. Parametreler & Veri Yükleme</div>', unsafe_allow_html=True)

            reklam_url_default = ""
            if st.session_state.eklenti_img:
                st.success("🎯 Yakalanan Görüntü Analize Hazır!")
                st.image(st.session_state.eklenti_img, caption="Analiz Edilecek Görsel", use_container_width=True)
                reklam_url_default = st.session_state.get("eklenti_url", "")
                if st.button("🧹 Görüntüyü Temizle"):
                    st.session_state.eklenti_img = None
                    st.session_state.eklenti_url = ""
                    st.rerun()
                st.divider()

            sektor = st.selectbox("Faaliyet Sektörü", ["Kozmetik & Kişisel Bakım / Anne-Bebek", "Takviye Edici Gıda & Sağlık", "E-Ticaret & İndirim Kampanyaları", "Sosyal Medya & Influencer Reklamları", "Diğer"])
            mecra = st.selectbox("Yayınlanacak Mecra", ["İnternet / Sosyal Medya", "Satış Noktası", "Ulusal Televizyon Kanalı", "Açık Hava (Billboard)"])
            
            reklam_url = st.text_input("Web Sayfası / Ürün Linki", value=reklam_url_default)
            reklam_metni = st.text_area("Reklam Metni / Ticari İddialar", height=90)
            yuklenen_gorseller = st.file_uploader("Ek Görseller (Opsiyonel)", type=["jpg", "png"], accept_multiple_files=True)
            
            analiz_butonu = st.button("Analizi Başlat", type="primary")

    with sag_kolon:
        with st.container(border=True):
            st.markdown(f'<div class="section-heading" lang="tr">2. Denetim Raporu & Çıktılar</div>', unsafe_allow_html=True)
            
            if analiz_butonu:
                trigger_scroll("top")
                st.session_state.analiz_gorselleri = []
                
                if st.session_state.eklenti_img:
                    st.session_state.analiz_gorselleri.append(st.session_state.eklenti_img)
                
                if yuklenen_gorseller:
                    for g in yuklenen_gorseller: st.session_state.analiz_gorselleri.append(optimize_image(Image.open(g)))
                
                birlestirilmis_metin = f"{reklam_metni}\n\n[Link]: {reklam_url}"
                ilgili_emsaller, emsal_liste = get_relevant_emsaller(birlestirilmis_metin, sektor)
                
                sistem_metodolojisi = f"SEN UZMAN REKLAM HUKUKU BAŞDENETÇİSİSİN. Veriler: Sektör: {sektor} | Mecra: {mecra} | İddialar: {birlestirilmis_metin}"
                base_prompt = sistem_metodolojisi + "\n### I. MEVZUAT UYUM ANALİZİ\n### II. ÖNGÖRÜLEN CEZA"
                
                icerik_listesi = [f"Metin: {birlestirilmis_metin}"]
                icerik_listesi.extend(st.session_state.analiz_gorselleri)

                rapor_alani = st.empty()
                try:
                    tam_rapor = ""
                    with st.spinner("AI Sentez Motoru Çalışıyor..."):
                        for parca in generate_multi_role_synthesis_stream(icerik_listesi, base_prompt, is_danisan):
                            tam_rapor += parca
                            rapor_alani.markdown(tam_rapor + "▌")
                    rapor_alani.empty()
                    st.session_state.rapor_sonucu = tam_rapor
                except Exception as err:
                    st.error(f"Sistem Hatası: {err}")

            if st.session_state.rapor_sonucu:
                with st.container(height=450):
                    st.markdown(st.session_state.rapor_sonucu)
                if not is_danisan:
                    if st.button("Resmi Reklam Kurulu Şikayet Dilekçesini Hazırla", type="primary"):
                        with st.spinner("Dilekçe yazılıyor..."):
                            st.session_state.dilekce_sonucu = generate_content_safe_text([st.session_state.rapor_sonucu + "\nBuna göre şikayet dilekçesi yaz."])
                            st.rerun()
                if st.session_state.dilekce_sonucu:
                    st.markdown(st.session_state.dilekce_sonucu)
            else:
                st.info("Rapor bu alanda oluşturulacaktır.")

else:
    with sol_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">📡 Pazar Radarı</div>', unsafe_allow_html=True)
            radar_urun = st.text_input("Marka / Ürün Anahtar Kelimesi", value="incia bebek yağı")
            radar_tara_butonu = st.button("🚀 Hedef Linkleri Tespit Et", type="primary")
            
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">📥 Yakalanan Reklamlar</div>', unsafe_allow_html=True)
            if st.button("📥 Eklentiden Gelen Yeni Görüntüyü Al", use_container_width=True):
                with st.spinner("Canlı kuyruktan veri alınıyor..."):
                    gelen_veri = eklenti_verisini_getir()
                    if gelen_veri:
                        st.session_state.eklenti_url = gelen_veri.get('url', '')
                        b64_img = gelen_veri.get('image', '')
                        if ',' in b64_img:
                            b64_img = b64_img.split(',')[1]
                        
                        b64_img = b64_img.strip().replace('\n', '').replace('\r', '')
                        missing_padding = len(b64_img) % 4
                        if missing_padding != 0:
                            b64_img += '=' * (4 - missing_padding)
                            
                        img_bytes = base64.b64decode(b64_img)
                        st.session_state.eklenti_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                        st.rerun()
                    else:
                        st.warning("Henüz eklentiden gönderilen yeni bir görüntü bulunamadı.")
            
            if st.session_state.eklenti_img:
                st.success("🎯 Görüntü başarıyla çekildi! Analiz için üst menüden 'Denetim Modu'na geçebilirsiniz.")
                st.image(st.session_state.eklenti_img, caption="Yakalanan Görsel", use_container_width=True)

    with sag_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">📋 Tespit Edilen Linkler</div>', unsafe_allow_html=True)
            if radar_tara_butonu:
                with st.spinner("Taranıyor..."):
                    st.session_state.radar_link_sonuclari = gelismis_coklu_hedef_taramasi(radar_urun, "", serpapi_key)
            
            if st.session_state.radar_link_sonuclari:
                toplam_link = sum(len(v) for v in st.session_state.radar_link_sonuclari.values())
                st.success(f"🎯 Toplam {toplam_link} bağlantı bulundu. Linke tıklayıp eklenti ile AdShield'a gönderebilirsiniz.")
                alt_sekmeler = st.tabs(list(st.session_state.radar_link_sonuclari.keys()))
                for i, (kat, links) in enumerate(st.session_state.radar_link_sonuclari.items()):
                    with alt_sekmeler[i]:
                        for idx, item in enumerate(links, 1):
                            st.markdown(f"**{idx}. [{item['baslik']}]({item['url']})**")
                            st.divider()
