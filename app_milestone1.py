import streamlit as st
import pandas as pd
import json
import os
import tempfile
from io import BytesIO
from datetime import datetime

# --- 1. IMPORT YOUR MODULAR FUNCTIONS ---
from src.section_normalizer import normalize_text as full_normalize
from src.remove_personal import remove_personal
from src.skill_extractor import extract_skills
from src.file_readers_txt import read_txt
from src.file_readers_docx import read_docx
from src.file_readers_pdf import read_pdf

# Sets Streamlit page metadata and layout.
st.set_page_config(
    page_title="AI Skill Gap Analyzer - Milestone 1",
    page_icon="🤖",
    layout="wide"
)

# --- HELPER FUNCTION FOR VISUALS for skills
def create_skill_tags(skills):
    """
    Generates a string of HTML for displaying skills as colorful tags.
    """
    if not skills:
        return "No skills extracted."
    
    tags_html = ""
    colors = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0", "#00BCD4"]  # palette
    
    for i, skill in enumerate(sorted(skills)):
        color = colors[i % len(colors)]
        tags_html += f"""<span style="background-color: {color}; color: white; padding: 4px 8px; margin: 2px; border-radius: 12px; font-size: 14px; display: inline-block; font-weight: 500; white-space: nowrap;">{skill}</span>"""
        
    return f"""<div style="display: flex; flex-wrap: wrap; gap: 5px;">{tags_html}</div>"""


# --- 2. CORE PIPELINE FUNCTION (Orchestrator) ---
def run_full_pipeline(raw_text, doc_name, doc_type, tmp_path=None):
    """
    Processes a single document (file or text input) through cleaning and skill extraction.
    """
    results = {
        'file_name': doc_name,
        'document_type': doc_type,
        'success': False,
        'error': 'Extraction failed',
        'extracted_skills': [],
    }
    
    try:
        if not raw_text or not str(raw_text).strip():
            raise ValueError("No text provided or extracted.")
            
        # --- Cleaning and Normalization ---
        cleaned_text = remove_personal(raw_text)
        if not cleaned_text:
            raise ValueError("remove_personal() returned None or empty text.")
        
        cleaned_text = full_normalize(cleaned_text)
        if not cleaned_text:
            raise ValueError("full_normalize() returned None or empty text.")
        
        # Debug print (console only)
        print("DEBUG normalized text preview:\n", cleaned_text[:300])
        
        # --- Rule-Based Skill Extraction ---
        skills_file_path = "skills_list.txt"
        if not os.path.exists(skills_file_path):
            raise FileNotFoundError(f"Missing skills file: {skills_file_path}")
        
        extracted_skills = extract_skills(cleaned_text, skills_file_path)
        
        # --- Stats ---
        original_length = len(raw_text)
        final_length = len(cleaned_text)
        reduction = ((original_length - final_length) / original_length * 100) if original_length > 0 else 0
        
        results.update({
            'success': True,
            'error': None,
            'original_text': raw_text,
            'cleaned_text': cleaned_text,
            'extracted_skills': extracted_skills,
            'original_length': original_length,
            'final_length': final_length,
            'reduction_percentage': reduction,
            'word_count': len(cleaned_text.split()),
        })

    except Exception as e:
        results['error'] = f"Processing Error: {str(e)}"
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
            
    return results


# --- Wrapper for file uploads ---
def process_document_from_file(file_content, file_name, file_format, doc_type):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_format}") as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name
        
        # A. Ingestion
        if file_format == 'txt':
            raw_text = read_txt(tmp_path)
        elif file_format == 'pdf':
            raw_text = read_pdf(tmp_path)
        elif file_format == 'docx':
            raw_text = read_docx(tmp_path)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

        return run_full_pipeline(raw_text, file_name, doc_type, tmp_path)

    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        
        return {
            'file_name': file_name,
            'document_type': doc_type,
            'success': False,
            'error': f"File Read/Ingestion Error: {str(e)}",
            'extracted_skills': [],
        }


