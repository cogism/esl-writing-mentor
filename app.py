import streamlit as st
import streamlit.components.v1 as components
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os
import re # EKLENDİ: Hata etiketlerini ayrıştırmak için
from docx import Document

# 1. Sayfa Ayarları 
st.set_page_config(page_title="ESL Writing Mentor", page_icon="✒️", layout="wide")

# CSS: Minimalist Tasarım ve Animasyonlu Kartlar + SARI INLINE HIGHLIGHT
st.markdown("""
    <style>
    .stApp { font-family: 'Inter', sans-serif; }
    .stMarkdown { color: #cbd5e1 !important; } 
    h1, h2, h3 { color: #f8fafc !important; font-weight: 600 !important; letter-spacing: -0.5px; }
    
    .stTextArea textarea, .stTextInput input {
        background-color: #0f172a !important; 
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        padding: 16px !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
        transition: border-color 0.3s ease;
    }
    .stTextArea textarea:focus, .stTextInput input:focus { border-color: #3b82f6 !important; box-shadow: none !important; }
    
    .report-card { 
        background-color: #1e293b; 
        padding: 40px; 
        border-radius: 16px; 
        border: 1px solid rgba(255,255,255,0.05);
        color: #e2e8f0 !important; 
        line-height: 1.8;
        font-size: 16px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -2px rgba(0, 0, 0, 0.1); 
    }
    .coach-card {
        background-color: rgba(56, 189, 248, 0.1); 
        border-left: 4px solid #38bdf8;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    
    .report-card h3 { color: #38bdf8 !important; margin-top: 30px; margin-bottom: 15px; font-size: 1.25rem; border-bottom: 1px solid #334155; padding-bottom: 8px; }
    .report-card h3:first-child { margin-top: 0; }
    .report-card strong { color: #fbbf24 !important; background-color: rgba(251, 191, 36, 0.12); padding: 2px 6px; border-radius: 6px; font-weight: 600; }

    /* --- SIDEBAR MENÜ TASARIMI --- */
    div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div[role="radiogroup"] > label {
        background-color: rgba(255, 255, 255, 0.03) !important;
        padding: 16px 20px !important;
        border: 2px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        margin-bottom: 12px !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        width: 100%;
        display: flex;
        align-items: center;
    }
    div[role="radiogroup"] > label p { font-size: 1.15rem !important; font-weight: 600 !important; color: #e2e8f0 !important; margin: 0 !important; }
    div[role="radiogroup"] > label:hover { border-color: #38bdf8 !important; background-color: rgba(56, 189, 248, 0.08) !important; transform: translateX(6px); }
    div[role="radiogroup"] > label[data-checked="true"], div[role="radiogroup"] > label[aria-checked="true"] { border-color: #3b82f6 !important; background-color: rgba(59, 130, 246, 0.15) !important; }
    div[role="radiogroup"] > label[data-checked="true"] p, div[role="radiogroup"] > label[aria-checked="true"] p { color: #38bdf8 !important; }

    /* --- EKLENDİ: SARI TONLU INLINE HIGHLIGHT (EKRAN GÖRÜNTÜSÜNDEKİ GİBİ) --- */
    .err-wrapper {
        position: relative;
        display: inline-block;
        margin: 0 2px;
        cursor: help;
    }
    .err-text {
        color: #fbbf24 !important; /* Sarı Metin */
        background-color: rgba(251, 191, 36, 0.12) !important; /* Koyu Sarı Zemin */
        padding: 2px 6px;
        border-radius: 6px; /* Oval Köşeler */
        font-weight: 600;
    }
    .err-wrapper:hover::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 130%;
        left: 50%;
        transform: translateX(-50%);
        background-color: #1e293b;
        color: #f8fafc;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #334155;
        width: 280px;
        z-index: 1000;
        font-size: 0.85rem;
        line-height: 1.6;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
        white-space: pre-wrap;
        font-weight: normal;
    }
    </style>
    """, unsafe_allow_html=True)

