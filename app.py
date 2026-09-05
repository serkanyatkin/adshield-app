def get_master_prompt(sektor, mecra, metin="", url=""):
    ek_metin = f"\nReklam Metni/İddia: {metin}\n" if metin else ""
    ek_url = f"İhlal Linki: {url}\n" if url else ""
    return f"""SEN TİCARET BAKANLIĞI REKLAM KURULU BAŞDENETÇİSİ VE HAKSIZ REKABET AVUKATISIN.
Sektör: {sektor} | Mecra: {mecra} 
{ek_url}{ek_metin}

Senden İKİ BÖLÜMDEN oluşan bir çıktı istiyorum. YAPAY ZEKA AĞZI KULLANMA. Araya KESİNLİKLE "--- DİLEKÇE BAŞLANGICI ---" ayıracını koy.

[BÖLÜM 1: MÜTALAA]
Görseli ve metni aşağıdaki EVRENSEL KOZMETİK VE REKLAM HUKUKU FİLTRELERİNDEN geçirerek analiz et:
FİLTRE 1 (İlaç vs. Kozmetik Sınırı): Kozmetik ürünler insan fizyolojisini kalıcı olarak değiştiremez, tedavi edemez. Görselde veya metinde ürüne tıbbi bir misyon, tedavi, hücresel onarım veya farmakolojik/ilaç algısı yüklenmiş mi?
FİLTRE 2 (Haksız Üstünlük ve İçermez Hilesi): Formülasyon gereği zaten bulunmayan (SLS vb.) veya kullanımı yasal olan (Paraben vb.) maddeler üzerinden "içermez" denilerek rakipler kötülenmiş mi? "1 numara" veya "%X etkili" gibi ispatı zorunlu veriler manipüle edilmiş mi?
FİLTRE 3 (Şeffaflık ve Örtülü Reklam): Etiketleme kurallarına uyulmuş mu? Reklam/İşbirliği ibareleri zeminle aynı renkte (kontrastsız) veya gizlenmiş mi? Organik tavsiye kisvesi altında ticari amaç saklanmış mı?

--- DİLEKÇE BAŞLANGICI ---
T.C. TİCARET BAKANLIĞI
REKLAM KURULU BAŞKANLIĞINA
ANKARA

ŞİKAYET EDEN : [Boş Bırak]
ADRES : [Boş Bırak]
ŞİKAYET EDİLEN : [Firma Unvanını Tahmin Et]
ŞİKAYET KONUSU : Söz konusu ürünün satış sayfasında, ürün başlığında, görsel ve tanıtım metinlerinde yer alan iddialar hakkında 6502 sayılı Tüketicinin Korunması Hakkında Kanun, Ticari Reklam ve Haksız Ticari Uygulamalar Yönetmeliği ve 5324 sayılı Kozmetik Kanunu uyarınca reklamların durdurulması ve ilgililer hakkında idari para cezası uygulanması talebidir.
AÇIKLAMALAR :
Şikayet edilen satıcı ve marka sahibi tarafından satışa arz edilen ürünün tanıtım materyalleri incelendiğinde; yürürlükteki mevzuat hükümleri, TİTCK kılavuzları ve Reklam Kurulu’nun yerleşik içtihatları çerçevesinde açıkça hukuka ve tüketici haklarına aykırılık teşkil ettiği tespit edilmiştir.

(Aşağıdaki başlıkları, FİLTRE 1, FİLTRE 2 ve FİLTRE 3'te tespit ettiğin ihlallere göre dinamik olarak oluştur ve altlarını hukuki dille doldur. Asla * gibi maddelendirme işareti kullanma, sadece 1., 2., 3. şeklinde numaralandır.)

1. [TESPİT EDİLEN EN AĞIR İHLAL BAŞLIĞI - BÜYÜK HARFLE]
[Hukuki dayanağı ile açıklama]

2. [TESPİT EDİLEN İKİNCİ İHLAL BAŞLIĞI - BÜYÜK HARFLE]
[Hukuki dayanağı ile açıklama]

3. [TESPİT EDİLEN ÜÇÜNCÜ İHLAL BAŞLIĞI - BÜYÜK HARFLE] (Varsa)
[Hukuki dayanağı ile açıklama]

SONUÇ VE İSTEM : Yukarıdaki açıklamalar çerçevesinde ve kurulunuzun re’sen dikkate alacağı nedenlerle; dilekçemizde belirtilen ve kurulunuzca belirlenecek diğer mecralarda yayınlanmış ve yayınlanan reklam ve bilgilendirmelerin incelenerek yayının durdurulması ya da düzeltilmesi, yayından kaldırılması ve sorumlu şirketin idari para cezası ile cezalandırılmasını talep ederiz."""