# --- 3. STREAMLIT UI ---
def main():
    st.title("🤖 AI Skill Gap Analyzer: Milestone 1")
    st.markdown("### Data Ingestion, Cleaning, and Initial Extraction")

    upload_col, jd_col = st.columns([1, 1])
    
    with upload_col:
        st.subheader("1. Upload your Resume")
        uploaded_resume_files = st.file_uploader(
            "Select Resume(s) (PDF, DOCX, TXT)",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            key="resume_uploader"
        )

    jd_file = None
    jd_text = None
    with jd_col:
        st.subheader("2. Upload your job description")
        jd_input_mode = st.radio(
            "Choose JD Input:",
            ('Paste Text', 'Upload File'),
            index=0,
            horizontal=False,
            key="jd_mode_radio"
        )
        jd_name = st.text_input("Name this Job Description", "Job Description (Target)", key="jd_name_input")
        
        if jd_input_mode == 'Paste Text':
            jd_text = st.text_area("Paste Job Description Text Here", height=250, key="jd_text_area")
        else:
            jd_file = st.file_uploader(
                "Upload Single Job Description File (PDF, DOCX, TXT)",
                type=['pdf', 'docx', 'txt'],
                accept_multiple_files=False,
                key="jd_file_uploader"
            )
    
    st.markdown("---")
    
    all_documents_to_process = []
    
    if uploaded_resume_files or (jd_text and jd_text.strip()) or jd_file:
        
        if jd_file:
            file_content = jd_file.getvalue()
            file_name = jd_file.name
            file_format = file_name.split('.')[-1].lower()
            all_documents_to_process.append({
                'content': file_content,
                'name': jd_name,
                'format': file_format,
                'type': 'job_description'
            })
        elif jd_text and jd_text.strip():
            all_documents_to_process.append({
                'content': jd_text,
                'name': jd_name,
                'format': 'txt_text',
                'type': 'job_description'
            })

        for file in uploaded_resume_files:
            all_documents_to_process.append({
                'content': file.getvalue(),
                'name': file.name,
                'format': file.name.split('.')[-1].lower(),
                'type': 'resume'
            })
        
        if all_documents_to_process:
            num_resumes = len(uploaded_resume_files)
            has_jd = 1 if any(d['type'] == 'job_description' for d in all_documents_to_process) else 0
            st.info(f"Ready to process {num_resumes} resume(s) and {has_jd} Job Description.")
            
            if st.button("🚀 Process Documents", type="primary"):
                st.session_state.processed_docs = []
                progress_bar = st.progress(0)
                
                for i, doc in enumerate(all_documents_to_process):
                    progress = (i + 1) / len(all_documents_to_process)
                    progress_bar.progress(progress)
                    
                    if doc['format'] == 'txt_text':
                        result = run_full_pipeline(doc['content'], doc['name'], doc['type'])
                    else:
                        result = process_document_from_file(doc['content'], doc['name'], doc['format'], doc['type'])
                        
                    st.session_state.processed_docs.append(result)
                
                progress_bar.empty()
    
    if 'processed_docs' in st.session_state and st.session_state.processed_docs:
        
        successful_docs = [doc for doc in st.session_state.processed_docs if doc['success']]
        
        if successful_docs:
            st.markdown("## Analysis Results")
            
            for doc in successful_docs:
                doc_icon = "💼" if doc['document_type'] == 'job_description' else "📄"

                with st.expander(f"{doc_icon} {doc['file_name']} - SUCCESS", expanded=True):
                    
                    st.markdown("##### 🧹 Cleaning Summary")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Original Chars", f"{doc['original_length']:,}")
                    col2.metric("Final Chars", f"{doc['final_length']:,}")
                    col3.metric(
                        "Cleaning Reduction",
                        f"{doc['reduction_percentage']:.2f}%",
                        delta_color="normal" if doc['reduction_percentage'] > 0 else "off",
                        delta="Reduced" if doc['reduction_percentage'] > 0 else "No Change"
                    )

                    st.markdown("---")
                    
                    st.markdown("##### 💡 Extracted Skills (Rule-Based)")
                    st.metric("Total Unique Skills Found", len(doc['extracted_skills']))
                    st.markdown(create_skill_tags(doc['extracted_skills']), unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.markdown("##### 🔍 Text Transformation Proof: Original vs. Cleaned")
                    
                    text_col1, text_col2 = st.columns(2)
                    with text_col1:
                        st.markdown("**Original Text Snippet**")
                        st.code(doc['original_text'][:1000] + "\n\n...", language='text')
                    with text_col2:
                        st.markdown("**Cleaned Text**")
                        st.code(doc['cleaned_text'][:1000] + "\n\n...", language='text')

            extracted_data = [
                {'filename': d['file_name'], 'type': d['document_type'], 'skills': d['extracted_skills'], 'clean_snippet': d['cleaned_text'][:300] + "..."}
                for d in successful_docs
            ]
            
            if extracted_data:
                st.download_button(
                    label="📥 Download Extracted Data (JSON)",
                    data=json.dumps(extracted_data, indent=4),
                    file_name="milestone1_extracted_data.json",
                    mime="application/json"
                )
        
        failed_docs = [doc for doc in st.session_state.processed_docs if not doc['success']]
        if failed_docs:
            st.subheader("❌ Failed Documents")
            for doc in failed_docs:
                st.error(f"File: {doc['file_name']} | Type: {doc['document_type']} | Error: {doc['error']}")


if __name__ == "__main__":
    main()
