import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from PIL import Image
import docx
from docx.shared import Inches, Pt
import requests
import io
import urllib.parse
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
    except: pass
    return []

def create_docx(vaka_listesi):
    doc = docx.Document()
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    for idx, veri in enumerate(vaka_listesi, 1):
        doc.add_heading(f'Vaka Tespit Raporu #{idx}', level=1)
        if veri.get("url"): 
            p_url = doc.add_paragraph()
            p_url.add_run("Kaynak Bağlantı: ").bold = True
            p_url.add_run(veri['url'])
        if veri.get("gorsel"):
            try:
                img_io = io.BytesIO()
                veri["gorsel"].save(img_io, format="PNG")
                img_io.seek(0)
                doc.add_picture(img_io, width=Inches(5.0))
            except: pass
                
        rapor_metni = veri.get("rapor", "Rapor oluşturulamadı.")
        for line in rapor_metni.split('\n'):
            line = line.strip()
            if not line: continue
            if line.startswith('---'):
                doc.add_paragraph().add_run('_' * 50)
                continue
            if line.startswith('### '): doc.add_heading(line[4:].replace('**', ''), level=3)
            elif line.startswith('## '): doc.add_heading(line[3:].replace('**', ''), level=2)
            elif line.startswith('# '): doc.add_heading(line[2:].replace('**', ''), level=1)
            elif line.startswith('* ') or line.startswith('- '):
                p = doc.add_paragraph(style='List Bullet')
                parts = line[2:].split('**')
                for i, part in enumerate(parts):
                    if part: p.add_run(part).bold = (i % 2 != 0)
            else:
                p = doc.add_paragraph()
                parts = line.split('**')
                for i, part in enumerate(parts):
                    if part: p.add_run(part).bold = (i % 2 != 0)
        if idx < len(vaka_listesi): doc.add_page_break()
            
    docx_io = io.BytesIO()
    doc.save(docx_io)
    return docx_io.getvalue()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .block-container { max-width: 1200px !important; padding-top: 1.2rem !important; margin: 0 auto !important; }
    .firm-header { background-color: #2C3848; padding: 18px 26px; border-radius: 6px; color: #ffffff; display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
    .firm-title { font-family: 'Cinzel', serif; font-size: 19px; font-weight: 700; letter-spacing: 1.5px; }
    .firm-subtitle { font-size: 11px; color: #DCE4EC; margin-top: 2px; }
    .firm-badge { background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255, 255, 255, 0.3); font-size: 11px; padding: 5px 12px; border-radius: 4px; }
    .section-heading { font-family: 'Cinzel', serif; font-size: 13.5px; font-weight: 700; color: #2C3848; border-bottom: 2px solid #E2E8F0; padding-bottom: 5px; margin-bottom: 12px; }
    div[data-testid="stRadio"] > div[role="radiogroup"] { display: flex; justify-content: center; gap: 14px; width: 100%; margin-bottom: 20px; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label { flex: 1; background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 6px; padding: 12px 18px; cursor: pointer; text-align: center; display: flex; align-items: center; justify-content: center; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover { border-color: #5D728B; background: #F8FAFC; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) { border-color: #5D728B !important; background-color: #F1F5F9 !important; font-weight: 600 !important; color: #1E293B !important; }
</style>
<div class="firm-header" lang="tr">
    <div><div class="firm-title">ADSHIELD PRO</div><div class="firm-subtitle">Gelişmiş Hukuki Mütalaa & Risk Denetim Sistemi</div></div>
    <div class="firm-badge">Sınırsız Pro Motoru Aktif</div>
</div>
""", unsafe_allow_html=True)

SABIT_GEMINI_KEY = "AQ.Ab8RN6JFqapI0MHEsOtNuXt8Ag_3bQEXQ4Qiw0aUHAjHhjxXbg"
SABIT_SERP_KEY = "627674c9f6d0c31b8196c2551afa690a7d03bfcd1531e38226059fc0e95b8cd9"

with st.sidebar:
    st.header("Sistem Ayarları")
    api_key_input = st.text_input("Gemini API Key:", value=SABIT_GEMINI_KEY, type="password")
    serpapi_key = st.text_input("SerpApi Key:", value=SABIT_SERP_KEY, type="password")
    api_key = api_key_input if api_key_input else SABIT_GEMINI_KEY

def get_master_prompt(sektor, mecra, metin=""):
    ek_metin = f"\nReklam Metni/İddia: {metin}\n" if metin else ""
    return f"""SEN KATKISI DEĞİŞTİRİLEMEZ BİR HAKSIZ REKABET AVUKATI VE REKLAM KURULU BAŞDENETÇİSİSİN.
Sektör: {sektor} | Mecra: {mecra} {ek_metin}

"Genel olarak incelendiğinde", "hedef kitleye uygundur" gibi pazarlama ağzı ifadeleri KESİNLİKLE KULLANMA. Doğrudan hukuki tespite gir.

ZORUNLU ANALİZ ADIMLARI:
### 1. Görsel Tespitler
(Sadece ekranda gördüğün somut objeleri, mizanseni, punto farklılıklarını listele. Yorum yapma.)
### 2. Çapraz Hukuki İnceleme
**Kurumun Olası İddiası:** Görseldeki vaadin hangi tüketici zaafını veya sağlık beyanını ihlal ettiğini agresif bir dille yaz.
**Markanın Olası Savunması:** İlgili ibarenin neden sadece bir "kozmetik" veya "abartılı reklam" sayılabileceğini savun.
### 3. Risk Kararı
İlgili yönetmelikleri baz alarak net bir mütalaa yaz."""

def ai_istek_at(prompt, gorsel, is_stream=False):
    genai.configure(api_key=api_key)
    
    try:
        izin_verilenler = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except Exception as e:
        raise Exception(f"API anahtarınız Google sunucuları tarafından reddedildi. Detay: {str(e)}")

    hedef_modeller = [
        "gemini-pro-latest", 
        "gemini-3.1-pro-preview", 
        "gemini-2.5-pro", 
        "gemini-3.6-flash", 
        "gemini-flash-latest"
    ]
    
    secilen_model = None
    for hedef in hedef_modeller:
        if hedef in izin_verilenler:
            secilen_model = hedef
            break
            
    if not secilen_model:
        secilen_model = izin_verilenler[0] if izin_verilenler else None

    if not secilen_model:
        raise Exception("API anahtarınızın görsel işleme yetkisi yok.")

    model = genai.GenerativeModel(secilen_model)
    # Ücretli sürümde olduğumuz için bekleme (sleep) mekanizması kaldırıldı
    if is_stream:
        return model.generate_content([prompt, gorsel], stream=False, generation_config={"temperature": 0.3})
    else:
        return model.generate_content([prompt, gorsel], generation_config={"temperature": 0.3}).text

def generate_multi_role_synthesis_stream(gorsel, sektor, mecra, metin=""):
    prompt = get_master_prompt(sektor, mecra, metin)
    try:
        response = ai_istek_at(prompt, gorsel, is_stream=True)
        if response and response.text:
            words = response.text.split(' ')
            for i in range(0, len(words), 6):
                yield ' '.join(words[i:i+6]) + ' '
                time.sleep(0.02)
            return
    except Exception as e:
        yield f"\nSistem Hatası: {str(e)}"
        return

def analiz_et_tekil(gorsel, url, sektor, mecra):
    prompt = f"Bağlantı: {url} \n\n{get_master_prompt(sektor, mecra)}"
    try:
        return ai_istek_at(prompt, gorsel, is_stream=False)
    except Exception as e:
        return f"Hata oluştu: {str(e)}"

def tekil_sorgu_at(kategori, sorgu, api_key_val):
    url = f"https://serpapi.com/search.json?q={urllib.parse.quote(sorgu)}&api_key={api_key_val}&engine=google&gl=tr&hl=tr&num=20"
    try:
        response = requests.get(url, timeout=20)
        data = response.json()
        if "error" in data: return kategori, [{"baslik": "Hata/Engellendi", "url": "#", "snippet": data['error']}]
        link_havuzu = []
        for result in data.get("organic_results", []):
            link = result.get("link", "")
            if not link.startswith("http"): continue
            link_havuzu.append({"baslik": result.get("title", "İsimsiz"), "url": link, "snippet": result.get("snippet", "")})
        if not link_havuzu: return kategori, [{"baslik": "Uygun sonuç bulunamadı.", "url": "#", "snippet": ""}]
        return kategori, link_havuzu
    except Exception as e: 
        return kategori, [{"baslik": "⚠️ HATA", "url": "#", "snippet": str(e)}]

def gelismis_coklu_hedef_taramasi(urun_adi, api_key_val):
    if not api_key_val or not urun_adi.strip(): return {}
    t = urun_adi.strip()
    queries = {
        "📸 Instagram": f'site:instagram.com intitle:"{t}"',
        "🛒 E-Ticaret": f'(site:trendyol.com OR site:hepsiburada.com) intitle:"{t}" -inurl:sr -inurl:ara'
    }
    kategorize_sonuclar = {}
    for kat, q in queries.items():
        _, sonuclar = tekil_sorgu_at(kat, q, api_key_val)
        gorulenler = set()
        tekil_list = []
        for item in sonuclar:
            if item["url"] not in gorulenler:
                gorulenler.add(item["url"])
                tekil_list.append(item)
        kategorize_sonuclar[kat] = tekil_list
    return kategorize_sonuclar

for k in ["rapor_sonucu", "eklenti_img", "eklenti_url", "vaka_havuzu", "radar_link_sonuclari"]:
    if k not in st.session_state: st.session_state[k] = None if k != "vaka_havuzu" else []

mod_secimi = st.radio("Denetim Modu", [
    "Kurumsal Kampanya Taslağı Uyum Denetimi (İç Denetim & Revizyon Modu)",
    "Piyasa ve Rakip Reklam İncelemesi (Haksız Rekabet & Şikayet Modu)",
    "360° Çoklu Satıcı ve Pazar Radarı (Hedefli Ürün Linki Tespiti)"
], horizontal=True, label_visibility="collapsed")

is_radar = "360°" in mod_secimi

sol_kolon, sag_kolon = st.columns([1, 1.25], gap="large")

if not is_radar:
    with sol_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">1. Veri Yükleme</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Son Görüntüyü Al"):
                    gelen = eklenti_verilerini_getir()
                    if gelen:
                        son = gelen[-1]
                        st.session_state.eklenti_url = son.get('url', '')
                        b64 = son.get('image', '').split(',')[-1].strip() + '=='
                        st.session_state.eklenti_img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
                        st.rerun()
            with col2:
                if st.button("📥 Tüm Kuyruğu Al"):
                    for item in eklenti_verilerini_getir():
                        b64 = item.get('image', '').split(',')[-1].strip() + '=='
                        st.session_state.vaka_havuzu.append({"url": item.get('url', ''), "gorsel": Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB"), "rapor": None})
                    st.rerun()

            if st.session_state.eklenti_img:
                st.image(st.session_state.eklenti_img, use_container_width=True)
                sektor = st.selectbox("Faaliyet Sektörü", ["Kozmetik & Kişisel Bakım", "Takviye Edici Gıda & Sağlık", "E-Ticaret", "Diğer"])
                mecra = st.selectbox("Yayınlanacak Mecra", ["İnternet / Sosyal Medya", "Satış Noktası", "Televizyon", "Açık Hava"])
                reklam_url = st.text_input("Web Sayfası / Ürün Linki", value=st.session_state.get("eklenti_url", ""))
                reklam_metni = st.text_area("Reklam Metni / Ticari İddialar", height=90)
                
                if st.button("Tekil Analizi Başlat (Sınırsız Pro Mod)", type="primary"):
                    st.session_state.rapor_sonucu = None
            
            if st.session_state.vaka_havuzu:
                st.write(f"**Havuz:** {len(st.session_state.vaka_havuzu)} vaka")
                s_sektor = st.selectbox("Toplu Sektör", ["Kozmetik", "Takviye Edici Gıda"])
                s_mecra = st.selectbox("Toplu Mecra", ["İnternet", "TV"])
                if st.button("Toplu Analizi Başlat (Sınırsız Pro Mod)", type="primary"):
                    my_bar = st.progress(0)
                    status = st.empty()
                    for i, vaka in enumerate(st.session_state.vaka_havuzu):
                        status.info(f"Vaka #{i+1} inceleniyor...")
                        vaka["rapor"] = analiz_et_tekil(vaka["gorsel"], vaka["url"], s_sektor, s_mecra)
                        my_bar.progress((i + 1) / len(st.session_state.vaka_havuzu))
                    status.empty()
                    st.rerun()

    with sag_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">2. Hukuki Mütalaa Çıktıları</div>', unsafe_allow_html=True)
            if st.session_state.eklenti_img and st.session_state.rapor_sonucu is None and reklam_url is not None:
                rapor_alani = st.empty()
                tam_rapor = ""
                for parca in generate_multi_role_synthesis_stream(st.session_state.eklenti_img, sektor, mecra, reklam_metni):
                    tam_rapor += parca
                    rapor_alani.markdown(tam_rapor + "▌")
                rapor_alani.markdown(tam_rapor)
                st.session_state.rapor_sonucu = tam_rapor
            elif st.session_state.rapor_sonucu:
                st.markdown(st.session_state.rapor_sonucu)

            if st.session_state.vaka_havuzu:
                for idx, vaka in enumerate(st.session_state.vaka_havuzu, 1):
                    with st.expander(f"Vaka #{idx}"):
                        st.image(vaka["gorsel"], width=150)
                        if vaka["rapor"]: st.markdown(vaka["rapor"])
                if any(v.get("rapor") for v in st.session_state.vaka_havuzu):
                    word_bytes = create_docx(st.session_state.vaka_havuzu)
                    st.download_button("⬇️ Tüm Raporları İndir (DOCX)", word_bytes, "adshield_toplu.docx", use_container_width=True)

else:
    with sol_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">Pazar Radarı</div>', unsafe_allow_html=True)
            radar_urun = st.text_input("Marka / İhlal Kelimesi", value="incia bebek yağı")
            if st.button("Hedefleri Bul", type="primary"):
                with st.spinner("Tarama sürüyor..."):
                    st.session_state.radar_link_sonuclari = gelismis_coklu_hedef_taramasi(radar_urun, serpapi_key)
    with sag_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">Bulgular</div>', unsafe_allow_html=True)
            if st.session_state.get("radar_link_sonuclari"):
                sekmeler = st.tabs(list(st.session_state.radar_link_sonuclari.keys()))
                for i, (kat, links) in enumerate(st.session_state.radar_link_sonuclari.items()):
                    with sekmeler[i]:
                        for idx, item in enumerate(links, 1): st.markdown(f"**{idx}. [{item['baslik']}]({item['url']})**")
