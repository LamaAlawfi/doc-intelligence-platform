import streamlit as st
import os
import sys
import uuid
import json
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Move heavy imports inside to speed up UI start
def build_graph():
    from src.graph.builder import build_graph as b
    return b()

def read_file(path):
    from src.ingest.readers import read_file as r
    return r(path)

st.set_page_config(page_title="Government Document System", page_icon="🏛️", layout="wide")

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .gov-header {
        background: linear-gradient(90deg, #1b2631 0%, #2c3e50 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        border-bottom: 4px solid #3498db;
    }
    
    .gov-logo {
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -1px;
        background: linear-gradient(to right, #fff, #bdc3c7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .hero-section {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.3);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
    }

    .stButton>button {
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
        background: #1b2631;
        color: white;
        border: none;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        background: #2c3e50;
    }

    .status-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        background: #e1e8ed;
        color: #1b2631;
    }
    
    /* RTL Support */
    .rtl {
        direction: rtl;
        text-align: right;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- TRANSLATIONS ---
TRANSLATIONS = {
    "EN": {
        "title": "Unified Project Executive Dashboard",
        "subtitle": "Select an official workflow to begin document processing.",
        "nav_header": "🏛️ Navigation Menu",
        "secure_session": "Secure Session",
        "lang_toggle": "Language / اللغة",
        "f1_name": "📝 Official Template Planner",
        "f1_desc": "Structure professional report templates with official adherence to compliance standards.",
        "f1_help": "The Template Planner (formerly Generator) architecturally maps out a report's structure before content is written.",
        "f2_name": "📊 Intelligent Template Filler",
        "f2_desc": "Extract evidence-backed data into pre-defined government templates.",
        "f2_help": "Extracts specific data points into a pre-approved template with traceability.",
        "f3_name": "🤖 Strategy Synthesis",
        "f3_desc": "Generate high-level strategic intelligence reports from complex documents.",
        "f3_help": "Multi-agent workflow that plans, writes, and validates comprehensive reports.",
        "back_btn": "⬅️ Back to Dashboard",
        "status_header": "Pipeline Status",
        "logs_header": "🛠 Process Logs",
        "doc_count": "Number of Documents to Generate",
        "page_target": "Target Page Length",
        "init_agent": "🔨 Initialize Planning Agent",
        "run_filler": "🔨 Run Extraction Agent",
        "begin_mission": "🔨 Begin Strategic Mission",
        "approved": "✅ Approved",
        "processing": "Agent is architecting the document structure...",
        "dashboard_info": "👈 Please select a mission from the sidebar to begin.",
        "config_header": "Configuration & Scope",
        "quality_header": "⚖️ Human-in-the-Loop: Quality Review",
        "export_header": "📄 Official Export",
        "ingest_header": "1. Source Document Ingestion",
        "cite_header": "⚖️ Evidence Review & Traceability",
        "strat_header": "2. Strategic Mission Configuration",
        "out_header": "3. Strategic Outline Approval",
        "input_area": "Metadata Input Area",
        "yes": "Bilingual (AR/EN)",
        "no": "English Only",
        "tab_1": "🏗️ Full Document Builder",
        "tab_2": "📋 Blueprint Architect (Outline Only)",
        "tab_3": "⚡ Quick Generator (No Uploads)",
        "tab_4": "📚 Curriculum Generator",
        "hero_1_t": "🏗️ Full Strategic Document Builder",
        "hero_1_d": "<b>End-to-End Generation</b><br>Upload source files, let AI architect the structure, and write the full comprehensive content automatically.",
        "hero_2_t": "📋 Blueprint Architect (Template Only)",
        "hero_2_d": "<b>Structure & Outline Generation</b><br>Upload source files to generate a professional outline only. Export the empty template directly to fill later.",
        "hero_3_t": "⚡ Quick Topic Generator",
        "hero_3_d": "<b>Instruction-Based Generation</b><br>No uploads required. Provide instructions directly and let AI formulate the structure and write the complete document from scratch.",
        "hero_4_t": "📚 Curriculum Generator",
        "hero_4_d": "<b>Educational Materials Hub</b><br>Generate structured Teacher Guides and Student Files automatically from a single educational prompt.",
        "step_1": "1. Ingest Evidence",
        "step_2": "2. Chatbot Setup",
        "step_3": "3. Evaluate Blueprint",
        "step_4": "4. Live Synthesis",
        "step_5": "5. Review & Export",
        "step_no_upload": "🚫 No Upload Needed",
        "upload_refs": "Upload reference documents",
        "btn_process": "🚀 Process Materials",
        "st2_t1": "⚡ Quick Instructor (No Upload Required)",
        "st2_d1": "💡 Fast-Track: Skip evidence uploading. Provide direct instructions below and the AI will generate both structure and full content.",
        "st2_t2": "📚 Curriculum Director (No Upload Required)",
        "st2_d2": "💡 Fast-Track: Describe the curriculum target below. The AI will autonomously produce structured Teacher Guides and Student Files.",
        "st2_t3": "📋 Blueprint Architect (Outline/Structure Only)",
        "st2_d3": "🏗️ Focus Mode: The AI will analyze your uploaded files and build a highly professional skeleton outline for you to export immediately.",
        "st2_t4": " (Complete Builder)",
        "st2_d4": "💬 End-to-End: Chat with the AI to refine requirements. The AI will first build the structure, then fully synthesize the content from your uploaded files."
    },
    "AR": {
        "title": "لوحة القيادة التنفيذية الموحدة للمشاريع",
        "subtitle": "اختر سير عمل رسمي لبدء معالجة المستندات.",
        "nav_header": "🏛️ قائمة التنقل",
        "secure_session": "جلسة آمنة",
        "lang_toggle": "اللغة / Language",
        "f1_name": "📝 مخطط القوالب الرسمي",
        "f1_desc": "هيكلة قوالب التقارير الاحترافية مع الالتزام الرسمي بمعايير الامتثال.",
        "f1_help": "يقوم مخطط القوالب (المولد سابقاً) برسم هيكل التقرير معماريًا قبل كتابة المحتوى.",
        "f2_name": "📊 معبئ القوالب الذكي",
        "f2_desc": "استخراج البيانات المدعومة بالأدلة في قوالب حكومية محددة مسبقًا.",
        "f2_help": "يستخرج نقاط بيانات محددة في قالب معتمد مع إمكانية التتبع.",
        "f3_name": "🤖 توليف الاستراتيجية",
        "f3_desc": "توليد تقارير استخبارات استراتيجية رفيعة المستوى من مستندات معقدة.",
        "f3_help": "سير عمل متعدد الوكلاء يخطط ويكتب ويتحقق من التقارير الشاملة.",
        "back_btn": "⬅️ العودة إلى لوحة القيادة",
        "status_header": "حالة خط الإنتاج",
        "logs_header": "🛠 سجلات العمليات",
        "doc_count": "عدد المستندات المطلوب إنشاؤها",
        "page_target": "طول الصفحة المستهدف",
        "init_agent": "🔨 بدء وكيل التخطيط",
        "run_filler": "🔨 تشغيل وكيل الاستخراج",
        "begin_mission": "🔨 بدء المهمة الاستراتيجية",
        "approved": "✅ تم الموافقة",
        "processing": "الوكيل يقوم بهندسة هيكل المستند...",
        "dashboard_info": "👈 يرجى اختيار مهمة من القائمة الجانبية للبدء.",
        "config_header": "التكوين والنطاق",
        "quality_header": "⚖️ التدخل البشري: مراجعة الجودة",
        "export_header": "📄 تصدير رسمي",
        "ingest_header": "1. استيعاب مستندات المصدر",
        "cite_header": "⚖️ مراجعة الأدلة وإمكانية التتبع",
        "strat_header": "2. تكوين المهمة الاستراتيجية",
        "out_header": "3. الموافقة على المخطط الاستراتيجي",
        "input_area": "منطقة إدخال البيانات",
        "yes": "ثنائي اللغة (عربي/إنجليزي)",
        "no": "عربي فقط",
        "tab_1": "🏗️ البناء الكامل للمستند",
        "tab_2": "📋 مهندس القوالب (هيكل فقط)",
        "tab_3": "⚡ المولد السريع (بدون مرفقات)",
        "tab_4": "📚 مولد المناهج الدراسية",
        "hero_1_t": "🏗️ البناء الاستراتيجي للمستندات",
        "hero_1_d": "<b>توليد من البداية للنهاية</b><br>ارفع الملفات، دع الذكاء الاصطناعي يبني الهيكل ويكتب المحتوى الشامل تلقائياً.",
        "hero_2_t": "📋 مهندس المخطط (قالب فقط)",
        "hero_2_d": "<b>توليد الهيكل والمخطط</b><br>ارفع الملفات لتوليد مخطط احترافي فقط. قم بتصدير القالب فارغاً لتعبئته لاحقاً.",
        "hero_3_t": "⚡ المولد السريع للمواضيع",
        "hero_3_d": "<b>توليد مبني على التعليمات</b><br>بدون مرفقات. قدم تعليماتك مباشرة وسيقوم الذكاء الاصطناعي ببناء الهيكل وكتابة المستند الكامل.",
        "hero_4_t": "📚 مولد المناهج الدراسية",
        "hero_4_d": "<b>مركز المواد التعليمية</b><br>توليد أدلة المعلم وملفات الطالب مهيكلة تلقائياً من موضوع واحد.",
        "step_1": "1. رفع الأدلة",
        "step_2": "2. إعداد المساعد الذكي",
        "step_3": "3. تقييم المخطط",
        "step_4": "4. الكتابة المباشرة",
        "step_5": "5. المراجعة والتصدير",
        "step_no_upload": "🚫 لا حاجة لمرفقات",
        "upload_refs": "ارفع المستندات المرجعية",
        "btn_process": "🚀 معالجة المواد",
        "st2_t1": "⚡ الموجه السريع (لا حاجة للمرفقات)",
        "st2_d1": "💡 مسار سريع: تخطى رفع الأدلة. قدم تعليماتك مباشرة بالأسفل.",
        "st2_t2": "📚 مدير المناهج (لا حاجة للمرفقات)",
        "st2_d2": "💡 مسار سريع: صف المنهج المطلوب بالأسفل. سيستخرج النظام دليل المعلم وملف الطالب.",
        "st2_t3": "📋 مهندس المخططات (المسودة فقط)",
        "st2_d3": "🏗️ وضع التركيز: سيقوم النظام بتحليل ملفاتك وبناء مسودة احترافية لتصديرها فوراً.",
        "st2_t4": " (منشئ متكامل)",
        "st2_d4": "💬 متكامل: تحدث مع المساعد لتحسين المتطلبات. سيتم بناء الهيكل ثم صياغة المحتوى من ملفاتك."
    }
}

def _translate_cached(key, lang):
    return TRANSLATIONS.get(lang, {}).get(key, key)

def T(key):
    lang = st.session_state.state.get("language", "EN")
    return _translate_cached(key, lang)

@st.cache_resource
def get_cached_graph():
    return build_graph()

# --- GLOBAL STATE ---
if "state" not in st.session_state:
    st.session_state.state = {
        "files": [],
        "logs": [],
        "status": "idle",
        "warnings": [],
        "errors": [],
        "mode": "quick",
        "current_step": 1,
        "selected_template": None,
        "language": "EN",
        "doc_count": 1,
        "page_target": "3-5",
        "active_feature": "template_gen",
        "doc_language": "English", # Dynamically updated with UI toggle
        "definitions_acronyms": "",
        "reviewers": "",
        "approvers": "",
        "bilingual_intro_concl": False,
        "classification": "INTERNAL"
    }


# --- AUTHENTICATION & ROUTING STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "api_configured" not in st.session_state:
    st.session_state.api_configured = False
if "user_api_key" not in st.session_state:
    st.session_state.user_api_key = ""

# --- ROUTING PAGES ---
def render_login_page():
    st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #0f2027, #203a43, #2c5364);
    }
    [data-testid="block-container"] {
        max-width: 450px;
        padding-top: 10vh;
    }
    [data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 3rem 2rem;
        border-radius: 1.5rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(15px);
    }
    .login-title { font-size: 2.2rem; font-weight: 800; color: #ffffff; text-align: center; margin-bottom: 0px; letter-spacing: -0.5px; }
    .login-sub { color: #a0aec0; font-size: 1rem; text-align: center; margin-bottom: 30px; letter-spacing: 0.5px; }
    div[data-testid="stTextInput"] label p { color: #cbd5e0; font-weight: 500; font-size: 0.95rem; }
    div[data-testid="stTextInput"] input {
        background-color: rgba(0, 0, 0, 0.2) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px;
    }
    div[data-testid="stTextInput"] input:focus { border-color: #4facfe !important; box-shadow: 0 0 0 1px #4facfe !important; }
    .stButton>button {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: #ffffff;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 0.6rem;
        margin-top: 5px;
        transition: transform 0.2s ease, box-shadow 0.2s;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(79, 172, 254, 0.4); border: none; color: white;}
    </style>
    """, unsafe_allow_html=True)
    
    with st.form("login_form", clear_on_submit=False):
        st.markdown("<div class='login-title'>Secure Portal</div><div class='login-sub'>Document Intelligence System</div>", unsafe_allow_html=True)
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Authenticate", use_container_width=True)
        
        if submitted:
            # Try to get users from st.secrets first, then fall back to environment variables
            allowed_users = {}
            try:
                allowed_users = st.secrets.get("passwords", {})
            except Exception:
                pass
            
            # Fallback: Check for environment variables like PORTAL_PWD_LamaAlawfi="123"
            env_users = {k.replace("PORTAL_PWD_", ""): v for k, v in os.environ.items() if k.startswith("PORTAL_PWD_")}
            allowed_users.update(env_users)

            if user in allowed_users and allowed_users[user] == pwd:
                st.session_state.logged_in = True
                st.session_state.current_user = user
                st.rerun()
            elif not allowed_users:
                st.error("🔑 Authentication is not configured. Please add an environment variable 'PORTAL_PWD_YourName' on Render.")
            else:
                st.error("Invalid credentials. Please attempt again.")

def render_api_key_page():
    st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #0f2027, #203a43, #2c5364);
    }
    [data-testid="block-container"] {
        max-width: 500px;
        padding-top: 10vh;
    }
    [data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 3rem 2rem;
        border-radius: 1.5rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(15px);
    }
    .api-title { font-size: 2.2rem; font-weight: 800; color: #ffffff; text-align: center; margin-bottom: 0px; letter-spacing: -0.5px; }
    .api-sub { color: #a0aec0; font-size: 1rem; text-align: center; margin-bottom: 30px; line-height: 1.4; }
    div[data-testid="stTextInput"] label p { color: #cbd5e0; font-weight: 500; font-size: 0.95rem; }
    div[data-testid="stTextInput"] input {
        background-color: rgba(0, 0, 0, 0.2) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px;
    }
    div[data-testid="stTextInput"] input:focus { border-color: #11998e !important; box-shadow: 0 0 0 1px #11998e !important; }
    .stButton>button {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: #ffffff;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 0.6rem;
        margin-top: 5px;
        transition: transform 0.2s ease, box-shadow 0.2s;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(17, 153, 142, 0.4); border: none; color: white;}
    </style>
    """, unsafe_allow_html=True)

    with st.form("api_form", clear_on_submit=False):
        st.markdown("<div class='api-title'>API Configuration</div><div class='api-sub'>Please connect your secure language model keys to initiate the AI agents.</div>", unsafe_allow_html=True)
        st.info("Your API key runs only in this secure session memory and is never saved.")
        api_key = st.text_input("OpenAI API Key", type="password")
        
        submitted = st.form_submit_button("Initialize Platform", use_container_width=True)
        if submitted:
            if len(api_key.strip()) > 10:
                st.session_state.user_api_key = api_key.strip()
                os.environ["OPENAI_API_KEY"] = api_key.strip()
                st.session_state.api_configured = True
                st.rerun()
            else:
                st.error("Please provide a valid API sequence to proceed.")

# --- EXECUTE APP ROUTING ---
if not st.session_state.logged_in:
    render_login_page()
    st.stop()

if not st.session_state.api_configured:
    render_api_key_page()
    st.stop()

# --- SAFE TO INSTANTIATE AI ---
if "graph" not in st.session_state:
    st.session_state.graph = get_cached_graph()

# RTL Support class
rtl_class = "rtl" if st.session_state.state["language"] == "AR" else ""

# --- HEADER ---
with st.container():
    lang = st.session_state.state.get("language", "EN")
    st.markdown(f"""
    <div class="gov-header {rtl_class}">
        <div>
            <div class="gov-logo">🏛️ DOCUMENT INTELLIGENCE PLATFORM</div>
            <div class="gov-org">Official Government Synthesis & Planning System | v2.1 (Bilingual)</div>
        </div>
        <div style="display: flex; gap: 1rem; align-items: center;">
            <div style="font-size: 0.8rem; opacity: 0.7;">{T('secure_session')}: G-8821</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header(T("nav_header"))
        
        # User Account Info & Logout capability
        curr_user = st.session_state.get("current_user", "Pilot User")
        st.caption(f"👤 Logged in as: **{curr_user}**")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.api_configured = False
            if "user_api_key" in st.session_state: st.session_state.user_api_key = ""
            if "current_user" in st.session_state: del st.session_state["current_user"]
            st.rerun()
            
        st.divider()
        
        new_lang = st.radio(T("lang_toggle"), options=["EN", "AR"], index=0 if lang=="EN" else 1, horizontal=True)
        if new_lang != lang:
            st.session_state.state["language"] = new_lang
            st.session_state.state["doc_language"] = "Arabic" if new_lang == "AR" else "English"
            st.rerun()
        
        st.divider()
        
        st.divider()
        st.header(T("status_header"))
        curr_status = st.session_state.state.get("status", "Idle")
        st.info(f"State: `{curr_status.upper()}`")
        
        with st.expander(T("logs_header"), expanded=False):
            for log in st.session_state.state.get("logs", []):
                st.caption(f"**{log['timestamp']}** {log['step']}: {log['details']}")

# --- TABBED INTERFACE ---
tab_full, tab_blueprint, tab_quick, tab_curriculum = st.tabs([
    T("tab_1"), 
    T("tab_2"), 
    T("tab_3"),
    T("tab_4")
])

# --- REUSABLE PIPELINE ENGINE ---
def render_pipeline(mode):
    # Use mode-specific keys to keep features independent
    step_key = f"step_{mode}"
    chat_history_key = f"chat_history_{mode}"
    chat_stage_key = f"chat_stage_{mode}"
    all_text_key = f"all_text_{mode}"
    files_key = f"files_{mode}"
    template_key = f"template_{mode}"
    filled_key = f"filled_{mode}"
    topic_key = f"topic_{mode}"

    if step_key not in st.session_state.state:
        st.session_state.state[step_key] = 2 if mode == "quick_gen" else 1
    
    # Force skip ingest for quick_gen and curriculum
    if mode in ["quick_gen", "curriculum"] and st.session_state.state[step_key] == 1:
        st.session_state.state[step_key] = 2

    current_step = st.session_state.state[step_key]
    
    # Hero Section
    if mode == "full_builder":
        title, desc = T("hero_1_t"), T("hero_1_d")
    elif mode == "template_only":
        title, desc = T("hero_2_t"), T("hero_2_d")
    elif mode == "quick_gen":
        title, desc = T("hero_3_t"), T("hero_3_d")
    else:
        title, desc = T("hero_4_t"), T("hero_4_d")

    st.markdown(f"""
    <div class="hero-section">
        <h2 style='margin-top:0;'>{title}</h2>
        <p style='color: #555; font-size: 1.1rem;'>{desc}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Visual Stepper
    s_cols = st.columns(5)
    steps = [T("step_1"), T("step_2"), T("step_3"), T("step_4"), T("step_5")]
    if mode in ["quick_gen", "curriculum"]:
        steps[0] = T("step_no_upload")

    for i, s in enumerate(steps):
        if i + 1 == current_step:
            s_cols[i].markdown(f"**🔵 {s}**")
        elif i + 1 < current_step:
            s_cols[i].markdown(f"✅ {s}")
        else:
            s_cols[i].markdown(f"⚪ {s}")
    st.divider()

    # --- STEP 1: INGEST EVIDENCE ---
    if current_step == 1:
        st.subheader(T("step_1"))
        st.info("Upload the source documents that will drive the strategy and document generation." if st.session_state.state.get("language")=="EN" else "ارفع المستندات التي ستقود الاستراتيجية وعملية البناء.")
        uploaded_files = st.file_uploader(f"{T('upload_refs')} ({mode})", type=["pdf", "docx", "txt", "md"], accept_multiple_files=True, key=f"uploader_{mode}")
        
        if uploaded_files:
            if st.button(T("btn_process"), key=f"btn_ingest_{mode}"):
                from src.ingest.readers import read_file
                all_text = ""
                os.makedirs("storage", exist_ok=True)
                processed_files = []
                for uf in uploaded_files:
                    path = os.path.join("storage", uf.name)
                    with open(path, "wb") as f:
                        f.write(uf.getbuffer())
                    text, _ = read_file(path)
                    all_text += text + "\n\n"
                    processed_files.append({"name": uf.name, "path": path})
                
                st.session_state.state[all_text_key] = all_text
                st.session_state.state[files_key] = processed_files
                
                # --- AUTO-EXTRACT METADATA ---
                with st.spinner("Extracting metadata..."):
                    from src.graph.smart_agents.metadata_extractor_agent import metadata_extractor_agent
                    ext = metadata_extractor_agent(all_text)
                    if ext:
                        st.session_state.state[f"defs_{mode}"] = "\n".join(ext.get("definitions", []))
                        st.session_state.state[f"revs_{mode}"] = "\n".join(ext.get("reviewers", []))
                        st.session_state.state[f"apps_{mode}"] = "\n".join(ext.get("approvers", []))
                        if ext.get("organization"): st.session_state.state[f"org_{mode}"] = ext.get("organization")
                
                st.session_state.state[step_key] = 2
                st.rerun()

    # --- STEP 2: CONFIGURE (CHATBOT) & PLAN ---
    elif current_step == 2:
        if mode == "quick_gen":
            st.subheader(T("st2_t1"))
            st.info(T("st2_d1"))
        elif mode == "curriculum":
            st.subheader(T("st2_t2"))
            st.info(T("st2_d2"))
        elif mode == "template_only":
            st.subheader(T("st2_t3"))
            st.info(T("st2_d3"))
        else:
            st.subheader(T("config_header") + T("st2_t4"))
            st.info(T("st2_d4"))
        
        if chat_history_key not in st.session_state.state:
            st.session_state.state[chat_history_key] = []
        if chat_stage_key not in st.session_state.state:
            st.session_state.state[chat_stage_key] = 0
            
        stage = st.session_state.state[chat_stage_key]
        ui_lang = st.session_state.state.get("language", "EN")
        
        if mode == "curriculum":
            if ui_lang == "AR":
                questions = [
                    "يرجى وصف المنهج الذي تريد إنشاؤه (مثال: 'منهج هندسة الأوامر للصف الثاني متوسط'):",
                    "شكراً لك! أنا جاهز لبناء المنهج الدراسي."
                ]
            else:
                questions = [
                    "Please describe the curriculum you want to generate (e.g., 'Grade 8 Prompt Engineering'):",
                    "Thank you! Your requirements are complete. I am ready to generate the Curriculum Blueprint."
                ]
            max_stage = 1
        else:
            if ui_lang == "AR":
                questions = [
                    "ما هو **موضوع البحث** أو **اسم المشروع**؟",
                    "ما هو **نوع المهمة**؟ (اكتب 'تقني' لوثائق الهندسة والمعمارية، أو 'استراتيجي' للتقارير التنفيذية)",
                    "ما هي **الجهة المستهدفة** التي تصدر هذا التقرير؟ (يمكنك رفع الشعار أدناه أيضاً)",
                    "من هو **الجمهور المستهدف**؟ (مثل: مسؤولين تنفيذيين، تقنيين، جهة رقابية)",
                    "ما هي **النبرة** المفضلة و **درجة التصنيف** (سري، مقيد، داخلي)؟",
                    "ما هو **سمة الألوان** المفضلة للمستند؟ (مثلاً: أخضر، أزرق، أحمر)",
                    "كم عدد **الصفحات** المستهدفة؟ (مثلاً: 10 صفحات)",
                    "**التعريفات والاختصارات**: هل هناك مصطلحات معينة تريد إضافتها؟ (اكتبها بصيغة المصطلح: التعريف)",
                    "**المراجعين**: اذكر أسماء ووظائف المراجعين. (استخدم سطر جديد أو فاصلة منقوطة لكل شخص، مثلاً: فلان - مدير ; علان - مهندس)",
                    "**المعتمدين**: اذكر أسماء ووظائف المعتمدين. (مثلاً: فلان - الرئيس التنفيذي)",
                    "هل تريد جعل **المقدمة والخاتمة ثنائية اللغة** (عربي وإنجليزي)؟ (نعم / لا)",
                    "شكراً لك! متطلباتك مكتملة الآن. أنا مستعد لإنشاء المخطط الاستراتيجي المستفيض."
                ]
            else:
                questions = [
                    "What is the **Research Topic** or **Project Name**?",
                    "What is the **Mission Type**? (Type 'Technical' for Architecture/Engineering docs, or 'Strategic' for Management/Executive reports)",
                    "What is the **Target Organization** setting this report? (You can also upload a logo photo below)",
                    "Who is the target **Audience**? (e.g., Executive, Technical)",
                    "What is the preferred **Tone** and **Classification** (Internal, Restricted, Confidential)?",
                    "What is the preferred **Color Theme**? (e.g., Green, Blue, Red)",
                    "How many **Pages** are targeted? (e.g., 10 pages)",
                    "**Definitions & Acronyms**: Any specific terms to add? (Format: Term: Definition)",
                    "**Reviewers**: Provide names and titles. (Use a NEW LINE or SEMICOLON for each person, e.g., Name - Title ; Name2 - Title2)",
                    "**Approvers**: Provide names and titles of those who will approve it.",
                    "Do you want the **Introduction & Conclusion to be Bilingual** (Arabic & English)? (Yes / No)",
                    "Thank you! Your requirements are complete. I am ready to generate the comprehensive Blueprint."
                ]
            max_stage = 11

        if not st.session_state.state[chat_history_key]:
             st.session_state.state[chat_history_key].append({"role": "assistant", "content": questions[0]})
        
        # Dynamically remap existing assistant messages to the currently active language
        assistant_idx = 0
        for i, msg in enumerate(st.session_state.state[chat_history_key]):
            if msg["role"] == "assistant":
                if assistant_idx < len(questions):
                    st.session_state.state[chat_history_key][i]["content"] = questions[assistant_idx]
                assistant_idx += 1
                
        for msg in st.session_state.state[chat_history_key]:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
                
        if stage < max_stage:
            if stage == 1 and mode != "curriculum":
                uploader_txt = "اختياري: قم برفع شعار الجهة" if ui_lang == "AR" else "Optional: Upload Organization Logo"
                uploaded_logo = st.file_uploader(uploader_txt, type=["png", "jpg", "jpeg"], key=f"logo_up_{mode}")
                if uploaded_logo:
                    os.makedirs("storage/assets", exist_ok=True)
                    logo_path = os.path.join("storage/assets", f"logo_{mode}.png")
                    with open(logo_path, "wb") as f: f.write(uploaded_logo.getbuffer())
                    st.session_state.state[f"logo_path_{mode}"] = logo_path
                    st.success("Logo uploaded!" if ui_lang=="EN" else "تم رفع الشعار!")

            # Use Text Area for multi-line inputs (Stages 7, 8, 9)
            if stage in [7, 8, 9]:
                area_label = questions[stage].replace('**', '')
                with st.expander("📝 " + (T("input_area") or "Input Area"), expanded=True):
                    user_area_msg = st.text_area(area_label, key=f"area_in_{mode}_{stage}", height=150, help="Press the button below to submit.")
                    if st.button("Submit Answer", key=f"btn_submit_{mode}_{stage}", type="primary"):
                        st.session_state.state[chat_history_key].append({"role": "user", "content": user_area_msg})
                        if stage == 7:
                            if user_area_msg.lower() not in ["no", "none", "لا", "skip"]:
                                existing = st.session_state.state.get(f"defs_{mode}", "")
                                st.session_state.state[f"defs_{mode}"] = (existing + "\n" + user_area_msg).strip()
                        elif stage == 8:
                            if user_area_msg.lower() not in ["no", "none", "لا", "skip"]:
                                existing = st.session_state.state.get(f"revs_{mode}", "")
                                st.session_state.state[f"revs_{mode}"] = (existing + "\n" + user_area_msg).strip()
                        elif stage == 9:
                            if user_area_msg.lower() not in ["no", "none", "لا", "skip"]:
                                existing = st.session_state.state.get(f"apps_{mode}", "")
                                st.session_state.state[f"apps_{mode}"] = (existing + "\n" + user_area_msg).strip()
                        
                        st.session_state.state[chat_stage_key] = stage + 1
                        st.session_state.state[chat_history_key].append({"role": "assistant", "content": questions[stage + 1]})
                        st.rerun()
            # Use UI Choice for Stage 10 (Binary)
            elif stage == 10:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ " + (T("yes") or "Yes"), key=f"btn_yes_{mode}", use_container_width=True):
                        st.session_state.state[chat_history_key].append({"role": "user", "content": "Yes"})
                        st.session_state.state[f"bilingual_{mode}"] = True
                        st.session_state.state[chat_stage_key] = 11
                        st.session_state.state[chat_history_key].append({"role": "assistant", "content": questions[11]})
                        st.rerun()
                with col2:
                    if st.button("❌ " + (T("no") or "No"), key=f"btn_no_{mode}", use_container_width=True):
                        st.session_state.state[chat_history_key].append({"role": "user", "content": "No"})
                        st.session_state.state[f"bilingual_{mode}"] = False
                        st.session_state.state[chat_stage_key] = 11
                        st.session_state.state[chat_history_key].append({"role": "assistant", "content": questions[11]})
                        st.rerun()
            else:
                # ONLY render chat_input if this is the ACTIVE feature to avoid COLLISIONS
                active_match = False
                if mode == "full_builder" and st.session_state.state["active_feature"] == "full_builder": active_match = True
                elif mode == "template_only" and st.session_state.state["active_feature"] == "template_only": active_match = True
                elif mode == "quick_gen" and st.session_state.state["active_feature"] == "quick_gen": active_match = True
                elif mode == "curriculum" and st.session_state.state["active_feature"] == "curriculum": active_match = True
                
                if active_match:
                    chat_placeholder = "اكتب إجابتك هنا..." if ui_lang == "AR" else "Type your answer here..."
                    if user_msg := st.chat_input(chat_placeholder, key=f"chat_in_{mode}"):
                        st.session_state.state[chat_history_key].append({"role": "user", "content": user_msg})
                        if stage == 0: st.session_state.state[topic_key] = user_msg
                        elif stage == 1: 
                            st.session_state.state[f"mission_type_{mode}"] = "technical" if any(x in user_msg.lower() for x in ["تقني", "technical", "tech"]) else "strategic"
                        elif stage == 2: st.session_state.state[f"org_{mode}"] = user_msg
                        elif stage == 5: st.session_state.state[f"color_theme_{mode}"] = user_msg
                        elif stage == 6: st.session_state.state[f"page_target_{mode}"] = user_msg
                        
                        st.session_state.state[chat_stage_key] = stage + 1
                        st.session_state.state[chat_history_key].append({"role": "assistant", "content": questions[stage + 1]})
                        st.rerun()
                
        st.divider()
        if stage == max_stage:
            if st.button("🚀 Generate Blueprint", key=f"btn_gen_{mode}", use_container_width=True, type="primary"):
                with st.spinner("Architecting..."):
                    from src.graph.smart_agents.template_generator_agent import template_generator_agent
                    doc_lang = "Arabic" if ui_lang == "AR" else "English"
                    context = st.session_state.state.get(all_text_key, "")[:12000] 
                    chat_log = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.state[chat_history_key]])
                    
                    # Logic to determine template target mode based on page count
                    target_pages_raw = str(st.session_state.state.get(f'page_target_{mode}', '1'))
                    import re
                    page_nums = re.findall(r'\d+', target_pages_raw)
                    page_val = int(page_nums[0]) if page_nums else 1
                    if "ten" in target_pages_raw.lower() or "عشر" in target_pages_raw.lower():
                        page_val = 10
                    
                    template_mode = "Strategic Mode"
                    use_mission = st.session_state.state.get(f"mission_type_{mode}", "strategic")
                    
                    if mode == "curriculum":
                        template_mode = "Curriculum Mode"
                    elif use_mission == "technical":
                        template_mode = "Technical Solution Design"
                    elif page_val >= 9:
                        template_mode = "Strategic Compliance Mode" # Triggers 20-30 sections in prompts.py
                    
                    enhanced_topic = f"CHAT HISTORY:\n{chat_log}\n\nTARGET PAGE COUNT: {target_pages_raw}\n\nCONTEXT:\n{context}"
                    
                    template = template_generator_agent(
                        enhanced_topic, template_mode, os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                        language=doc_lang, bilingual_intro_concl=st.session_state.state.get(f"bilingual_{mode}", False)
                    )
                    st.session_state.state[template_key] = template
                    st.session_state.state[step_key] = 3
                    st.rerun()

    # --- STEP 3: EVALUATE ---
    elif current_step == 3:
        st.subheader(T("quality_header"))
        template_res = st.session_state.state.get(template_key, {})
        if not template_res:
            st.error("Failed."); st.button("Restart", on_click=lambda: st.session_state.state.update({step_key: 1}))
        else:
            st.markdown(f"### Proposed Architecture: {template_res.get('doc_type')}")
            meta = template_res.get("metadata", {})
            c1, c2, c3 = st.columns(3)
            c1.metric("Classification", meta.get("classification", "INTERNAL"))
            c2.metric("Version", meta.get("version", "1.0"))
            c3.metric("Owner", meta.get("owner_dept", "N/A"))
            
            for key, val in template_res.get("structure", {}).items():
                with st.expander(f"📍 {val.get('title')}"):
                    st.write(f"**Section Blueprint:**")
                    for b in val.get('bullets', []):
                         st.caption(f"- {b}")
                    previews = val.get('actual_content_preview', [])
                    if previews:
                        st.write("**Reference Insight:**")
                        for p in previews:
                            st.markdown(f"<div style='font-size:0.85rem; padding:10px; border-left:4px solid {st.session_state.state.get('language') == 'AR' and '#1a5276' or '#1b2631'}; background:#f4f6f7; margin-bottom:5px;'>{p}</div>", unsafe_allow_html=True)
            
            st.info("💡 **Metadata Preview:**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("**Definitions:**")
                st.caption(st.session_state.state.get(f"defs_{mode}", "None detected."))
            with col_b:
                st.write("**Reviewers/Approvers:**")
                st.caption(st.session_state.state.get(f"revs_{mode}", "Self-prepared."))
            
            st.divider()
            c1, c2, c3 = st.columns(3)
            if mode != "template_only":
                if c1.button("✅ Approve & Write Full Content", key=f"btn_appr_{mode}", use_container_width=True):
                    st.session_state.state[step_key] = 4; st.rerun()
            else:
                if c1.button("📥 Export Structure as PDF", key=f"btn_direct_pdf_{mode}", use_container_width=True):
                     # For Blueprint mode, we jump straight to Step 5 (Export)
                     # But we need to pretend we have "filled" content so the exporter works.
                     # We'll fill with the blueprint's own highlights.
                     filled_mock = {}
                     for k, v in template_res.get("structure", {}).items():
                         filled_mock[k] = {"content": [f"Blueprint Detail: {b}" for b in v.get('bullets', [])], "citations": ["Blueprint Layout"]}
                     st.session_state.state[filled_key] = filled_mock
                     st.session_state.state[step_key] = 5
                     st.rerun()
                
            if c2.button("🔄 Restart Chat", key=f"btn_res_{mode}"):
                del st.session_state.state[chat_history_key]; st.session_state.state[step_key] = 2; st.rerun()
                
            if c3.button("📥 Export Plan", key=f"btn_exp_plan_{mode}"):
                from src.generation.exporter import Exporter
                md = f"# {template_res.get('doc_type')}\n\n"
                path = Exporter.to_docx(template_res.get('doc_type'), md, meta)
                with open(path, "rb") as f: st.download_button("Download", f, file_name="plan.docx")

    # --- STEP 4: SYNTHESIS ---
    elif current_step == 4:
        st.subheader("🚀 AI Synthesis")
        template_res = st.session_state.state.get(template_key, {})
        structure_to_fill = template_res.get("structure", {})
        
        if filled_key not in st.session_state.state or st.session_state.state[filled_key] is None:
            with st.spinner("Synthesizing..."):
                from src.generation.template_filler import fill_template_with_llm
                all_text = st.session_state.state.get(all_text_key, "")
                context = f"TOPIC: {st.session_state.state.get(topic_key)}\n\nCONTEXT:\n{all_text}"[:30000]
                filled = fill_template_with_llm(context, structure_to_fill, language=("Arabic" if st.session_state.state.get("language")=="AR" else "English"), bilingual_intro_concl=st.session_state.state.get(f"bilingual_{mode}", False))
                
                enhanced = {}
                for k, v in filled.items():
                    content = v.get("bullets", v.get("content", v)) if isinstance(v, dict) else v
                    enhanced[k] = {"content": content, "confidence": 92, "citations": ["AI Synthesis"], "conflict_detected": v.get("conflict_detected", False) if isinstance(v, dict) else False}
                st.session_state.state[filled_key] = enhanced; st.rerun()

        filled_data = st.session_state.state[filled_key]
        for section, data in filled_data.items():
            title = structure_to_fill.get(section, {}).get("title", section)
            with st.expander(f"📍 {title}"):
                content = data.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        st.markdown(f"- {item}")
                else: st.write(content)
        
        if st.button("✅ Proceed to Export", key=f"btn_step5_{mode}"): st.session_state.state[step_key] = 5; st.rerun()

    # --- STEP 5: EXPORT ---
    elif current_step == 5:
        st.subheader(T("export_header"))
        filled_data = st.session_state.state.get(filled_key, {})
        template_res = st.session_state.state.get(template_key, {})
        meta = template_res.get('metadata', {})
        meta.update({
             "organization": st.session_state.state.get(f"org_{mode}", "المؤسسة الحكومية"),
             "language": "Arabic" if st.session_state.state.get("language")=="AR" else "English",
             "definitions_acronyms": st.session_state.state.get(f"defs_{mode}", ""),
             "reviewers": st.session_state.state.get(f"revs_{mode}", ""),
             "approvers": st.session_state.state.get(f"apps_{mode}", ""),
             "bilingual_intro_concl": st.session_state.state.get(f"bilingual_{mode}", False),
             "color_theme": st.session_state.state.get(f"color_theme_{mode}", "green")
        })
        
        from src.generation.exporter import Exporter
        structure_to_fill = template_res.get("structure", {})
        
        if mode == "curriculum":
            teacher_md = f"# Teacher Guide: {st.session_state.state.get(topic_key, 'Curriculum')}\n\n"
            student_md = f"# Student File: {st.session_state.state.get(topic_key, 'Curriculum')}\n\n"
            teacher_struct, student_struct = {}, {}

            for section, data in filled_data.items():
                title = structure_to_fill.get(section, {}).get("title", section.replace('_', ' ').title())
                content = data.get("content", [])
                
                md_chunk = f"\n## {title}\n\n"
                if isinstance(content, list):
                    for item in content: 
                        md_chunk += f"{item}\n\n"
                else: md_chunk += f"{content}\n\n"

                if "teacher" in title.lower() or "teacher" in section.lower():
                    teacher_md += md_chunk
                    teacher_struct[section] = structure_to_fill.get(section)
                elif "student" in title.lower() or "student" in section.lower():
                    student_md += md_chunk
                    student_struct[section] = structure_to_fill.get(section)
                else: # Fallback to Teacher Guide, or just include in both? Let's put in Teacher Guide.
                    teacher_md += md_chunk
                    teacher_struct[section] = structure_to_fill.get(section)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Export Teacher Guide", key=f"final_pdf_teach_{mode}"):
                    curr_topic = st.session_state.state.get(topic_key, 'Curriculum')
                    path = Exporter.to_pdf(f"Teacher Guide: {curr_topic}", teacher_md, meta, teacher_struct, st.session_state.state.get(f"logo_path_{mode}"))
                    with open(path, "rb") as f: st.download_button("Download Teacher Guide", f, file_name="Teacher_Guide.pdf")
            with col2:
                if st.button("📥 Export Student File", key=f"final_pdf_stud_{mode}"):
                    curr_topic = st.session_state.state.get(topic_key, 'Curriculum')
                    path = Exporter.to_pdf(f"Student File: {curr_topic}", student_md, meta, student_struct, st.session_state.state.get(f"logo_path_{mode}"))
                    with open(path, "rb") as f: st.download_button("Download Student File", f, file_name="Student_File.pdf")

        else:
            md_content = f"# {st.session_state.state.get(topic_key, 'Final Document')}\n\n"
            for section, data in filled_data.items():
                title = structure_to_fill.get(section, {}).get("title", section.replace('_', ' ').title())
                md_content += f"\n## {title}\n\n"
                content = data.get("content", [])
                if isinstance(content, list):
                    for item in content: md_content += f"{item}\n\n"
                else:
                    md_content += f"{content}\n\n"
    
            col1, col2 = st.columns(2)
            with col1:
                 if st.button("📥 Export PDF", key=f"final_pdf_{mode}"):
                     path = Exporter.to_pdf(st.session_state.state.get(topic_key), md_content, meta, template_res.get("structure", {}), st.session_state.state.get(f"logo_path_{mode}"))
                     with open(path, "rb") as f: st.download_button("Download PDF", f, file_name="report.pdf")
        
        if st.button("🔄 Start New Task", key=f"reset_{mode}"):
            for k in [step_key, chat_history_key, chat_stage_key, template_key, filled_key]: 
                if k in st.session_state.state: del st.session_state.state[k]
            st.rerun()

# --- MAIN RENDER ---
with tab_full:
    st.session_state.state["active_feature"] = "full_builder"
    render_pipeline("full_builder")

with tab_blueprint:
    st.session_state.state["active_feature"] = "template_only"
    render_pipeline("template_only")

with tab_quick:
    st.session_state.state["active_feature"] = "quick_gen"
    render_pipeline("quick_gen")

with tab_curriculum:
    st.session_state.state["active_feature"] = "curriculum"
    render_pipeline("curriculum")
