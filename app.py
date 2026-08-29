import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from PIL import Image
import docx
from docx.shared import Inches, Pt
import os
import requests
import io
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import time
import json
import base64

st.set_page_config(page_title="AdShield | Kurumsal Denetim", layout="wide", initial_sidebar_state="collapsed")

def eklenti_verilerini_getir():
    try:
        u_url = st.secrets.get("UPSTASH_REDIS_REST_URL")
        u_token = st.secrets.get("UPSTASH_REDIS_REST_TOKEN")
        if not u_url or not u_token: return []
            
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
                    if isinstance(parsed, str): parsed = json.loads(parsed)
                    islenmis_liste.append(parsed)
                return islenmis_liste
    except Exception:
        pass
    return []

# ----------------- AKILLI WORD (DOCX) OLUŞTURUCU -----------------
def create_docx(vaka_listesi):
    doc = docx.Document()
    
    # Varsayılan font ayarlarını daha kurumsal yapalım
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)

    for idx, veri in enumerate(vaka_listesi, 1):
        # Vaka Ana Başlığı
        doc.add_heading(f'Vaka Tespit Raporu #{idx}', level=1)
        
        # Link Alanı (Tıklanabilir ve belirgin)
        if veri.get("url"): 
            p_url = doc.add_paragraph()
            p_url.add_run("Kaynak Bağlantı: ").bold = True
            p_url.add_run(veri['url'])
            
        # Görsel Alanı (Boyutu optimize edildi)
        if veri.get("gorsel"):
            try:
                img_io = io.BytesIO()
                veri["gorsel"].save(img_io, format="PNG")
                img_io.seek(0)
                doc.add_picture(img_io, width=Inches(5.0))
            except:
                pass
                
        rapor_metni = veri.get("rapor", "Rapor oluşturulamadı.")
        
        # --- MARKDOWN AYRIŞTIRICI (PARSER) ---
        for line in rapor_metni.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Ayıraç Çizgileri
            if line.startswith('---'):
                p = doc.add_paragraph()
                p.add_run('_' * 50)
                continue
            
            # Başlıkları Temizle ve Word Başlığına (Heading) Çevir
            if line.startswith('### '):
                doc.add_heading(line[4:].replace('**', ''), level=3)
                continue
            elif line.startswith('## '):
                doc.add_heading(line[3:].replace('**', ''), level=2)
                continue
            elif line.startswith('# '):
                doc.add_heading(line[2:].replace('**', ''), level=1)
                continue
            
            # Madde İmleri (Bullet Points) Algılayıcı
            if line.startswith('* '):
                p = doc.add_paragraph(style='List Bullet')
                line_content = line[2:]
            elif line.startswith('- '):
                p = doc.add_paragraph(style='List Bullet')
                line_content = line[2:]
            else:
                p = doc.add_paragraph()
                line_content = line
                
            # Kalın (Bold) Metinleri Ayır ve Word Formatına Çevir
            parts = line_content.split('**')
            for i, part in enumerate(parts):
                if not part: continue
                run = p.add_run(part)
                # Çift yıldızların arasındaki metinler kalın (bold) yapılır
                if i % 2 != 0:
                    run.bold = True
                    
        # Her yeni raporda yeni sayfaya geç
        if idx < len(vaka_listesi): 
            doc.add_page_break()
            
    docx_io = io.BytesIO()
    doc.save(docx_io)
    return docx_io.getvalue()

def trigger_scroll(position="top"):
    components.html(f"<script>setTimeout(() => window.scrollTo(0, 0), 200);</script>", height=0, width=0)

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
<div class="firm-header" lang="tr">
    <div><div class="firm-title">ADSHIELD COMPLIANCE</div><div class="firm-subtitle">Reklam Kurulu İçtihat & Kurumsal Risk Denetim Sistemi</div></div>
    <div class="firm-badge">Kurumsal Regülasyon & Denetim Motoru</div>
</div>
""", unsafe_allow_html=True)

try:
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    serpapi_key = st.secrets.get("SERPAPI_API_KEY", None)
except:
    api_key, serpapi_key = None, None

with st.sidebar:
    st.header("Sistem Ayarları")
    api_key = st.text_input("Gemini API Key:", value=api_key or "", type="password")
    serpapi_key = st.text_input("SerpApi Key:", value=serpapi_key or "", type="password")

TARGET_MODEL = "gemini-3.6-flash"

def get_working_model(system_instruction=None):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name=TARGET_MODEL, system_instruction=system_instruction)

def generate_multi_role_synthesis_stream(contents, system_instruction_base, is_danisan):
    genai.configure(api_key=api_key)
    rapor_turu_adi = "Mevzuat Uyum ve Revizyon Raporu" if is_danisan else "Piyasa İhlal ve Şikayet Raporu"
    single_master_prompt = f"""{system_instruction_base}
