import os
import streamlit as st
import pandas as pd
from main import run_pipeline

st.set_page_config(page_title="WebIntel Analytics", page_icon="🌐", layout="wide")

# Custom CSS to match provided design
st.markdown(
    """
    <style>
    .stApp {background-color: #0f1a2b; color: #e2e8f0;}
    .hero {text-align: center; padding: 2rem 0 1rem 0;}
    .hero h1 {font-size: 2.2rem; margin: 0;}
    .hero p {color: #a0aec0; margin-top: .4rem;}
    .card {
        background: #152238; border: 1px solid #24364d; border-radius: 12px; padding: 18px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.25);
    }
    .success-panel {background: #173a2e; border: 1px solid #2f7a62; border-radius: 12px; padding: 16px;}
    .muted {color:#90a4b8;}
    .tile {background:#152238; border: 1px solid #24364d; border-radius: 12px; padding:16px; height:100%;}
    .tile h4 {margin:0 0 6px 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Hero
st.markdown("""
<div class="hero">
  <h1>🌐 WebIntel Analytics</h1>
  <p>Advanced AI-powered web intelligence platform for comprehensive content analysis and strategic question generation</p>
</div>
""", unsafe_allow_html=True)

# Centered configuration card
left, center, right = st.columns([1, 2.5, 1])
with center:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Intelligence Configuration")
    st.caption("Configure your web intelligence parameters and data extraction preferences")

    url = st.text_input("Website URL", placeholder="https://example.com/help")
    query = st.text_area(
        "Question Types",
        value=(
            "Extract Golden Questions and Expected Responses that users commonly ask about this "
            "product/service for comprehensive bot testing"
        ),
        height=70,
        help="The retrieval/generation focus for extracting golden questions",
    )

    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        analysis_toggle = st.toggle("Analysis Questions", value=True)
        critical_toggle = st.toggle("Critical Thinking", value=False)
    with col_f2:
        st.selectbox("Output Format", options=["Excel (.xlsx)"], index=0, help="Only Excel is supported")
        output_name = st.text_input("Output filename", value="output/golden_qna.xlsx")

    # Advanced options as expandable section
    with st.expander("Advanced Options"):
        st.markdown("<span class='muted'>Scraping</span>", unsafe_allow_html=True)
        sc1, sc2, sc3 = st.columns([1,1,1])
        with sc1:
            scroll_pages = st.number_input("Scroll pages", min_value=1, max_value=20, value=5)
        with sc2:
            crawl = st.toggle("Crawl hyperlinks", value=False)
        with sc3:
            allow_external = st.toggle("Allow external domains", value=False)
        sc4, sc5 = st.columns(2)
        with sc4:
            max_depth = st.number_input("Max depth", min_value=1, max_value=5, value=1)
        with sc5:
            max_pages = st.number_input("Max pages", min_value=1, max_value=200, value=20)

        st.markdown("<span class='muted'>Retrieval & Validation</span>", unsafe_allow_html=True)
        rv1, rv2, rv3 = st.columns(3)
        with rv1:
            k = st.number_input("Top-k chunks", min_value=5, max_value=200, value=30)
        with rv2:
            validate = st.toggle("Content quality validation", value=False)
        with rv3:
            debug = st.toggle("Debug mode", value=False)

        st.markdown("<span class='muted'>Test Cases</span>", unsafe_allow_html=True)
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            with_tc = st.toggle("Generate TestCases", value=True)
        with tc2:
            tc_variations = st.number_input("# Variations per question", min_value=1, max_value=100, value=20)
        with tc3:
            tc_negatives = st.number_input("# Negative cases per question", min_value=1, max_value=100, value=12)
        tc_llm = False  # keep rule-based UI for now

    colb1, colb2, colb3 = st.columns([1,1,1])
    with colb2:
        run = st.button("Start Intelligence Analysis", use_container_width=True, type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

# Results / success panel
if 'last_output' not in st.session_state:
    st.session_state['last_output'] = ''

if run:
    if not url:
        st.error("Please enter a Website URL")
    else:
        with st.status("Running pipeline...", expanded=True) as s:
            s.write("Scraping and analyzing content...")
            try:
                out_path = run_pipeline(
                    url=url,
                    query=query,
                    output=output_name,
                    k=int(k),
                    scroll_pages=int(scroll_pages),
                    output_format="excel",
                    validate_content=bool(validate or debug),
                    crawl=bool(crawl),
                    max_depth=int(max_depth),
                    max_pages=int(max_pages),
                    same_domain_only=not bool(allow_external),
                    with_test_cases=bool(with_tc),
                    test_cases_llm=bool(tc_llm),
                    tc_variations=int(tc_variations),
                    tc_negatives=int(tc_negatives),
                )
                st.session_state['last_output'] = out_path
                s.write(f"Saved output to: {out_path}")
                s.update(state="complete")
                st.markdown("<div class='success-panel'>**Intelligence Report Ready**<br/>Comprehensive strategic insights generated from web analysis.</div>", unsafe_allow_html=True)
                if os.path.isfile(out_path):
                    st.download_button(
                        label="Download Excel",
                        data=open(out_path, "rb").read(),
                        file_name=os.path.basename(out_path),
                        use_container_width=True,
                    )
            except Exception as e:
                s.update(state="error")
                st.error(f"Pipeline failed: {e}")
                st.stop()

st.markdown("\n")

# Feature tiles row
tile1, tile2, tile3 = st.columns(3)
with tile1:
    st.markdown("<div class='tile'>", unsafe_allow_html=True)
    st.markdown("#### 🧠 Intelligent Content Mining")
    st.markdown("Advanced AI algorithms analyze web content to extract strategic insights and generate actionable intelligence")
    st.markdown("</div>", unsafe_allow_html=True)
with tile2:
    st.markdown("<div class='tile'>", unsafe_allow_html=True)
    st.markdown("#### ⚙️ Enterprise Configuration")
    st.markdown("Flexible configuration options for analysis depth, intelligence types, and export formats tailored to enterprise needs")
    st.markdown("</div>", unsafe_allow_html=True)
with tile3:
    st.markdown("<div class='tile'>", unsafe_allow_html=True)
    st.markdown("#### ⬇️ Multi-Format Intelligence Reports")
    st.markdown("Export intelligence reports in Excel for seamless integration with enterprise systems")
    st.markdown("</div>", unsafe_allow_html=True)
