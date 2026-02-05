import streamlit as st
import time
import requests
from bs4 import BeautifulSoup
import urllib.parse
import json
import re
import google.generativeai as genai

# ==========================================
# 🧠 REAL AI ENGINE
# ==========================================

class ScalerAIEngine:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash') 
        self.base_review_url = "https://www.scaler.com/review/"

    def scrape_website(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.find('h1').get_text().strip() if soup.find('h1') else "Scaler Masterclass"
                text = soup.get_text(separator=' ', strip=True)[:4000]
                return {"status": "success", "text": text, "title": title}
            else:
                return {"status": "error", "msg": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "msg": str(e)}

    def generate_quiz_with_gemini(self, context_text):
        prompt = f"""
        Act as a Senior Technical Instructor. Analyze this curriculum: '''{context_text}'''
        Task: Create a 5-question multiple-choice diagnostic quiz.
        Requirements:
        1. Questions must test PRE-REQUISITE knowledge for this specific topic.
        2. Output valid JSON.
        
        JSON Structure:
        [
            {{"id": 1, "q": "Question?", "options": ["A", "B", "C", "D"], "correct": "Correct Option String", "topic": "Topic Name"}}
        ]
        """
        try:
            response = self.model.generate_content(prompt)
            clean_json = re.sub(r'```json\n|```', '', response.text).strip()
            return json.loads(clean_json)
        except:
            return []

    def generate_short_report(self, quiz_results, total_score, max_score, user_name):
        """ 
        Generates a SHORT, punchy report.
        """
        performance_summary = f"Score: {total_score}/{max_score}\n"
        for res in quiz_results:
            status = "Correct" if res['is_correct'] else "Incorrect"
            performance_summary += f"- {res['topic']}: {status}\n"

        prompt = f"""
        Write a very short feedback summary for {user_name} based on this quiz performance:
        {performance_summary}

        Constraints:
        1. Max 100 words.
        2. Use 3 Bullet points max.
        3. Tone: High-energy, encouraging, constructive.
        4. Focus on how the Masterclass fills the specific gaps found.
        5. No formatting (like markdown bolding) inside the bullets to keep it clean.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except:
            return "Good effort! This Masterclass is exactly what you need to bridge your gaps."

    def generate_smart_link_data(self, company_name, grad_year):
        """ Returns both the URL and the Human-Readable Filter Text """
        service_companies = ["infosys", "tcs", "wipro", "cognizant", "accenture", "capgemini", "hcl", "tech mahindra"]
        current_year = 2026
        yoe = current_year - grad_year
        filters = []
        
        # Display Text Logic
        current_status = "Product Company"
        target_status = "Tech Giant"
        
        company_clean = company_name.lower().strip()
        is_service = any(svc in company_clean for svc in service_companies)
        
        if is_service:
            filters.append("Service To Product")
            current_status = "Service Based"
            target_status = "Product Based"
        else:
            filters.append("Service To Product") # Default

        if yoe <= 2:
            filters.append("Fresher")
            exp_text = "Fresher (0-2 YOE)"
        elif 2 < yoe <= 6:
            filters.append("2 To 5 Years Experience")
            exp_text = "Intermediate (2-6 YOE)"
        else:
            filters.append("6 To 10 Years Experience")
            exp_text = "Senior (6+ YOE)"
            
        query = urllib.parse.quote(" ".join(filters))
        url = f"{self.base_review_url}?filter={query}"
        
        return {
            "url": url,
            "current": f"{current_status} ({company_name})",
            "target": target_status,
            "exp": exp_text
        }

# ==========================================
# 🖥️ STREAMLIT FRONTEND
# ==========================================

st.set_page_config(page_title="Scaler AI Skill-Bridge", page_icon="🚀", layout="centered")

# CSS FIXES (White text on White bg fixed)
st.markdown("""
<style>
    .stButton>button {width: 100%; border-radius: 5px; font-weight: bold;}
    
    /* Report Box Styling */
    .report-box {
        background-color: #f0f2f6; 
        color: #000000; /* Force black text */
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #007bff;
        font-size: 16px;
        line-height: 1.5;
    }
    
    /* Filter Box Styling */
    .filter-box {
        border: 1px dashed #ccc;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        font-size: 14px;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    if api_key:
        if 'engine' not in st.session_state:
            st.session_state.engine = ScalerAIEngine(api_key)
    else:
        st.warning("Please enter API Key to start.")
        st.stop()

# STATE INIT
if 'step' not in st.session_state: st.session_state.step = 1

# HEADER
try:
    st.image("scaler.png", width=150)
except:
    st.markdown("## **Scaler Academy**")

# ==========================================
# STEP 1: REGISTRATION
# ==========================================
if st.session_state.step == 1:
    st.title("Masterclass Registration")
    st.markdown("Reserve your seat & get a **Personalized Skill Breakdown**.")
    
    with st.form("signup"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", "Divyansh Gangwar")
            phone = st.text_input("Phone Number", "+91 8534004168")
            grad_year = st.number_input("Graduation Year", 2010, 2030, 2027)
        with col2:
            email = st.text_input("Email", "divyanshgangwar3004@gmail.com")
            company = st.text_input("Company Name", "Infosys")
            role = st.text_input("Current Role", "QA Engineer")
        
        st.markdown("---")
        link = st.text_input("Masterclass URL", placeholder="Paste Scaler Event URL here...")
        
        btn = st.form_submit_button("Generate AI Assessment ➝")
        
        if btn:
            if not link:
                st.error("Please paste a Masterclass URL.")
            else:
                st.session_state.user = {
                    "name": name, "email": email, "phone": phone,
                    "grad_year": grad_year, "company": company, "role": role, "link": link
                }
                with st.spinner("🤖 Gemini is reading the syllabus..."):
                    scrape_result = st.session_state.engine.scrape_website(link)
                    if scrape_result['status'] == 'error':
                        st.error(f"Error: {scrape_result['msg']}")
                    else:
                        st.session_state.page_title = scrape_result['title']
                        with st.spinner("🧠 Generating diagnostic quiz..."):
                            quiz_data = st.session_state.engine.generate_quiz_with_gemini(scrape_result['text'])
                            if not quiz_data:
                                st.error("AI failed. Try again.")
                            else:
                                st.session_state.quiz = quiz_data
                                st.session_state.step = 2
                                st.rerun()

# ==========================================
# STEP 2: QUIZ
# ==========================================
elif st.session_state.step == 2:
    st.subheader(f"{st.session_state.page_title}")
    st.info(f"Hi {st.session_state.user['name'].split()[0]}, answer these {len(st.session_state.quiz)} questions to check your baseline.")
    
    with st.form("quiz_form"):
        answers = {}
        for i, q in enumerate(st.session_state.quiz):
            st.write(f"**{i+1}. {q['q']}**")
            answers[i] = st.radio(f"Select Answer {i}", q['options'], key=i, label_visibility="collapsed")
            st.markdown("---")
            
        submit = st.form_submit_button("Submit Answers")
        
        if submit:
            score = 0
            results_log = []
            for i, q in enumerate(st.session_state.quiz):
                is_correct = (answers[i] == q['correct'])
                if is_correct: score += 1
                results_log.append({"topic": q.get('topic', 'General'), "is_correct": is_correct})
            
            st.session_state.score = score
            st.session_state.results_log = results_log
            st.session_state.step = 3
            st.rerun()

# ==========================================
# STEP 3: RESULTS (Refined)
# ==========================================
elif st.session_state.step == 3:
    user = st.session_state.user
    
    # Generate Report ONCE
    if 'ai_report' not in st.session_state:
        with st.spinner("✍️ Analyzing results..."):
            st.session_state.ai_report = st.session_state.engine.generate_short_report(
                st.session_state.results_log, 
                st.session_state.score, 
                len(st.session_state.quiz), 
                user['name'].split()[0]
            )

    # 1. SCORE DISPLAY (Big & Visible)
    st.title("Readiness Report")
    col_score, col_text = st.columns([1, 2])
    with col_score:
        st.metric(label="Your Score", value=f"{st.session_state.score}/{len(st.session_state.quiz)}")
    
    # 2. SHORT REPORT (Black text on Grey)
    st.markdown(f"<div class='report-box'>{st.session_state.ai_report}</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    # 3. ALUMNI FILTERS (Clear Logic)
    smart_data = st.session_state.engine.generate_smart_link_data(user['company'], user['grad_year'])
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Your Career Path")
        st.write("See stories of alumni who made this exact transition:")
        
        # Explicit Filter Visual
        st.markdown(f"""
        <div class="filter-box">
        📍 <b>Current:</b> {smart_data['current']} <br>
        🎯 <b>Target:</b> {smart_data['target']} <br>
        ⏳ <b>Experience:</b> {smart_data['exp']}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.write("") # Spacer
        st.write("")
        st.link_button("Read Their Stories ➝", smart_data['url'])
        st.session_state.clicked = True

    st.markdown("---")
    
    # 4. SMALL CRM BUTTON
    col_x, col_y, col_z = st.columns([1, 2, 1])
    with col_y:
        if st.button("Simulate CRM Sync", type="secondary", use_container_width=True):
            st.session_state.step = 4
            st.rerun()

# ==========================================
# STEP 4: CRM DASHBOARD
# ==========================================
elif st.session_state.step == 4:
    st.subheader("🔒 LeadSquared Data Push")
    
    clicked = st.session_state.get('clicked', False)
    warmth_score = "🔥 HOT" if clicked else "❄️ COLD"

    payload = {
        "lead_name": st.session_state.user['name'],
        "company": st.session_state.user['company'],
        "score": f"{st.session_state.score}/{len(st.session_state.quiz)}",
        "lead_warmth": warmth_score,
        "ai_summary": st.session_state.ai_report[:100] + "..."
    }
    
    st.json(payload)
    
    if st.button("Reset"):
        st.session_state.clear()
        st.rerun()