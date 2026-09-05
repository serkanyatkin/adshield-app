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
    except Exception:
        pass
    return []

def create_docx(vaka_listesi):
    doc = docx.Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)

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
                p = doc.add_paragraph()
                p.add_run('_' * 50)
                continue
            if line.startswith('### '): doc.add_heading(line[4:].replace('**', ''), level=3)
            elif line.startswith('## '): doc.add_heading(line[3:].replace('**', ''), level=2)
            elif line.startswith('# '): doc.add_heading(line[2:].replace('**', ''), level=1)
            elif line.startswith('* ') or line.startswith('- '):
                p = doc.add_paragraph(style='List Bullet')
                line_content = line[2:]
                parts = line_content.split('**')
                for i, part in enumerate(parts):
                    if not part: continue
                    run = p.add_run(part)
                    if i % 2 != 0: run.bold = True
            else:
                p = doc.add_paragraph()
                parts = line.split('**')
                for i, part in enumerate(parts):
                    if not part: continue
                    run = p.add_run(part)
                    if i % 2 != 0: run.bold = True
        if idx < len(vaka_listesi): doc.add_page_break()
            
    docx_io = io.BytesIO()
    doc.save(docx_io)
    return docx_io.getvalue()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .block-container { max-width: 1200px !important; padding-top: 1.2rem !important; margin: 0 auto !important; }
    .firm-header { background-color: #2C3848; padding: 18px 26px; border-radius: 6px; color: #ffffff; display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; box-shadow: 0 4px 14px rgba(44, 56, 72, 0.2); }
    .firm-title { font-family: 'Cinzel', serif; font-size: 19px; letter-spacing: 1.5px; font-weight: 700; }
    .firm-subtitle { font-size: 11px; letter-spacing: 1px; color: #DCE4EC; margin-top: 2px; }
    .firm-badge { background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255, 255, 255, 0.3); color: #ffffff; font-size: 11px; font-weight: 600; padding: 5px 12px; border-radius: 4px; }
    .section-heading { font-family: 'Cinzel', serif; font-size: 13.5px; letter-spacing: 1px; color: #2C3848; font-weight: 700; margin-bottom: 12px; border-bottom: 2px solid #E2E8F0; padding-bottom: 5px; }
</style>
<div class="firm-header" lang="tr">
    <div><div class="firm-title">ADSHIELD PRO</div><div class="firm-subtitle">Gelişmiş Hukuki Mütalaa & Risk Denetim Sistemi</div></div>
    <div class="firm-badge">Gemini 1.5 Pro Motoru Aktif</div>
</div>
""", unsafe_allow_html=True)

SABIT_SERP_KEY = "627674c9f6d0c31b8196c2551afa690a7d03bfcd1531e38226059fc0e95b8cd9"

with st.sidebar:
    st.header("Sistem Ayarları")
    api_key = st.text_input("Gemini API Key:", value=st.secrets.get("GEMINI_API_KEY", ""), type="password")
    serpapi_key = st.text_input("SerpApi Key:", value=SABIT_SERP_KEY, type="password")

if not serpapi_key: serpapi_key = SABIT_SERP_KEY

# ZEKASI YÜKSELTİLMİŞ MODEL
TARGET_MODEL = "gemini-1.5-pro"

# YENİ HUKUKİ MÜTALAA MİMARİSİ (PROMPT)
MASTER_PROMPT = """SEN KATKISI DEĞİŞTİRİLEMEZ BİR HAKSIZ REKABET AVUKATI VE REKLAM KURULU BAŞDENETÇİSİSİN.
"Genel olarak incelendiğinde", "hedef kitleye uygundur", "tasarım başarılıdır" gibi pazarlama ağzı ifadeleri KESİNLİKLE KULLANMA. Doğrudan hukuki tespite gir.

ZORUNLU ANALİZ ADIMLARI (Bu yapıya birebir uy):

### 1. Görsel Tespitler (Görsel Körlüğünü Kırmak İçin)
(Sadece ekranda gördüğün somut objeleri, mizanseni, punto farklılıklarını ve yazıları listele. Yorum yapma.)

### 2. Çapraz Hukuki İnceleme
**Kurumun/Şikayetçinin Olası İddiası:** Görseldeki mizansenin veya vaadin hangi tüketici zaafını istismar ettiğini veya hangi fizyolojik etkiyi (sağlık beyanını) ima ettiğini agresif bir dille yaz.
**Markanın Olası Savunması:** İlgili ibarenin neden sadece bir "kozmetik" veya "abartılı reklam (puffery)" sayılabileceğini, hukuki bir boşluk bularak savun.

### 3. Mevzuat ve İçtihat Altlaması (Risk Kararı)
6502 Sayılı Kanun, Ticari Reklam Yönetmeliği ve TİTCK kılavuzlarını baz alarak net bir ihlal kararı ver. "Şu madde ihlal edilmiştir, idari para cezası riski yüksektir" şeklinde kesin bir mütalaa yaz."""

def get_working_model():
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name=TARGET_MODEL)

def generate_multi_role_synthesis_stream(contents):
    genai.configure(api_key=api_key)
    model = get_working_model()
    for attempt in range(3):
        try:
            response = model.generate_content([MASTER_PROMPT] + contents, stream=False)
            if response and response.text:
                words = response.text.split(' ')
                for i in range(0, len(words), 6):
                    yield ' '.join(words[i:i+6]) + ' '
                    time.sleep(0.04)
                return
        except Exception as e:
            if "429" in str(e) or "Quota" in str(e):
                yield f"\n\n> ⏳ 1.5 Pro Kotası Bekleniyor ({35 * (attempt+1)} sn)...\n\n"
                time.sleep(35 * (attempt + 1))
                continue
            yield f"\nSentezleme hatası: {str(e)}"
            return

def analiz_et_tekil(gorsel, url):
    genai.configure(api_key=api_key)
    model = get_working_model()
    prompt = f"Aşağıdaki bağlantıda yer alan reklamı ({url}) incele. \n\n{MASTER_PROMPT}"
    
    for deneme in range(3):
        try:
            # 1.5 Pro modelinde yaratıcılığı (temperature) biraz açıyoruz ki farklı kararlar sentezleyebilsin.
            res = model.generate_content([prompt, gorsel], generation_config={"temperature": 0.3})
            return res.text
        except Exception as e:
            if "429" in str(e) or "Quota" in str(e):
                time.sleep(35 * (deneme + 1)) 
                continue
            return f"Hata oluştu: {str(e)}"
    return "Analiz tamamlanamadı: Google Gemini API limitleri aşıldı."

def tekil_sorgu_at(kategori, sorgu, api_key_val):
    url = f"https://serpapi.com/search.json?q={urllib.parse.quote(sorgu)}&api_key={api_key_val}&engine=google&gl=tr&hl=tr&num=20"
    try:
        response = requests.get(url, timeout=20)
        data = response.json()
        if "error" in data: return kategori, [{"baslik": "Sonuç Bulunamadı", "url": "#", "snippet": data['error']}]
        link_havuzu = []
        for result in data.get("organic_results", []):
            link = result.get("link", "")
            if not link.startswith("http"): continue
            link_havuzu.append({"baslik": result.get("title", ""), "url": link, "snippet": result.get("snippet", "")})
        return kategori, link_havuzu
    except Exception as e: 
        return kategori, [{"baslik": "⚠️ HATA", "url": "#", "snippet": str(e)}]

def gelismis_coklu_hedef_taramasi(urun_adi, api_key_val):
    if not api_key_val or not urun_adi.strip(): return {}
    t = urun_adi.strip()
    queries = {
        "📸 Instagram": f'site:instagram.com "{t}"',
        "🛒 E-Ticaret": f'(site:trendyol.com OR site:hepsiburada.com) "{t}" -inurl:sr -inurl:ara -inurl:kategori'
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

for k in ["rapor_sonucu", "eklenti_img", "vaka_havuzu"]:
    if k not in st.session_state: st.session_state[k] = None if k != "vaka_havuzu" else []

mod_secimi = st.radio("Denetim Modu", ["Kurumsal Uyum Denetimi (Tekil/Çoklu)", "Pazar Radarı"], horizontal=True, label_visibility="collapsed")

sol_kolon, sag_kolon = st.columns([1, 1.25], gap="large")

if "Uyum" in mod_secimi:
    with sol_kolon:
        with st.container(border=True):
            st.markdown(f'<div class="section-heading" lang="tr">1. Veri Yükleme & Kuyruk</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Son Görüntüyü Al (Tekil)"):
                    gelen_liste = eklenti_verilerini_getir()
                    if gelen_liste:
                        son_item = gelen_liste[-1]
                        b64_img = son_item.get('image', '').split(',')[-1].strip()
                        b64_img += '=' * ((4 - len(b64_img) % 4) % 4)
                        st.session_state.eklenti_img = Image.open(io.BytesIO(base64.b64decode(b64_img))).convert("RGB")
                        st.rerun()
            with col2:
                if st.button("📥 Tüm Kuyruğu Al (Toplu)"):
                    gelen_liste = eklenti_verilerini_getir()
                    if gelen_liste:
                        for item in gelen_liste:
                            b64 = item.get('image', '').split(',')[-1].strip()
                            b64 += '=' * ((4 - len(b64) % 4) % 4)
                            st.session_state.vaka_havuzu.append({"url": item.get('url', ''), "gorsel": Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB"), "rapor": None})
                        st.rerun()

            if st.session_state.eklenti_img:
                st.image(st.session_state.eklenti_img, use_container_width=True)
                if st.button("Tekil Analizi Başlat", type="primary"):
                    st.session_state.rapor_sonucu = None
            
            if st.session_state.vaka_havuzu:
                st.write(f"**Havuz:** {len(st.session_state.vaka_havuzu)} vaka")
                if st.button("Toplu Analizi Başlat (Pro Mod)", type="primary"):
                    my_bar = st.progress(0, text="Pro Model çalışıyor...")
                    status = st.empty()
                    for i, vaka in enumerate(st.session_state.vaka_havuzu):
                        if i > 0:
                            for sec in range(35, 0, -1):
                                status.warning(f"1.5 Pro kotası için {sec} sn bekleniyor...")
                                time.sleep(1)
                        status.info(f"Vaka #{i+1} derin analize tabi tutuluyor...")
                        vaka["rapor"] = analiz_et_tekil(vaka["gorsel"], vaka["url"])
                        my_bar.progress((i + 1) / len(st.session_state.vaka_havuzu))
                    status.empty()
                    st.rerun()

    with sag_kolon:
        with st.container(border=True):
            st.markdown(f'<div class="section-heading" lang="tr">2. Hukuki Mütalaa Çıktıları</div>', unsafe_allow_html=True)
            if st.session_state.eklenti_img and not st.session_state.rapor_sonucu:
                rapor_alani = st.empty()
                tam_rapor = ""
                for parca in generate_multi_role_synthesis_stream([st.session_state.eklenti_img]):
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
                        else: st.info("Bekliyor...")
                if any(v.get("rapor") for v in st.session_state.vaka_havuzu):
                    word_bytes = create_docx(st.session_state.vaka_havuzu)
                    st.download_button("⬇️ Tüm Mütalaaları İndir (DOCX)", data=word_bytes, file_name="adshield_pro_rapor.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

else:
    with sol_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">Pazar Radarı</div>', unsafe_allow_html=True)
            radar_urun = st.text_input("Marka / İhlal Kelimesi", value="incia bebek yağı")
            if st.button("Hedefleri Bul", type="primary"):
                with st.spinner("Taranıyor..."):
                    st.session_state.radar_link_sonuclari = gelismis_coklu_hedef_taramasi(radar_urun, serpapi_key)
    with sag_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">Bulgular</div>', unsafe_allow_html=True)
            if st.session_state.get("radar_link_sonuclari"):
                sekmeler = st.tabs(list(st.session_state.radar_link_sonuclari.keys()))
                for i, (kat, links) in enumerate(st.session_state.radar_link_sonuclari.items()):
                    with sekmeler[i]:
                        for idx, item in enumerate(links, 1): st.markdown(f"**{idx}. [{item['baslik']}]({item['url']})**")