# Gelişmiş Global JavaScript: Kelime sınırlarını ve tüm text alanlarını canlı takip eder
components.html("""
    <script>
    const doc = window.parent.document;
    if (!doc.getElementById('esl-global-script')) {
        const scriptMarker = doc.createElement('div');
        scriptMarker.id = 'esl-global-script';
        doc.body.appendChild(scriptMarker);

        doc.addEventListener('input', function(e) {
            if (e.target.tagName.toLowerCase() === 'textarea') {
                const label = e.target.getAttribute('aria-label');
                let counterId = null;

                if (label === 'Draft 1 Metni:') counterId = 'counter-d1';
                else if (label === 'Draft 2 (Final) Metni:') counterId = 'counter-d2';
                else if (label === 'Metninizi yapıştırın:' || label === 'Metninizi düzenleyin:') counterId = 'live-word-counter';

                if (counterId) {
                    const text = e.target.value.trim();
                    const words = text === "" ? 0 : text.split(/\\s+/).length;
                    const counter = doc.getElementById(counterId);
                    if (counter) {
                        if (words > 500) {
                            counter.innerHTML = "Kelime Sayısı: " + words + " / 500 (Sınırı aştınız!)";
                            counter.style.color = "#ef4444"; 
                        } else if (words > 0 && words < 100) {
                            counter.innerHTML = "Kelime Sayısı: " + words + " / 500 (Çok kısa!)";
                            counter.style.color = "#f59e0b"; 
                        } else {
                            counter.innerHTML = "Kelime Sayısı: " + words + " / 500";
                            counter.style.color = "#94a3b8"; 
                        }
                    }
                }
            }
        });
    }
    </script>
""", height=0)

def read_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

# EKLENDİ: Yapay zekanın 2'ye böldüğü çıktıyı HTML'e çeviren fonksiyon
def parse_dual_output(raw_output: str):
    parts = raw_output.split("---RAPOR_BASLANGIC---")
    marked_text = parts[0].strip()
    report = parts[1].strip() if len(parts) > 1 else "Rapor oluşturulamadı."
    
    # regex: [ERR]yanlış|doğru|tür|neden[/ERR]
    pattern = r"\[ERR\](.*?)\|(.*?)\|(.*?)\|(.*?)\[/ERR\]"
    def replace_with_html(match):
        wrong, fixed, etype, reason = match.groups()
        # GÜNCELLENDİ: \n yerine HTML satır atlama kodu olan &#10; kullanıldı
        return (f'<span class="err-wrapper" data-tooltip="🏷️ Tür: {etype}&#10;✨ Doğrusu: {fixed}&#10;💡 Neden: {reason}">'
                f'<span class="err-text">{wrong}</span></span>')
    
    html_marked_text = re.sub(pattern, replace_with_html, marked_text)
    return html_marked_text, report

