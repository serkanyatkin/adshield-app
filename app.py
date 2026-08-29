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
import time
import json
import base64
import textwrap

st.set_page_config(
    page_title="AdShield | Reklam Mevzuatı & Risk Denetim Platformu",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------- CANLI KUYRUK YÖNETİMİ (TOPLU) -----------------
def eklenti_verilerini_getir():
    try:
        u_url = st.secrets.get("UPSTASH_REDIS_REST_URL")
        u_token = st.secrets.get("UPSTASH_REDIS_REST_TOKEN")
        if not u_url or not u_token: 
            return []
            
        headers = {"Authorization": f"Bearer {u_token}"}
        res = requests.get(f"{u_url}/lrange/adshield_queue/0/-1", headers=headers, timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            raw_list = data.get("result", [])
            if raw_list:
                requests.get(f"{u_url}/del/adshield_queue", headers=headers, timeout=3)
                islenmis_liste = []
                for item in raw_list:
                    parsed = json.loads(item)
                    if isinstance(parsed, str): 
                        parsed = json.loads(parsed)
                    islenmis_liste.append(parsed)
                return islenmis_liste
    except Exception as e:
        print(f"Toplu okuma hatası: {e}")
    return []

# ----------------- ÇOKLU ÇIKTI OLUŞTURUCULAR -----------------
def create_docx(vaka_listesi):
    doc = docx.Document()
    for idx, veri in enumerate(vaka_listesi, 1):
        doc.add_heading(f'Vaka Tespit Raporu #{idx}', level=1)
        if veri.get("url"): 
            doc.add_paragraph(f"Kaynak Bağlantı: {veri['url']}")
        if veri.get("gorsel"):
            try:
                img_io = io.BytesIO()
                veri["gorsel"].save(img_io, format="PNG")
                img_io.seek(0)
                doc.add_picture(img_io, width=Inches(6.0))
            except:
                pass
        doc.add_paragraph(veri.get("rapor", "Rapor oluşturulamadı."))
        if idx < len(vaka_listesi): 
            doc.add_page_break()
    docx_io = io.BytesIO()
    doc.save(docx_io)
    return docx_io.getvalue()

def create_pdf(vaka_listesi, baslik_metni="AdShield Denetim Raporu"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    for idx, veri in enumerate(vaka_listesi, 1):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"{baslik_metni} - Vaka #{idx}", ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        
        if veri.get("url"): 
            # URL'leri 60 karakterde bir zorla kesiyoruz
            guvenli_url = textwrap.fill(veri['url'], width=60, break_long_words=True)
            pdf.multi_cell(0, 6, f"Kaynak:\n{guvenli_url}")
            pdf.ln(3)
            
        if veri.get("gorsel"):
            try:
                temp_img = f"temp_adshield_{int(time.time())}_{idx}.png"
                veri["gorsel"].save(temp_img, format="PNG")
                pdf.image(temp_img, w=170)
                os.remove(temp_img)
            except:
                pdf.multi_cell(0, 6, "[Görsel PDF'e basılamadı]")
            
        pdf.ln(5)
        rapor_metni = veri.get("rapor", "")
        
        # Fazla uzun Markdown çizgilerini temizle
        rapor_metni = re.sub(r'[-*_]{4,}', '---', rapor_metni)
        
        for line in rapor_metni.split('\n'):
            # 50 karakteri geçen tüm boşluksuz kelimeleri böl
            line = re.sub(r'(\S{50})', r'\1 ', line)
            
            # Satırları garanti olması için maksimum 65 karakter genişliğinde sar
            sarmalanmis_satirlar = textwrap.wrap(line, width=65, break_long_words=True)
            
            if not sarmalanmis_satirlar:
                pdf.ln(5)
                continue
                
            for p_line in sarmalanmis_satirlar:
                guvenli_metin = p_line.encode('latin-1', 'replace').decode('latin-1')
                
                # ZIRH (HATA YAKALAMA): Eğer FPDF bu satırda milimetrik genişlik hatası verirse çökmesini engelle
                try:
                    pdf.multi_cell(0, 6, guvenli_metin)
                except Exception:
                    try:
                        # Eğer çok uzun geldiyse zorla kısaltıp bas
                        pdf.multi_cell(0, 6, guvenli_metin[:40] + "...")
                    except:
                        pass # Eğer hala hata veriyorsa satırı atla, ancak PDF'i ASLA çökertme
                        
    return bytes(pdf.output())

# Sayfa İçi Akıllı Kaydırma
def trigger_scroll(position="top"):
    components.html(f"<script>setTimeout(() => window.scrollTo(0, 0), 200);</script>", height=0, width=0)

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

def optimize_image(img, max_dimension=2000):
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
    single_master_prompt = f"""{system_instruction_base}
GÖREVİN: Aşağıdaki materyali tek seferde, eşzamanlı olarak hem KATI BİR MEVZUAT BAŞDENETÇİSİ hem de KIDEMLİ BİR HAKSIZ REKABET AVUKATI şapkalarıyla incelemek ve bana doğrudan KUSURSUZ, HARMANLANMIŞ BİR {rapor_turu_adi} üretmektir.
KESİN KURALLAR:
1. "KİME:", "HAZIRLAYAN:", "KONU:" gibi bürokratik giriş antetlerini ASLA KULLANMA. 
2. Emsal Kararlarda "L'Oreal", "La Roche-Posay" tekrarlarından kaçın.
3. Raporu şık bir Markdown düzeninde oluştur.
4. Görsel üzerinde ambalaj, mg, enjektör gibi "tıbbi cihaz" işaretleri varsa asla kozmetik muamelesi yapma."""
    
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
            if "429" in err_str and attempt < 1:
                yield "\n\n> ⏳ Sistem duraklatıldı, 15 saniye içinde devam edecek...\n\n"
                time.sleep(15)
                continue 
            yield f"\nSentezleme hatası: {err_str}"
            return

def analiz_et_tekil(gorsel, url, sektor, mecra):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name=TARGET_MODEL)
    prompt = f"SEN UZMAN REKLAM HUKUKU BAŞDENETÇİSİSİN. Sektör: {sektor} | Mecra: {mecra} | URL: {url}\nLütfen görseli incele, mevzuat uyumunu analiz et ve riskleri listele. Antet kullanma."
    try:
        res = model.generate_content([prompt, gorsel])
        return res.text
    except Exception as e:
        return f"Hata oluştu: {e}"

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
            if not link.startswith("http") or any(y in url_lower for y in yasakli): 
                continue
            link_havuzu.append({"baslik": title, "url": link, "snippet": snippet})
        return kategori, link_havuzu
    except Exception as e: 
        return kategori, [{"baslik": "⚠️ HATA", "url": "#", "snippet": str(e)}]

def gelismis_coklu_hedef_taramasi(urun_adi, marka_domain, api_key_val):
    if not api_key_val or not urun_adi.strip(): 
        return {}
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

# Session States
for k in ["rapor_sonucu", "dilekce_sonucu", "analiz_gorselleri", "radar_link_sonuclari", "eklenti_img", "eklenti_url"]:
    if k not in st.session_state: 
        st.session_state[k] = None
        
if "vaka_havuzu" not in st.session_state: 
    st.session_state.vaka_havuzu = []

st.markdown('<div class="mode-header-title" lang="tr">İnceleme Modunu Seçiniz</div>', unsafe_allow_html=True)
mod_secimi = st.radio("Denetim Modu", [
    "Kurumsal Kampanya Taslağı Uyum Denetimi (İç Denetim & Revizyon Modu)",
    "Piyasa ve Rakip Reklam İncelemesi (Haksız Rekabet & Şikayet Modu)",
    "360° Çoklu Satıcı ve Pazar Radarı (Hedefli Ürün Linki Tespiti)"
], horizontal=True, label_visibility="collapsed")

is_danisan = "İç Denetim" in mod_secimi
is_radar = "360° Çoklu Satıcı" in mod_secimi

sol_kolon, sag_kolon = st.columns([1, 1.25], gap="large")

# ----------------- MOD 1 & 2: TEKİL İNCELEME -----------------
if not is_radar:
    with sol_kolon:
        with st.container(border=True):
            st.markdown(f'<div class="section-heading" lang="tr">1. Parametreler & Veri Yükleme</div>', unsafe_allow_html=True)

            if st.button("📥 Eklentiden Son Görüntüyü Al (Tekil İşlem)", use_container_width=True):
                with st.spinner("Kuyruktan veri alınıyor..."):
                    gelen_liste = eklenti_verilerini_getir()
                    if gelen_liste:
                        son_item = gelen_liste[-1]
                        st.session_state.eklenti_url = son_item.get('url', '')
                        b64_img = son_item.get('image', '').split(',')[1] if ',' in son_item.get('image', '') else son_item.get('image', '')
                        b64_img = b64_img.strip().replace('\n', '').replace('\r', '')
                        b64_img += '=' * ((4 - len(b64_img) % 4) % 4)
                        st.session_state.eklenti_img = Image.open(io.BytesIO(base64.b64decode(b64_img))).convert("RGB")
                        st.rerun()
                    else:
                        st.warning("Kuyrukta veri bulunamadı.")

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

            sektor = st.selectbox("Faaliyet Sektörü", ["Kozmetik & Kişisel Bakım / Anne-Bebek", "Takviye Edici Gıda & Sağlık", "E-Ticaret", "Diğer"])
            mecra = st.selectbox("Yayınlanacak Mecra", ["İnternet / Sosyal Medya", "Satış Noktası", "Televizyon", "Açık Hava"])
            reklam_url = st.text_input("Web Sayfası / Ürün Linki", value=reklam_url_default)
            reklam_metni = st.text_area("Reklam Metni / Ticari İddialar", height=90)
            analiz_butonu = st.button("Analizi Başlat", type="primary")

    with sag_kolon:
        with st.container(border=True):
            st.markdown(f'<div class="section-heading" lang="tr">2. Denetim Raporu & Çıktılar</div>', unsafe_allow_html=True)
            
            if analiz_butonu:
                trigger_scroll("top")
                st.session_state.analiz_gorselleri = []
                if st.session_state.eklenti_img: 
                    st.session_state.analiz_gorselleri.append(st.session_state.eklenti_img)
                
                birlestirilmis_metin = f"{reklam_metni}\n\n[Link]: {reklam_url}"
                sistem_metodolojisi = f"SEN UZMAN REKLAM HUKUKU BAŞDENETÇİSİSİN. Veriler: Sektör: {sektor} | Mecra: {mecra} | İddialar: {birlestirilmis_metin}"
                base_prompt = sistem_metodolojisi + "\n### I. MEVZUAT UYUM ANALİZİ\n### II. ÖNGÖRÜLEN CEZA"
                icerik_listesi = [f"Metin: {birlestirilmis_metin}"] + st.session_state.analiz_gorselleri

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

# ----------------- MOD 3: 360 DERECE RADAR & TOPLU İŞLEM -----------------
else:
    with sol_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">📡 Pazar Radarı</div>', unsafe_allow_html=True)
            radar_urun = st.text_input("Marka / Ürün Anahtar Kelimesi", value="incia bebek yağı")
            radar_tara_butonu = st.button("🚀 Hedef Linkleri Tespit Et", type="primary")
            
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">📥 Toplu Görüntü Havuzu (Batch Processing)</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Tüm Kuyruğu Al", use_container_width=True):
                    with st.spinner("Kuyruk boşaltılıyor..."):
                        gelen_liste = eklenti_verilerini_getir()
                        if gelen_liste:
                            for item in gelen_liste:
                                b64_img = item.get('image', '').split(',')[1] if ',' in item.get('image', '') else item.get('image', '')
                                b64_img = b64_img.strip().replace('\n', '').replace('\r', '')
                                b64_img += '=' * ((4 - len(b64_img) % 4) % 4)
                                img = Image.open(io.BytesIO(base64.b64decode(b64_img))).convert("RGB")
                                st.session_state.vaka_havuzu.append({"url": item.get('url', ''), "gorsel": img, "rapor": None})
                            st.success(f"🎯 {len(gelen_liste)} yeni görüntü havuza eklendi!")
                            st.rerun()
                        else: 
                            st.warning("Kuyrukta veri bulunamadı.")
            with col2:
                if st.button("🧹 Havuzu Temizle", use_container_width=True):
                    st.session_state.vaka_havuzu = []
                    st.rerun()

            if st.session_state.vaka_havuzu:
                st.write(f"**Havuzdaki Vaka Sayısı: {len(st.session_state.vaka_havuzu)}**")
                s_sektor = st.selectbox("Toplu Analiz İçin Sektör", ["Kozmetik & Kişisel Bakım", "Takviye Edici Gıda", "E-Ticaret"])
                s_mecra = st.selectbox("Toplu Analiz İçin Mecra", ["İnternet", "Televizyon", "Açık Hava"])
                
                if st.button("🚀 Tüm Havuzu Analiz Et", type="primary"):
                    progress_text = "Vakalar analiz ediliyor..."
                    my_bar = st.progress(0, text=progress_text)
                    for i, vaka in enumerate(st.session_state.vaka_havuzu):
                        vaka["rapor"] = analiz_et_tekil(vaka["gorsel"], vaka["url"], s_sektor, s_mecra)
                        my_bar.progress((i + 1) / len(st.session_state.vaka_havuzu), text=f"İşleniyor: {i+1}/{len(st.session_state.vaka_havuzu)}")
                    st.success("Tüm analizler tamamlandı!")
                    st.rerun()

    with sag_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">📋 Analiz Sonuçları & Linkler</div>', unsafe_allow_html=True)
            
            if radar_tara_butonu:
                with st.spinner("Taranıyor..."): 
                    st.session_state.radar_link_sonuclari = gelismis_coklu_hedef_taramasi(radar_urun, "", serpapi_key)
            
            if st.session_state.radar_link_sonuclari:
                st.success("Linkler bulundu. Tıklayıp eklenti ile kuyruğa gönderebilirsiniz.")
                alt_sekmeler = st.tabs(list(st.session_state.radar_link_sonuclari.keys()))
                for i, (kat, links) in enumerate(st.session_state.radar_link_sonuclari.items()):
                    with alt_sekmeler[i]:
                        for idx, item in enumerate(links, 1): 
                            st.markdown(f"**{idx}. [{item['baslik']}]({item['url']})**")
                st.divider()

            if st.session_state.vaka_havuzu:
                st.markdown("**🔍 Toplu Denetim Raporları**")
                for idx, vaka in enumerate(st.session_state.vaka_havuzu, 1):
                    with st.expander(f"Vaka #{idx} - {vaka['url'][:50]}..."):
                        st.image(vaka["gorsel"], width=200)
                        if vaka["rapor"]: 
                            st.markdown(vaka["rapor"])
                        else: 
                            st.info("Henüz analiz edilmedi.")
                            
                if any(v.get("rapor") for v in st.session_state.vaka_havuzu):
                    col_pdf, col_word = st.columns(2)
                    with col_pdf:
                        pdf_bytes = create_pdf(st.session_state.vaka_havuzu)
                        st.download_button("⬇️ PDF İndir", data=pdf_bytes, file_name="adshield_toplu.pdf", mime="application/pdf", use_container_width=True)
                    with col_word:
                        word_bytes = create_docx(st.session_state.vaka_havuzu)
                        st.download_button("⬇️ Word İndir", data=word_bytes, file_name="adshield_toplu.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