GÖREVİN: Aşağıdaki materyali tek seferde, eşzamanlı olarak hem KATI BİR MEVZUAT BAŞDENETÇİSİ hem de KIDEMLİ BİR HAKSIZ REKABET AVUKATI şapkalarıyla incelemek ve bana doğrudan KUSURSUZ, HARMANLANMIŞ BİR {rapor_turu_adi} üretmektir.
KESİN KURALLAR:
1. "KİME:", "HAZIRLAYAN:", "KONU:" gibi bürokratik giriş antetlerini ASLA KULLANMA. 
2. Emsal Kararlarda "L'Oreal", "La Roche-Posay" tekrarlarından kaçın.
3. Raporu şık bir Markdown düzeninde oluştur.
4. Görsel üzerinde ambalaj, mg, enjektör gibi "tıbbi cihaz" işaretleri varsa asla kozmetik muamelesi yapma."""
    
    model = get_working_model()
    for attempt in range(3):
        try:
            response = model.generate_content([single_master_prompt] + contents, stream=False)
            if response and response.text:
                words = response.text.split(' ')
                for i in range(0, len(words), 6):
                    yield ' '.join(words[i:i+6]) + ' '
                    time.sleep(0.04)
                return
        except Exception as e:
            if "429" in str(e) or "Quota" in str(e):
                yield f"\n\n> ⏳ API Kotası Doldu. Sistem {15 * (attempt+1)} saniye uykuya geçiyor...\n\n"
                time.sleep(15 * (attempt + 1))
                continue
            yield f"\nSentezleme hatası: {str(e)}"
            return

def analiz_et_tekil(gorsel, url, sektor, mecra):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name=TARGET_MODEL)
    prompt = f"SEN UZMAN REKLAM HUKUKU BAŞDENETÇİSİSİN. Sektör: {sektor} | Mecra: {mecra} | URL: {url}\nLütfen görseli incele, mevzuat uyumunu analiz et ve riskleri listele. Antet kullanma."
    
    for deneme in range(3):
        try:
            res = model.generate_content([prompt, gorsel])
            return res.text
        except Exception as e:
            hata = str(e)
            if "429" in hata or "Quota" in hata:
                time.sleep(15 * (deneme + 1))
                continue
            return f"Hata oluştu: {hata}"
    return "❌ Kritik Hata: API kotası aşıldı ve tüm yeniden deneme (retry) süreleri tükendi."

def tekil_sorgu_at(kategori, sorgu, api_key_val):
    url = f"https://serpapi.com/search.json?q={urllib.parse.quote(sorgu)}&api_key={api_key_val}&engine=google&gl=tr&hl=tr&num=20"
    try:
        response = requests.get(url, timeout=20)
        data = response.json()
        if "error" in data: return kategori, [{"baslik": "⚠️ API HATASI", "url": "#", "snippet": data['error']}]
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

for k in ["rapor_sonucu", "dilekce_sonucu", "analiz_gorselleri", "radar_link_sonuclari", "eklenti_img", "eklenti_url"]:
    if k not in st.session_state: st.session_state[k] = None
if "vaka_havuzu" not in st.session_state: st.session_state.vaka_havuzu = []

st.markdown('<div class="mode-header-title" lang="tr">İnceleme Modunu Seçiniz</div>', unsafe_allow_html=True)
mod_secimi = st.radio("Denetim Modu", ["Kurumsal Kampanya Taslağı Uyum Denetimi (İç Denetim & Revizyon Modu)", "Piyasa ve Rakip Reklam İncelemesi (Haksız Rekabet & Şikayet Modu)", "360° Çoklu Satıcı ve Pazar Radarı (Hedefli Ürün Linki Tespiti)"], horizontal=True, label_visibility="collapsed")
is_danisan = "İç Denetim" in mod_secimi
is_radar = "360° Çoklu Satıcı" in mod_secimi

sol_kolon, sag_kolon = st.columns([1, 1.25], gap="large")

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
            if st.session_state.eklenti_img:
                st.image(st.session_state.eklenti_img, caption="Analiz Edilecek Görsel", use_container_width=True)
                if st.button("🧹 Görüntüyü Temizle"):
                    st.session_state.eklenti_img, st.session_state.eklenti_url = None, ""
                    st.rerun()
                st.divider()
            sektor = st.selectbox("Faaliyet Sektörü", ["Kozmetik & Kişisel Bakım / Anne-Bebek", "Takviye Edici Gıda & Sağlık", "E-Ticaret", "Diğer"])
            mecra = st.selectbox("Yayınlanacak Mecra", ["İnternet / Sosyal Medya", "Satış Noktası", "Televizyon", "Açık Hava"])
            reklam_url = st.text_input("Web Sayfası / Ürün Linki", value=st.session_state.get("eklenti_url", ""))
            reklam_metni = st.text_area("Reklam Metni / Ticari İddialar", height=90)
            analiz_butonu = st.button("Analizi Başlat", type="primary")

    with sag_kolon:
        with st.container(border=True):
            st.markdown(f'<div class="section-heading" lang="tr">2. Denetim Raporu & Çıktılar</div>', unsafe_allow_html=True)
            if analiz_butonu:
                st.session_state.analiz_gorselleri = [st.session_state.eklenti_img] if st.session_state.eklenti_img else []
                icerik_listesi = [f"Metin: {reklam_metni}\n\n[Link]: {reklam_url}"] + st.session_state.analiz_gorselleri
                rapor_alani = st.empty()
                try:
                    tam_rapor = ""
                    with st.spinner("AI Sentez Motoru Çalışıyor..."):
                        for parca in generate_multi_role_synthesis_stream(icerik_listesi, f"SEN UZMAN REKLAM HUKUKU BAŞDENETÇİSİSİN. Sektör: {sektor} | Mecra: {mecra}", is_danisan):
                            tam_rapor += parca
                            rapor_alani.markdown(tam_rapor + "▌")
                    rapor_alani.empty()
                    st.session_state.rapor_sonucu = tam_rapor
                except Exception as err: st.error(f"Sistem Hatası: {err}")
            if st.session_state.rapor_sonucu:
                with st.container(height=450): st.markdown(st.session_state.rapor_sonucu)

else:
    with sol_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">📡 Pazar Radarı</div>', unsafe_allow_html=True)
            radar_urun = st.text_input("Marka / Ürün Anahtar Kelimesi", value="incia bebek yağı")
            radar_tara_butonu = st.button("🚀 Hedef Linkleri Tespit Et", type="primary")
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">📥 Toplu Görüntü Havuzu (Paralel İşleme)</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Tüm Kuyruğu Al", use_container_width=True):
                    gelen_liste = eklenti_verilerini_getir()
                    if gelen_liste:
                        for item in gelen_liste:
                            b64 = item.get('image', '').split(',')[-1].strip().replace('\n', '').replace('\r', '')
                            b64 += '=' * ((4 - len(b64) % 4) % 4)
                            st.session_state.vaka_havuzu.append({"url": item.get('url', ''), "gorsel": Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB"), "rapor": None})
                        st.rerun()
            with col2:
                if st.button("🧹 Havuzu Temizle", use_container_width=True):
                    st.session_state.vaka_havuzu = []
                    st.rerun()

            if st.session_state.vaka_havuzu:
                st.write(f"**Havuzdaki Vaka Sayısı: {len(st.session_state.vaka_havuzu)}**")
                s_sektor = st.selectbox("Toplu Analiz İçin Sektör", ["Kozmetik & Kişisel Bakım", "Takviye Edici Gıda", "E-Ticaret"])
                s_mecra = st.selectbox("Toplu Analiz İçin Mecra", ["İnternet", "Televizyon", "Açık Hava"])
                
                if st.button("🚀 Tüm Havuzu Paralel Analiz Et", type="primary"):
                    progress_text = "Vakalar çoklu iş parçacıklarıyla (Thread) analiz ediliyor..."
                    my_bar = st.progress(0, text=progress_text)
                    
                    with st.spinner("API sınırlarına karşı akıllı kalkan devrede..."):
                        with ThreadPoolExecutor(max_workers=3) as executor:
                            futures = [executor.submit(analiz_et_tekil, vaka["gorsel"], vaka["url"], s_sektor, s_mecra) for vaka in st.session_state.vaka_havuzu]
                            
                            for i, future in enumerate(futures):
                                st.session_state.vaka_havuzu[i]["rapor"] = future.result()
                                my_bar.progress((i + 1) / len(st.session_state.vaka_havuzu), text=f"Tamamlanan İşlem: {i+1}/{len(st.session_state.vaka_havuzu)}")
                                
                    st.success("Tüm eşzamanlı analizler tamamlandı!")
                    st.rerun()

    with sag_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">📋 Analiz Sonuçları & Linkler</div>', unsafe_allow_html=True)
            if radar_tara_butonu:
                st.session_state.radar_link_sonuclari = gelismis_coklu_hedef_taramasi(radar_urun, "", serpapi_key)
            if st.session_state.radar_link_sonuclari:
                alt_sekmeler = st.tabs(list(st.session_state.radar_link_sonuclari.keys()))
                for i, (kat, links) in enumerate(st.session_state.radar_link_sonuclari.items()):
                    with alt_sekmeler[i]:
                        for idx, item in enumerate(links, 1): st.markdown(f"**{idx}. [{item['baslik']}]({item['url']})**")
                st.divider()

            if st.session_state.vaka_havuzu:
                st.markdown("**🔍 Toplu Denetim Raporları**")
                for idx, vaka in enumerate(st.session_state.vaka_havuzu, 1):
                    with st.expander(f"Vaka #{idx} - {vaka['url'][:50]}..."):
                        st.image(vaka["gorsel"], width=200)
                        if vaka["rapor"]: st.markdown(vaka["rapor"])
                        else: st.info("Henüz analiz edilmedi.")
                            
                if any(v.get("rapor") for v in st.session_state.vaka_havuzu):
                    word_bytes = create_docx(st.session_state.vaka_havuzu)
                    st.download_button("⬇️ Tüm Raporları Word (DOCX) Olarak İndir", data=word_bytes, file_name="adshield_toplu_rapor.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