class ESLFeedbackBot:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            st.error("Hata: .env dosyasında HUGGINGFACE_API_KEY bulunamadı!")
            st.stop()
        self.client = InferenceClient(token=api_key)
    
    def analyze_essay(self, essay: str, tone: str, topic: str = "") -> str:
        topic_context = f"\nÖğrenciye Verilen Essay Sorusu: {topic}\n" if topic.strip() else ""
        
        # GÜNCELLENDİ: Metni sarı etiket formatına hazırlayan ve raporu bölen Prompt
        prompt = f"""<|im_start|>system
        Sen anadili Türkçe olan, acımasız ama adil bir IELTS Examiner ve uzman İngilizce öğretmenisin.
        Öğrenciye Karşı Tonun: {tone}
        
        Lütfen KESİNLİKLE aşağıdaki 2 aşamalı kurala uy:
        
        ### 1. ADIM: İŞARETLENMİŞ METİN (INLINE HIGHLIGHT)
        Öğrencinin metnini KESİNLİKLE DEĞİŞTİRME. Yalnızca hatalı kelimeleri/kısımları şu etiket içine alarak metni aynen yaz:
        [ERR]hatalı_kısım|doğru_hali|HATA_TİPİ|açıklama[/ERR]
        (Hata Tipleri: SPELLING, GRAMMAR, VOCABULARY, PUNCTUATION, STYLE)
        
        ### 2. ADIM: DETAYLI RAPOR
        Metin işaretlemesi bittikten sonra tam olarak "---RAPOR_BASLANGIC---" yaz.
        Ayracın altına Görev Başarısı (soru verilmişse uyumu), Akıcılık ve Bütünlük, Kelime Dağarcığı, Gramer üzerinden Türkçe analizini yap. Sayısal IELTS puanı verme, CEFR tahmini yap.
        <|im_end|>
        <|im_start|>user
        {topic_context}
        Öğrenci Metni: {essay}
        <|im_end|>
        <|im_start|>assistant
        """
        return self._call_api(prompt)

    def get_quick_coach_feedback(self, outline: str, draft1: str, topic: str = "") -> str:
        topic_context = f"\nÖğrenciye Verilen Essay Sorusu: {topic}\n" if topic.strip() else ""
        
        prompt = f"""<|im_start|>system
        Sen anadili Türkçe olan bir IELTS Yazma Koçusun.
        Öğrenci bir taslak (outline) oluşturdu ve buna dayanarak ilk taslağını (Draft 1) yazdı.
        Görevin: Bu ilk taslağa KISA, ÖZ ve YAPICI bir geri bildirim vermek.
        
        KURALLAR:
        1. İnce gramer hatalarına TAKILMA.
        2. Sadece "Task Achievement" (Eğer soru verilmişse, soruya cevap vermiş mi?) ve "Coherence" (Fikir akışı) odaklan.
        3. Outline ile yazdığı metin uyumlu mu kontrol et.
        4. Öğrenciyi motive et ve 2. taslağa geçmesi için ona net 2-3 hedef ver.
        5. Çok uzun yazma, okunabilir ve tatlı-sert bir Türkçe kullan.
        <|im_end|>
        <|im_start|>user
        {topic_context}
        Öğrencinin Taslağı (Outline):\n{outline}\n\nÖğrencinin Draft 1 Metni:\n{draft1}
        <|im_end|>
        <|im_start|>assistant
        """
        return self._call_api(prompt)

    def _call_api(self, prompt: str) -> str:
        try:
            response = self.client.chat_completion(
                model="Qwen/Qwen2.5-72B-Instruct",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception:
            try:
                response = self.client.chat_completion(
                    model="Qwen/Qwen2.5-32B-Instruct",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=3000,
                    temperature=0.1
                )
                return response.choices[0].message.content
            except Exception as inner_e:
                return f"Analiz hatası: {str(inner_e)}"

def get_word_count_html(word_count, counter_id):
    if word_count > 500:
        return f"<div id='{counter_id}' style='color: #ef4444; font-size: 0.9em; font-weight: 500; margin-top: -10px; margin-bottom: 15px;'>Kelime Sayısı: {word_count} / 500 (Sınırı aştınız!)</div>"
    elif 0 < word_count < 100:
        return f"<div id='{counter_id}' style='color: #f59e0b; font-size: 0.9em; font-weight: 500; margin-top: -10px; margin-bottom: 15px;'>Kelime Sayısı: {word_count} / 500 (Çok kısa!)</div>"
    else:
        return f"<div id='{counter_id}' style='color: #94a3b8; font-size: 0.9em; font-weight: 500; margin-top: -10px; margin-bottom: 15px;'>Kelime Sayısı: {word_count} / 500</div>"

def render_fast_analysis(tone):
    st.markdown("İngilizce yazılarınızı IELTS standartlarında, yapay zeka destekli bir gözetmenle analiz edin.")
    st.write("") 

    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        uploaded_file = st.file_uploader("Word veya TXT dosyası yükleyin", type=["docx", "txt"])
        
        input_text = ""
        if uploaded_file:
            if uploaded_file.type == "text/plain":
                input_text = uploaded_file.read().decode("utf-8")
            else:
                input_text = read_docx(uploaded_file)
            input_text = st.text_area("Metninizi düzenleyin:", value=input_text, height=350, label_visibility="collapsed")
        else:
            input_text = st.text_area("Metninizi yapıştırın:", height=450, placeholder="Örn: Technology has made our lives more complex...")

        word_count = len(input_text.split()) if input_text else 0
        st.markdown(get_word_count_html(word_count, "live-word-counter"), unsafe_allow_html=True)

        if st.button("Analizi Başlat", type="primary", use_container_width=True):
            if not input_text.strip():
                st.warning("Lütfen analiz için bir metin girin.")
            elif word_count < 100:
                st.error(f"Metniniz çok kısa ({word_count} kelime). Lütfen en az 100 kelimelik bir metin girin.")
            elif word_count > 500:
                st.error(f"Metniniz çok uzun ({word_count} kelime). Lütfen maksimum 500 kelime girin.")
            else:
                with st.spinner("Examiner metni inceliyor..."):
                    bot = ESLFeedbackBot()
                    raw_result = bot.analyze_essay(input_text, tone)
                    # GÜNCELLENDİ: Hataları ekranda göstermek için ayırıyoruz
                    html_text, report = parse_dual_output(raw_result)
                    st.session_state.fast_html = html_text
                    st.session_state.fast_report = report
                    st.session_state.fast_done = True

    with col_out:
        if "fast_done" in st.session_state:
            # GÜNCELLENDİ: Ekran görüntüsündeki gibi Report Card içinde gösteriyoruz
            st.markdown("### 🎯 Hatalı Metin Üzerinde Analiz")
            st.markdown(f'<div class="report-card" style="margin-bottom: 20px; font-size: 1.1rem; line-height: 2.2;">\n{st.session_state.fast_html}\n</div>', unsafe_allow_html=True)
            
            st.markdown("### 📊 Detaylı IELTS Raporu")
            st.markdown(f'<div class="report-card">\n\n{st.session_state.fast_report}\n\n</div>', unsafe_allow_html=True)
        else:
            st.info("Detaylı geri bildirim raporunuz burada görüntülenecektir.")

def render_draft_creator(tone):
    # Üst Kısım: Başlık ve Halter (Pratik Soruları) Popover'ı
    col_title, col_practice = st.columns([5, 1])
    with col_title:
        st.markdown("IELTS yazılarınızı planlayın, ilk taslağınızı yazın ve koçtan geri bildirim alın.")
    with col_practice:
        with st.popover("🏋️ Pratik"):
            st.markdown("Kopyalayıp yandaki alana yapıştırabilirsiniz:")
            st.markdown("**Opinion**\n- Artificial intelligence will completely replace human teachers in the future. Do you agree or disagree?")
            st.markdown("**Discussion**\n- Some people think strict punishments for driving offences are the key to reducing traffic accidents. Others believe other measures would be more effective. Discuss both views.")
            st.markdown("**Problem & Solution**\n- In many countries, the amount of crime committed by teenagers is increasing. What are the main causes of this and what solutions can you suggest?")
            st.markdown("**Adv/Disadv**\n- More and more people are choosing to work from home. Do the advantages of this trend outweigh the disadvantages?")

    if "draft_step" not in st.session_state:
        st.session_state.draft_step = 1

    # İsteğe bağlı soru alanı
    essay_topic = st.text_area("Essay Sorusu (İsteğe Bağlı):", value=st.session_state.get("essay_topic", ""), placeholder="Pratik sorusunu veya kendi IELTS sorunuzu buraya yapıştırın...", height=68)
    st.session_state.essay_topic = essay_topic # Hafızada tut
    
    essay_type = st.selectbox("IELTS Essay Tipi Seçin:", ["Opinion (Agree/Disagree)", "Discussion (Discuss both views)", "Problem & Solution", "Advantages & Disadvantages"])
    
    # Dinamik Yönergeler
    structure_hints = {
        "Opinion (Agree/Disagree)": {
            "intro": "Konuyu tanıt ve net bir şekilde kendi fikrini (Thesis) belirt.",
            "body1": "Fikrini destekleyen BİRİNCİ ana sebep. Açıkla ve spesifik bir örnek ver.",
            "body2": "Fikrini destekleyen İKİNCİ ana sebep. Açıkla ve spesifik bir örnek ver.",
            "conclusion": "Ana sebeplerini özetle ve fikrini tekrar güçlü bir şekilde vurgula."
        },
        "Discussion (Discuss both views)": {
            "intro": "Her iki görüşü de tanıt ve kendi fikrinin/duruşunun ne olduğunu belirt.",
            "body1": "BİRİNCİ GÖRÜŞ: İnsanların bir kısmı neden böyle düşünüyor? Açıkla ve örnekle.",
            "body2": "İKİNCİ GÖRÜŞ: Diğerleri neden farklı düşünüyor? Kendi görüşünü de yedirerek açıkla.",
            "conclusion": "İki görüşü de kısaca özetle ve son kararını/fikrini netleştir."
        },
        "Problem & Solution": {
            "intro": "Verilen sorunu tanımla ve bu yazıda nedenleri ile olası çözümleri tartışacağını belirt.",
            "body1": "SORUNLAR/NEDENLER: Bu probleme ne yol açıyor? Temel sebepleri açıkla.",
            "body2": "ÇÖZÜMLER: Bu sorun nasıl çözülebilir? Hükümetler veya bireyler ne yapmalı?",
            "conclusion": "Sorunları ve önerdiğin temel çözümleri özetle."
        },
        "Advantages & Disadvantages": {
            "intro": "Konuyu tanıt ve bu durumun hem avantajları hem de dezavantajları olduğunu belirt.",
            "body1": "AVANTAJLAR: Bu durumun en büyük faydaları (pros) nelerdir? Örneklerle açıkla.",
            "body2": "DEZAVANTAJLAR: Bu durumun olumsuz yanları (cons) veya riskleri nelerdir?",
            "conclusion": "Avantaj ve dezavantajları özetle."
        }
    }
    hints = structure_hints[essay_type]

    # ADIM 1: OUTLINE
    with st.expander("📝 1. Adım: Outline (Taslak) Oluşturucu", expanded=(st.session_state.draft_step == 1)):
        col1, col2 = st.columns(2)
        with col1:
            intro_thesis = st.text_area("Giriş (Introduction):", placeholder=hints["intro"], height=100)
            body1 = st.text_area("Gelişme 1 (Body Paragraph 1):", placeholder=hints["body1"], height=150)
        with col2:
            body2 = st.text_area("Gelişme 2 (Body Paragraph 2):", placeholder=hints["body2"], height=150)
            conclusion = st.text_area("Sonuç (Conclusion):", placeholder=hints["conclusion"], height=100)
        
        if st.button("Outline'ı Onayla & Draft 1'e Geç"):
            st.session_state.outline = f"Intro: {intro_thesis}\nBody 1: {body1}\nBody 2: {body2}\nConclusion: {conclusion}"
            st.session_state.draft_step = 2
            st.rerun()

    # ADIM 2: DRAFT 1
    if st.session_state.draft_step >= 2:
        with st.expander("✍️ 2. Adım: İlk Taslağı (Draft 1) Yaz", expanded=(st.session_state.draft_step == 2)):
            st.info("Oluşturduğunuz Outline'a sadık kalarak ilk taslağınızı yazın. Gramer hatalarına takılmayın!")
            
            draft1_text = st.text_area("Draft 1 Metni:", height=300)
            d1_words = len(draft1_text.split()) if draft1_text else 0
            st.markdown(get_word_count_html(d1_words, "counter-d1"), unsafe_allow_html=True)
            
            if st.button("Koçtan Hızlı Geri Bildirim Al", type="primary"):
                if not draft1_text.strip():
                    st.warning("Lütfen Draft 1'i boş bırakmayın.")
                elif d1_words < 100:
                    st.error(f"Metniniz çok kısa ({d1_words} kelime). Lütfen en az 100 kelimelik bir metin girin.")
                elif d1_words > 500:
                    st.error(f"Metniniz çok uzun ({d1_words} kelime). Lütfen maksimum 500 kelime girin.")
                else:
                    with st.spinner("IELTS Koçu taslağını inceliyor..."):
                        bot = ESLFeedbackBot()
                        st.session_state.coach_feedback = bot.get_quick_coach_feedback(st.session_state.outline, draft1_text, essay_topic)
                        st.session_state.draft1_text = draft1_text
                        st.session_state.draft_step = 3
                        st.rerun()

    # ADIM 3: KOÇ FEEDBACK VE DRAFT 2
    if st.session_state.draft_step >= 3:
        st.markdown("### 🗣️ Koçun Geri Bildirimi")
        st.markdown(f'<div class="coach-card">\n\n{st.session_state.coach_feedback}\n\n</div>', unsafe_allow_html=True)
        
        st.markdown("### 🚀 3. Adım: Final Draft (Draft 2)")
        st.info("Koçun tavsiyelerini dikkate alarak metninizi son haline getirin. Bu metin detaylı analizine gidecektir.")
        
        draft2_text = st.text_area("Draft 2 (Final) Metni:", value=st.session_state.get("draft1_text", ""), height=400)
        d2_words = len(draft2_text.split()) if draft2_text else 0
        st.markdown(get_word_count_html(d2_words, "counter-d2"), unsafe_allow_html=True)
        
        if st.button("Final Draft'ı Acımasızca Analiz Et", type="primary"):
            if not draft2_text.strip():
                st.warning("Final draft boş olamaz.")
            elif d2_words < 100:
                st.error(f"Metniniz çok kısa ({d2_words} kelime). Lütfen en az 100 kelimelik bir metin girin.")
            elif d2_words > 500:
                st.error(f"Metniniz çok uzun ({d2_words} kelime). Lütfen maksimum 500 kelime girin.")
            else:
                with st.spinner("Examiner Final Draft'ını inceliyor..."):
                    bot = ESLFeedbackBot()
                    raw_result = bot.analyze_essay(draft2_text, tone, essay_topic)
                    # GÜNCELLENDİ: Hataları ayırıyoruz
                    html_text, report = parse_dual_output(raw_result)
                    st.session_state.final_html = html_text
                    st.session_state.final_report = report
                    st.session_state.draft_step = 4

    # FİNAL RAPORU
    if st.session_state.draft_step == 4:
        # GÜNCELLENDİ: Sarı oval hataların gösterimi
        st.markdown("### 🎯 Hatalı Metin Üzerinde Analiz")
        st.markdown(f'<div class="report-card" style="margin-bottom: 20px; font-size: 1.1rem; line-height: 2.2;">\n{st.session_state.final_html}\n</div>', unsafe_allow_html=True)
        
        st.markdown("### 👨‍🏫 Final IELTS Sınav Raporu")
        st.markdown(f'<div class="report-card">\n\n{st.session_state.final_report}\n\n</div>', unsafe_allow_html=True)

def main():
    # Sidebar - Navigasyon
    with st.sidebar:
        st.markdown("## 🛠️ Araç Seçimi")
        st.write("") 
        app_mode = st.radio(
            "Araç Seçimi:", 
            ["📝 Hızlı Analiz", "🏗️ IELTS Draft Creator"],
            label_visibility="collapsed" 
        )
        st.divider()
        st.markdown("### ⚙️ Ayarlar")
        tone = st.selectbox("Geri Bildirim Tonu", ["Destekleyici", "Profesyonel", "Sıkı ve Detaycı"], index=1)
        st.divider()
        st.caption("Tarık - Writing Mentor Project 2026")

    st.title("ESL Writing Mentor")
    
    if app_mode == "📝 Hızlı Analiz":
        render_fast_analysis(tone)
    elif app_mode == "🏗️ IELTS Draft Creator":
        render_draft_creator(tone)

with st.sidebar:
    st.divider()
    with st.expander("🔐 Gizlilik ve Kullanım"):
        st.caption("""
            Bu uygulama Hugging Face API'sini kullanmaktadır. 
            Girdiğiniz metinler analiz edilmek üzere şifreli olarak iletilir. 
            Lütfen şifre veya çok özel kişisel verilerinizi paylaşmayınız.
        """)
if __name__ == "__main__":
    main()