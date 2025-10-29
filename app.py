import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import tempfile
from io import BytesIO
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import base64
import logging
import re
import requests
from sklearn.metrics.pairwise import cosine_similarity
from wordcloud import WordCloud
import PyPDF2
import docx
from PIL import Image
import pdf2image
import pytesseract
import io

# Import Milestone 1 modules
try:
    from src.text_cleaner.section_normalizer import normalize_text as full_normalize
    from src.text_cleaner.remove_personal import remove_personal
    from src.skill_extractor import extract_skills
    from src.file_readers.file_readers_txt import read_txt
    from src.file_readers.file_readers_docx import read_docx
    from src.file_readers.file_readers_pdf import read_pdf
except ImportError:
    st.warning("⚠️ Milestone 1 modules not found. Using fallback implementations.")

# Import Milestone 2 modules
try:
    from askill_ext import AdvancedSkillExtractor, EnhancedSkillGapAnalyzer
except ImportError:
    st.warning("⚠️ Milestone 2 modules not found. Using integrated implementation.")

# Import Milestone 3 modules - MODIFIED TO MATCH FIRST CODE
try:
    from gap_analysys import (
        SentenceBERTEncoder, 
        SimilarityCalculator, 
        SkillGapAnalyzer,
        GapVisualizer,
        LearningPathGenerator,
        SkillMatch,
        GapAnalysisResult
    )
    MILESTONE3_AVAILABLE = True
except ImportError:
    st.warning("⚠️ Milestone 3 modules not found. Using fallback implementation.")
    MILESTONE3_AVAILABLE = False

# Page Configuration
st.set_page_config(
    page_title="AI Skill Gap Analyzer Pro",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Beautiful CSS Styling (keeping the same CSS as second code)
def load_custom_css():
    st.markdown("""
 <style>
    /* Global Styles */
    .main {
        padding-top: 2rem;
    }
    
    /* Hero Section */
    .hero-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        position: relative;
        overflow: hidden;
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
        animation: fadeInUp 1s ease-out;
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        opacity: 0.95;
        animation: fadeInUp 1s ease-out 0.2s;
        animation-fill-mode: both;
    }
    
    /* Progress Steps */
    .progress-container {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        position: relative;
    }
    
    .progress-step {
        flex: 1;
        text-align: center;
        position: relative;
        z-index: 2;
        cursor: pointer;
    }
    
    .progress-circle {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: #e0e0e0;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 0.5rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .progress-step.active .progress-circle {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transform: scale(1.1);
    }
    
    .progress-step.completed .progress-circle {
        background: #28a745;
        color: white;
    }
    
    .progress-step.clickable .progress-circle:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    .progress-line {
        position: absolute;
        top: 25px;
        left: 0;
        right: 0;
        height: 2px;
        background: #e0e0e0;
        z-index: 1;
    }
    
    .progress-line-active {
        background: linear-gradient(90deg, #28a745 0%, #e0e0e0 100%);
    }
    
    /* Card Styles */
    .card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }
    
    .card-header {
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #333;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Skill Tags */
    .skill-tag {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        margin: 0.3rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .skill-tag:hover {
        transform: scale(1.05);
    }
    
    .skill-matched {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
    }
    
    .skill-partial {
        background: linear-gradient(135deg, #ffc107, #fd7e14);
        color: white;
    }
    
    .skill-missing {
        background: linear-gradient(135deg, #dc3545, #e83e8c);
        color: white;
    }
    
    .skill-highlight {
        background-color: yellow;
        padding: 2px 4px;
        border-radius: 3px;
    }
    
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-label {
        color: #6c757d;
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    
    /* Upload Area */
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background: #f8f9ff;
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        border-color: #764ba2;
        background: #f0f2ff;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    /* File Status */
    .file-status {
        display: flex;
        align-items: center;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        background: #f8f9fa;
        
    }
    
    .file-status.success {
        background: black;
        border-left: 4px solid #28a745;
    }
    
    .file-status.error {
        background: #f8d7da;
        border-left: 4px solid #dc3545;
    }
    
    .file-status-icon {
        margin-right: 0.5rem;
        font-size: 1.2rem;
    }
    
    /* Normalization Summary */
    .norm-summary {
        background: #black;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #2196f3;
    }
    
    /* Evidence Modal */
    .evidence-modal {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        z-index: 1000;
        max-width: 600px;
        max-height: 80vh;
        overflow-y: auto;
    }
    
    /* Animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Heatmap Cell */
    .heatmap-cell {
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .heatmap-cell:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }

    /* High Priority Gap */
    .priority-gap {
        background: #1a1a1a;
        border-left: 4px solid #0d6efd;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        color: #ffffff;
    }

    /* Specific Priority Levels */
    .priority-gap.high {
        border-left-color: #dc3545;
    }

    .priority-gap.medium {
        border-left-color: #ffc107;
    }

    .priority-gap.low {
        border-left-color: #17a2b8;
    }

    /* ===== NEW PROFESSIONAL GRADIENT STYLES ===== */
    
    /* Professional Gradient Backgrounds */
    .gradient-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        padding: 2rem;
    }

    .gradient-success {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        border-radius: 15px;
        padding: 2rem;
    }

    .gradient-warning {
        background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
        color: white;
        border-radius: 15px;
        padding: 2rem;
    }

    .gradient-danger {
        background: linear-gradient(135deg, #dc3545 0%, #e83e8c 100%);
        color: white;
        border-radius: 15px;
        padding: 2rem;
    }

    .gradient-dark {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        color: white;
        border-radius: 15px;
        padding: 2rem;
    }

    .gradient-ocean {
        background: linear-gradient(135deg, #2196f3 0%, #21cbf3 100%);
        color: white;
        border-radius: 15px;
        padding: 2rem;
    }

    .gradient-sunset {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%);
        color: white;
        border-radius: 15px;
        padding: 2rem;
    }

    .gradient-forest {
        background: linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%);
        color: white;
        border-radius: 15px;
        padding: 2rem;
    }

    .gradient-premium {
        background: linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%);
        color: white;
        border-radius: 15px;
        padding: 2rem;
    }

    /* Enhanced Metric Cards with Glass Effect */
    .glass-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        color: white;
        text-align: center;
    }

    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        background: rgba(255, 255, 255, 0.15);
    }

    .glass-card .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ffffff, #f0f0f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .glass-card .metric-label {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1rem;
        margin-top: 0.5rem;
    }

    /* Animated Gradient Border */
    .animated-border {
        position: relative;
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    .animated-border::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000);
        background-size: 400%;
        border-radius: 17px;
        z-index: -1;
        animation: glowing 20s linear infinite;
        opacity: 0.7;
        filter: blur(5px);
    }

    @keyframes glowing {
        0% { background-position: 0 0; }
        50% { background-position: 400% 0; }
        100% { background-position: 0 0; }
    }

    /* Professional Button Gradients */
    .btn-gradient-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        cursor: pointer;
        display: inline-block;
        text-align: center;
        text-decoration: none;
    }

    .btn-gradient-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        color: white;
    }

    .btn-gradient-success {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
        cursor: pointer;
        display: inline-block;
        text-align: center;
        text-decoration: none;
    }

    .btn-gradient-success:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
        color: white;
    }

    .btn-gradient-warning {
        background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 193, 7, 0.3);
        cursor: pointer;
        display: inline-block;
        text-align: center;
        text-decoration: none;
    }

    .btn-gradient-warning:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 193, 7, 0.4);
        color: white;
    }

    /* Enhanced Skill Tags with Gradients */
    .skill-tag-premium {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
        display: inline-block;
        margin: 0.2rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }

    .skill-tag-premium:hover {
        transform: scale(1.05) translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    .skill-tag-gold {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #333;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
        display: inline-block;
        margin: 0.2rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3);
    }

    .skill-tag-gold:hover {
        transform: scale(1.05) translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 215, 0, 0.4);
    }

    /* Progress Bar Gradients */
    .progress-gradient {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #667eea 100%);
        background-size: 200% 100%;
        animation: shimmer 2s infinite linear;
        border-radius: 10px;
        height: 8px;
        margin: 1rem 0;
    }

    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }

    /* Floating Animation */
    .float-animation {
        animation: float 3s ease-in-out infinite;
    }

    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }

    /* Pulse Animation for Important Elements */
    .pulse-important {
        animation: pulse 2s infinite;
        border-radius: 15px;
        padding: 1rem;
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(102, 126, 234, 0); }
        100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0); }
    }

    /* Enhanced Card with Gradient Border */
    .card-gradient-border {
        position: relative;
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }

    .card-gradient-border::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 17px;
        z-index: -1;
        opacity: 0.8;
    }

    /* Stats Highlight */
    .stats-highlight {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }

    /* ATS Score Styles */
    .ats-score-container {
        text-align: center;
        padding: 2rem;
    }

    .ats-score-circle {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: bold;
        margin: 0 auto 1rem;
        color: white;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }

    .ats-score-excellent {
        background: linear-gradient(135deg, #28a745, #20c997);
    }

    .ats-score-good {
        background: linear-gradient(135deg, #17a2b8, #6f42c1);
    }

    .ats-score-average {
        background: linear-gradient(135deg, #ffc107, #fd7e14);
    }

    .ats-score-poor {
        background: linear-gradient(135deg, #dc3545, #e83e8c);
    }

    .ats-factor {
        margin: 1rem 0;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 10px;
    }

    .ats-factor-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }

    .ats-factor-title {
        font-weight: 600;
        color: #333;
    }

    .ats-factor-score {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: bold;
        color: white;
    }

    .ats-factor-excellent {
        background: linear-gradient(135deg, #28a745, #20c997);
    }

    .ats-factor-good {
        background: linear-gradient(135deg, #17a2b8, #6f42c1);
    }

    .ats-factor-average {
        background: linear-gradient(135deg, #ffc107, #fd7e14);
    }

    .ats-factor-poor {
        background: linear-gradient(135deg, #dc3545, #e83e8c);
    }

    /* Learning Path Styles */
    .learning-path-item {
        border-left: 4px solid;
        padding-left: 1rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }

    .learning-path-item:hover {
        transform: translateX(5px);
    }

    .learning-path-high {
        border-left-color: #dc3545;
        background: linear-gradient(135deg, rgba(220, 53, 69, 0.05), rgba(232, 62, 140, 0.05));
    }

    .learning-path-medium {
        border-left-color: #ffc107;
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.05), rgba(253, 126, 20, 0.05));
    }

    .learning-path-low {
        border-left-color: #17a2b8;
        background: linear-gradient(135deg, rgba(23, 162, 184, 0.05), rgba(111, 66, 193, 0.05));
    }

    /* Badge Styles */
    .badge-gradient {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin: 0 0.25rem;
    }

    .badge-success {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
    }

    .badge-warning {
        background: linear-gradient(135deg, #ffc107, #fd7e14);
        color: white;
    }

    .badge-danger {
        background: linear-gradient(135deg, #dc3545, #e83e8c);
        color: white;
    }

    /* Section Dividers */
    .section-divider {
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
        border: none;
        margin: 2rem 0;
        border-radius: 2px;
    }

    /* Text Gradients */
    .text-gradient-primary {
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }

    .text-gradient-success {
        background: linear-gradient(135deg, #28a745, #20c997);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2rem;
        }
        
        .progress-step {
            font-size: 0.8rem;
        }
        
        .progress-circle {
            width: 40px;
            height: 40px;
        }
        
        .metric-value {
            font-size: 2rem;
        }
    }
</style>
    """, unsafe_allow_html=True)

load_custom_css()

# Initialize Session State
def init_session_state():
    defaults = {
        'current_step': 1,
        'resume_file': None,
        'jd_file': None,
        'resume_text': '',
        'jd_text': '',
        'cleaned_resume': '',
        'cleaned_jd': '',
        'resume_skills': [],
        'jd_skills': [],
        'analysis_result': None,
        'learning_path': [],
        'processing_complete': False,
        'milestone1_complete': False,
        'milestone2_complete': False,
        'milestone3_complete': False,
        'max_step_reached': 1,
        'ats_score': None,
        'ats_analysis': None,
        'file_status': [],
        'normalization_summary': {},
        'selected_model': 'spaCy base model',
        'confidence_threshold': 0.6,
        'similarity_threshold': 0.6,
        'embedding_model': 'all-MiniLM-L6-v2',
        'highlighted_skill': None,
        'show_raw_text': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Enhanced File Reader with OCR
class EnhancedFileReader:
    @staticmethod
    def read_txt(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def read_pdf(file_path):
        try:
            # Try PyPDF2 first
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                
                # Check if text is meaningful (not just scanned)
                if len(text.strip()) > 100:
                    return text, "text", 1.0
                else:
                    # Use OCR for scanned PDFs
                    return EnhancedFileReader._ocr_pdf(file_path)
        except:
            return EnhancedFileReader._ocr_pdf(file_path)
    
    @staticmethod
    def _ocr_pdf(file_path):
        try:
            images = pdf2image.convert_from_path(file_path)
            text = ""
            confidences = []
            
            for image in images:
                ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                page_text = " ".join([word for i, word in enumerate(ocr_data['text']) if int(ocr_data['conf'][i]) > 0])
                text += page_text + "\n"
                
                # Calculate average confidence
                confidences.extend([int(conf) for conf in ocr_data['conf'] if int(conf) > 0])
            
            avg_confidence = np.mean(confidences) / 100 if confidences else 0.5
            return text, "ocr", avg_confidence
        except Exception as e:
            return "", "error", 0.0
    
    @staticmethod
    def read_docx(file_path):
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    
    @staticmethod
    def count_pages(file_path):
        if file_path.endswith('.pdf'):
            try:
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    return len(reader.pages)
            except:
                return 1
        return 1

# Enhanced Skill Extractor with Categorization
class EnhancedSkillExtractor:
    def __init__(self):
        # Skill categories with examples
        self.skill_categories = {
            'technical': [
                'Python', 'Java', 'JavaScript', 'SQL', 'Machine Learning', 'Deep Learning',
                'TensorFlow', 'PyTorch', 'React', 'Node.js', 'Docker', 'Kubernetes',
                'AWS', 'Azure', 'GCP', 'Git', 'CI/CD', 'Microservices', 'REST API',
                'MongoDB', 'PostgreSQL', 'Redis', 'Elasticsearch', 'Kafka', 'Spark'
            ],
            'soft': [
                'Communication', 'Leadership', 'Teamwork', 'Problem Solving', 'Critical Thinking',
                'Creativity', 'Adaptability', 'Time Management', 'Project Management',
                'Collaboration', 'Analytical Skills', 'Decision Making', 'Negotiation'
            ],
            'tools': [
                'Jira', 'Confluence', 'Slack', 'Trello', 'Asana', 'Figma', 'Sketch',
                'VS Code', 'IntelliJ', 'Eclipse', 'Postman', 'Docker Desktop',
                'Kubernetes Dashboard', 'Grafana', 'Prometheus', 'Jenkins'
            ],
            'certifications': [
                'AWS Certified', 'Azure Certified', 'Google Cloud Certified',
                'PMP', 'Scrum Master', 'CISSP', 'CompTIA', 'Cisco Certified',
                'Oracle Certified', 'Microsoft Certified', 'Salesforce Certified'
            ]
        }
        
        # Build skill lookup dictionary
        self.skill_lookup = {}
        for category, skills in self.skill_categories.items():
            for skill in skills:
                self.skill_lookup[skill.lower()] = category
    
    def extract_skills(self, text, model_type='spaCy', confidence_threshold=0.6):
        """Extract skills with categorization and confidence scores"""
        text_lower = text.lower()
        extracted_skills = []
        
        # Extract skills based on model type
        if model_type == 'spaCy':
            # Simulate spaCy extraction with confidence
            for skill, category in self.skill_lookup.items():
                if skill in text_lower:
                    # Calculate confidence based on context
                    confidence = self._calculate_confidence(skill, text_lower)
                    if confidence >= confidence_threshold:
                        extracted_skills.append({
                            'name': skill.title(),
                            'category': category,
                            'confidence': confidence,
                            'occurrences': text_lower.count(skill),
                            'sentences': self._find_sentences(skill, text)
                        })
        elif model_type == 'custom_ner':
            # Simulate custom NER extraction
            for skill, category in self.skill_lookup.items():
                if skill in text_lower:
                    confidence = min(0.9, self._calculate_confidence(skill, text_lower) + 0.1)
                    if confidence >= confidence_threshold:
                        extracted_skills.append({
                            'name': skill.title(),
                            'category': category,
                            'confidence': confidence,
                            'occurrences': text_lower.count(skill),
                            'sentences': self._find_sentences(skill, text)
                        })
        else:  # keyword list
            for skill, category in self.skill_lookup.items():
                if skill in text_lower:
                    confidence = 0.7  # Default confidence for keyword matching
                    if confidence >= confidence_threshold:
                        extracted_skills.append({
                            'name': skill.title(),
                            'category': category,
                            'confidence': confidence,
                            'occurrences': text_lower.count(skill),
                            'sentences': self._find_sentences(skill, text)
                        })
        
        return extracted_skills
    
    def _calculate_confidence(self, skill, text):
        """Calculate confidence score based on context"""
        # Simple heuristic: more occurrences = higher confidence
        occurrences = text.count(skill)
        base_confidence = min(0.9, 0.5 + (occurrences * 0.1))
        
        # Boost confidence if skill appears in specific sections
        if any(section in text for section in ['skills', 'experience', 'projects']):
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _find_sentences(self, skill, text):
        """Find sentences containing the skill"""
        sentences = text.split('.')
        skill_sentences = []
        
        for sentence in sentences:
            if skill.lower() in sentence.lower():
                skill_sentences.append(sentence.strip())
        
        return skill_sentences[:3]  # Return up to 3 sentences

# Fallback Visualization Class - MODIFIED TO USE MILESTONE 3
class FallbackVisualizer:
    """Fallback visualization class if Milestone 3 not available"""
    
    @staticmethod
    def create_similarity_heatmap(similarity_matrix, resume_skills, jd_skills):
        """Create similarity heatmap"""
        # Limit display to avoid overcrowding
        max_display = 20
        display_resume = resume_skills[:max_display]
        display_jd = jd_skills[:max_display]
        display_matrix = similarity_matrix[:max_display, :max_display]
        
        fig = go.Figure(data=go.Heatmap(
            z=display_matrix,
            x=display_jd,
            y=display_resume,
            colorscale='RdYlGn',
            zmid=0.5,
            text=np.round(display_matrix, 2),
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(
                title="Similarity",
                tickmode="linear",
                tick0=0,
                dtick=0.2
            )
        ))
        
        fig.update_layout(
            title=f"Skill Similarity Heatmap (Top {min(max_display, len(resume_skills))} x {min(max_display, len(jd_skills))} skills)",
            xaxis_title="Job Description Skills",
            yaxis_title="Resume Skills",
            height=600,
            width=900,
            xaxis={'side': 'bottom'},
            yaxis={'autorange': 'reversed'}
        )
        
        return fig
    
    @staticmethod
    def create_match_distribution_pie(matched, partial, missing):
        """Create pie chart for match distribution"""
        labels = ['Strong Matches', 'Partial Matches', 'Missing Skills']
        values = [matched, partial, missing]
        colors = ['#28a745', '#ffc107', '#dc3545']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            hole=0.3,
            textposition='auto',
            textinfo='label+percent+value'
        )])
        
        fig.update_layout(
            title="Skill Match Distribution",
            height=500,
            showlegend=True
        )
        
        return fig
    
    @staticmethod
    def create_skill_comparison_bar(all_matches, top_n=15):
        """Create bar chart comparing skill similarities"""
        # Sort by similarity
        all_matches_sorted = sorted(all_matches, key=lambda x: x[1], reverse=True)[:top_n]
        
        skills = [m[0] for m in all_matches_sorted]
        similarities = [m[1] * 100 for m in all_matches_sorted]
        
        fig = go.Figure(data=[go.Bar(
            y=skills,
            x=similarities,
            orientation='h',
            marker=dict(color='lightblue'),
            text=[f"{s:.1f}%" for s in similarities],
            textposition='auto'
        )])
        
        fig.update_layout(
            title=f"Top {top_n} Skills by Similarity Score",
            xaxis_title="Similarity Score (%)",
            yaxis_title="Skills",
            height=600,
            yaxis=dict(autorange="reversed"),
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_overall_score_gauge(overall_score):
        """Create gauge chart for overall match score"""
        score_percentage = overall_score * 100
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score_percentage,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Overall Match Score", 'font': {'size': 24}},
            delta={'reference': 70, 'increasing': {'color': "green"}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "darkblue"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 40], 'color': '#ffcccc'},
                    {'range': [40, 70], 'color': '#ffffcc'},
                    {'range': [70, 100], 'color': '#ccffcc'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))
        
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        
        return fig

# Enhanced Visualizer - MODIFIED TO USE MILESTONE 3
class EnhancedVisualizer:
    def __init__(self):
        # Use Milestone 3 visualizer if available, otherwise fallback
        if MILESTONE3_AVAILABLE:
            try:
                self.visualizer = GapVisualizer()
            except:
                self.visualizer = FallbackVisualizer()
        else:
            self.visualizer = FallbackVisualizer()
    
    @staticmethod
    def create_tag_cloud(skills):
        """Create tag cloud visualization"""
        if not skills:
            return None
        
        # Count skill frequencies
        skill_freq = {}
        for skill in skills:
            if isinstance(skill, dict):
                name = skill['name']
                freq = skill.get('occurrences', 1)
            else:
                name = skill
                freq = 1
            skill_freq[name] = skill_freq.get(name, 0) + freq
        
        if not skill_freq:
            return None
        
        # Generate word cloud
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            colormap='viridis',
            max_words=50
        ).generate_from_frequencies(skill_freq)
        
        # Convert to image
        img = io.BytesIO()
        wordcloud.to_image().save(img, format='PNG')
        img.seek(0)
        
        return img
    
    @staticmethod
    def create_radar_chart(resume_skills, jd_skills):
        """Create radar chart comparing skill categories"""
        categories = ['Technical', 'Soft', 'Tools', 'Certifications']
        
        # Count skills by category
        def count_by_category(skills):
            counts = {'Technical': 0, 'Soft': 0, 'Tools': 0, 'Certifications': 0}
            for skill in skills:
                if isinstance(skill, dict):
                    category = skill.get('category', 'technical')
                else:
                    category = 'technical'  # Default
                
                # Map to radar categories
                if category == 'technical':
                    counts['Technical'] += 1
                elif category == 'soft':
                    counts['Soft'] += 1
                elif category == 'tools':
                    counts['Tools'] += 1
                elif category == 'certifications':
                    counts['Certifications'] += 1
            
            return list(counts.values())
        
        resume_counts = count_by_category(resume_skills)
        jd_counts = count_by_category(jd_skills)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=resume_counts,
            theta=categories,
            fill='toself',
            name='Resume',
            line_color='blue',
            fillcolor='rgba(0, 123, 255, 0.25)'
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=jd_counts,
            theta=categories,
            fill='toself',
            name='Job Description',
            line_color='red',
            fillcolor='rgba(255, 0, 0, 0.25)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(max(resume_counts), max(jd_counts)) + 1]
                )
            ),
            title="Skill Category Comparison",
            height=500
        )
        
        return fig
    
    def create_similarity_heatmap(self, similarity_matrix, resume_skills, jd_skills):
        """Create interactive similarity heatmap using Milestone 3"""
        # Convert skill names if they're dictionaries
        resume_names = [s['name'] if isinstance(s, dict) else s for s in resume_skills]
        jd_names = [s['name'] if isinstance(s, dict) else s for s in jd_skills]
        
        # Use Milestone 3 visualizer if available
        if hasattr(self.visualizer, 'create_similarity_heatmap'):
            return self.visualizer.create_similarity_heatmap(similarity_matrix, resume_names, jd_names)
        else:
            return FallbackVisualizer.create_similarity_heatmap(similarity_matrix, resume_names, jd_names)
    
    def create_match_distribution_pie(self, matched, partial, missing):
        """Create pie chart for match distribution using Milestone 3"""
        if hasattr(self.visualizer, 'create_match_distribution_pie'):
            return self.visualizer.create_match_distribution_pie(matched, partial, missing)
        else:
            return FallbackVisualizer.create_match_distribution_pie(matched, partial, missing)
    
    def create_skill_comparison_bar(self, all_matches, top_n=15):
        """Create bar chart comparing skill similarities using Milestone 3"""
        if hasattr(self.visualizer, 'create_skill_comparison_bar'):
            return self.visualizer.create_skill_comparison_bar(all_matches, top_n)
        else:
            return FallbackVisualizer.create_skill_comparison_bar(all_matches, top_n)
    
    def create_overall_score_gauge(self, overall_score):
        """Create gauge chart for overall match score using Milestone 3"""
        if hasattr(self.visualizer, 'create_overall_score_gauge'):
            return self.visualizer.create_overall_score_gauge(overall_score)
        else:
            return FallbackVisualizer.create_overall_score_gauge(overall_score)
    
    @staticmethod
    def create_skill_distribution(skills):
        """Create skill distribution by category"""
        categories = ['Technical', 'Soft', 'Tools', 'Certifications']
        counts = {'Technical': 0, 'Soft': 0, 'Tools': 0, 'Certifications': 0}
        
        for skill in skills:
            if isinstance(skill, dict):
                category = skill.get('category', 'technical')
            else:
                category = 'technical'
            
            if category == 'technical':
                counts['Technical'] += 1
            elif category == 'soft':
                counts['Soft'] += 1
            elif category == 'tools':
                counts['Tools'] += 1
            elif category == 'certifications':
                counts['Certifications'] += 1
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(counts.keys()),
                y=list(counts.values()),
                marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
            )
        ])
        
        fig.update_layout(
                title="Skill Distribution by Category",
    xaxis_title="Category",
    yaxis_title="Count",
    height=400,
    paper_bgcolor="#121212",       # dark background
    plot_bgcolor="#1a1a1a",        # dark plot area
    font=dict(color="#FFFFFF"),    # white text for readability
    xaxis=dict(
        title_font=dict(color="#FFFFFF"),
        tickfont=dict(color="#CCCCCC"),
        gridcolor="#333333",
        linecolor="#666666"
    ),
    yaxis=dict(
        title_font=dict(color="#FFFFFF"),
        tickfont=dict(color="#CCCCCC"),
        gridcolor="#333333",
        linecolor="#666666"
    )

        )
        
        return fig

# Enhanced Export Functionality
class ReportGenerator:
    @staticmethod
    def generate_pdf_report(resume_skills, jd_skills, analysis_result, ats_score):
        """Generate PDF report"""
        # Helper function to extract skill name from SkillMatch object or string
        def get_skill_name(skill):
            if hasattr(skill, 'jd_skill'):  # SkillMatch object
                return skill.jd_skill
            return skill  # String

        # Create report content
        report_content = f"""
        <html>
        <head>
            <title>Skill Gap Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #667eea; }}
                h2 {{ color: #333; border-bottom: 2px solid #667eea; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .skill-matched {{ color: #28a745; font-weight: bold; }}
                .skill-partial {{ color: #ffc107; font-weight: bold; }}
                .skill-missing {{ color: #dc3545; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Skill Gap Analysis Report</h1>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

            <h2>Overall Match Score</h2>
            <div class="metric">
                <h3>{analysis_result.get('overall_score', 0):.1f}%</h3>
                <p>Match Percentage</p>
            </div>
            <div class="metric">
                <h3>{ats_score:.1f}%</h3>
                <p>ATS Score</p>
            </div>

            <h2>Skills Summary</h2>
            <table>
                <tr>
                    <th>Category</th>
                    <th>Resume Skills</th>
                    <th>JD Skills</th>
                    <th>Matched</th>
                </tr>
                <tr>
                    <td>Technical</td>
                    <td>{len([s for s in resume_skills if s.get('category') == 'technical'])}</td>
                    <td>{len([s for s in jd_skills if s.get('category') == 'technical'])}</td>
                    <td>{len([s for s in analysis_result.get('matched_skills', [])])}</td>
                </tr>
            </table>

            <h2>Matched Skills</h2>
            <ul>
                {''.join([f'<li class="skill-matched">{get_skill_name(skill)}</li>' for skill in analysis_result.get('matched_skills', [])[:10]])}
            </ul>

            <h2>Partial Matches</h2>
            <ul>
                {''.join([f'<li class="skill-partial">{get_skill_name(skill)} ({getattr(skill, "similarity", 0):.1%} similarity)</li>' for skill in analysis_result.get('partial_matches', [])[:10]])}
            </ul>

            <h2>Top Missing Skills</h2>
            <ul>
                {''.join([f'<li class="skill-missing">{get_skill_name(skill)} ({getattr(skill, "similarity", 0):.1%} similarity)</li>' for skill in analysis_result.get('missing_skills', [])[:10]])}
            </ul>

            <h2>High Priority Skill Gaps</h2>
            <table>
                <tr>
                    <th>Skill</th>
                    <th>Priority</th>
                    <th>Importance</th>
                    <th>Similarity</th>
                    <th>Recommended Action</th>
                </tr>
                {''.join([f'''
                <tr>
                    <td>{gap['skill']}</td>
                    <td>{gap['priority'].title()}</td>
                    <td>{gap['importance']:.1%}</td>
                    <td>{gap.get('similarity', 0):.1%}</td>
                    <td>{gap['suggested_action']}</td>
                </tr>
                ''' for gap in analysis_result.get('priority_gaps', [])[:5]])}
            </table>

            <h2>Learning Path Recommendations</h2>
            <table>
                <tr>
                    <th>Skill</th>
                    <th>Priority</th>
                    <th>Estimated Time</th>
                    <th>Resources</th>
                </tr>
                {''.join([f'''
                <tr>
                    <td>{item['skill']}</td>
                    <td>{item['priority'].title()}</td>
                    <td>{item['estimated_time']}</td>
                    <td>{', '.join(item['resources'][:2])}</td>
                </tr>
                ''' for item in st.session_state.get('learning_path', [])[:5]])}
            </table>
        </body>
        </html>
        """

        return report_content

    @staticmethod
    def generate_csv_report(resume_skills, jd_skills, analysis_result):
        """Generate CSV report"""
        data = []

        # Add header
        data.append(['Skill', 'Category', 'In Resume', 'In JD', 'Match Status', 'Similarity', 'Priority'])

        # Helper function to extract skill name from SkillMatch object or string
        def get_skill_name(skill):
            if hasattr(skill, 'jd_skill'):  # SkillMatch object
                return skill.jd_skill
            return skill  # String

        # Helper function to extract similarity from SkillMatch object
        def get_similarity(skill):
            if hasattr(skill, 'similarity'):  # SkillMatch object
                return skill.similarity
            return 1.0 if skill in analysis_result.get('matched_skills', []) else 0.0

        # Process all skills
        all_skills = set()
        all_skills.update([s['name'] if isinstance(s, dict) else s for s in resume_skills])
        all_skills.update([s['name'] if isinstance(s, dict) else s for s in jd_skills])

        for skill in all_skills:
            in_resume = skill in [s['name'] if isinstance(s, dict) else s for s in resume_skills]
            in_jd = skill in [s['name'] if isinstance(s, dict) else s for s in jd_skills]

            # Check if skill is in matched, partial, or missing
            matched_names = [get_skill_name(s) for s in analysis_result.get('matched_skills', [])]
            partial_names = [get_skill_name(s) for s in analysis_result.get('partial_matches', [])]
            missing_names = [get_skill_name(s) for s in analysis_result.get('missing_skills', [])]

            if skill in matched_names:
                status = 'Matched'
                # Find the actual skill object to get similarity
                for s in analysis_result.get('matched_skills', []):
                    if get_skill_name(s) == skill:
                        similarity = get_similarity(s)
                        break
            elif skill in partial_names:
                status = 'Partial'
                # Find the actual skill object to get similarity
                for s in analysis_result.get('partial_matches', []):
                    if get_skill_name(s) == skill:
                        similarity = get_similarity(s)
                        break
            elif skill in missing_names:
                status = 'Missing'
                # Find the actual skill object to get similarity
                for s in analysis_result.get('missing_skills', []):
                    if get_skill_name(s) == skill:
                        similarity = get_similarity(s)
                        break
            else:
                status = 'Unknown'
                similarity = 0.5

            # Find priority from priority gaps
            priority = 'N/A'
            for gap in analysis_result.get('priority_gaps', []):
                if gap['skill'] == skill:
                    priority = gap['priority'].title()
                    break

            # Find category
            category = 'Unknown'
            for s in resume_skills + jd_skills:
                if isinstance(s, dict) and s['name'] == skill:
                    category = s.get('category', 'Unknown')
                    break

            data.append([skill, category, in_resume, in_jd, status, f"{similarity:.1%}", priority])

        return data

# Main Application Class - MODIFIED TO USE MILESTONE 3
class AISkillGapAnalyzer:
    def __init__(self):
        self.logger = self._setup_logger()
        
        # Initialize components
        self.file_reader = EnhancedFileReader()
        self.skill_extractor = EnhancedSkillExtractor()
        self.visualizer = EnhancedVisualizer()
        self.report_generator = ReportGenerator()
        
        # Initialize Milestone 3 components if available
        if MILESTONE3_AVAILABLE:
            try:
                self.encoder = SentenceBERTEncoder()
                self.calculator = SimilarityCalculator()
                self.analyzer = SkillGapAnalyzer(self.encoder, self.calculator)
                self.learning_generator = LearningPathGenerator()
            except Exception as e:
                self.logger.warning(f"Failed to initialize Milestone 3 components: {e}")
                self.analyzer = None
                self.learning_generator = None
        else:
            self.analyzer = None
            self.learning_generator = None
        
        # Initialize embedding models
        self.embedding_models = {
            'all-MiniLM-L6-v2': 'sentence-transformers/all-MiniLM-L6-v2',
            'all-mpnet-base-v2': 'sentence-transformers/all-mpnet-base-v2',
            'multi-qa-mpnet-base-dot-v1': 'sentence-transformers/multi-qa-mpnet-base-dot-v1'
        }
        
        # Initialize ATS Score Checker
        self.ats_checker = ATSScoreChecker()
    
    def _setup_logger(self):
        logger = logging.getLogger('AISkillGapAnalyzer')
        if not logger.handlers:
            logger.setLevel(logging.INFO)
        return logger
    
    def process_file(self, uploaded_file, file_type):
        """Process uploaded file with detailed status tracking"""
        try:
            # Save temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            # Get file info
            file_ext = uploaded_file.name.split('.')[-1].lower()
            file_size = uploaded_file.size / 1024  # KB
            
            # Initialize status
            file_status = {
                'file_name': uploaded_file.name,
                'file_type': file_ext.upper(),
                'file_size': f"{file_size:.1f} KB",
                'pages': self.file_reader.count_pages(tmp_path),
                'parse_status': 'processing',
                'status_icon': '⏳',
                'error': None
            }
            
            try:
                # Read file content
                if file_ext == 'txt':
                    raw_text = self.file_reader.read_txt(tmp_path)
                    text_type = "text"
                    ocr_confidence = 1.0
                elif file_ext == 'pdf':
                    raw_text, text_type, ocr_confidence = self.file_reader.read_pdf(tmp_path)
                elif file_ext == 'docx':
                    raw_text = self.file_reader.read_docx(tmp_path)
                    text_type = "text"
                    ocr_confidence = 1.0
                else:
                    raise ValueError(f"Unsupported file format: {file_ext}")
                
                if not raw_text:
                    raise ValueError("No text could be extracted from the file")
                
                # Clean text
                try:
                    cleaned_text = remove_personal(raw_text)
                    cleaned_text = full_normalize(cleaned_text)
                    
                    # Track normalization
                    norm_summary = {
                        'original_length': len(raw_text),
                        'cleaned_length': len(cleaned_text),
                        'removed_lines': raw_text.count('\n') - cleaned_text.count('\n'),
                        'removed_chars': len(raw_text) - len(cleaned_text),
                        'ocr_used': text_type == 'ocr',
                        'ocr_confidence': ocr_confidence
                    }
                except:
                    cleaned_text = raw_text
                    norm_summary = {
                        'original_length': len(raw_text),
                        'cleaned_length': len(cleaned_text),
                        'removed_lines': 0,
                        'removed_chars': 0,
                        'ocr_used': False,
                        'ocr_confidence': 1.0
                    }
                
                # Extract skills
                skills = self.skill_extractor.extract_skills(
                    cleaned_text,
                    st.session_state.selected_model,
                    st.session_state.confidence_threshold
                )
                
                # Update status
                file_status.update({
                    'parse_status': 'success',
                    'status_icon': '✅',
                    'word_count': len(cleaned_text.split()),
                    'token_count': len(cleaned_text.split()) * 1.3,  # Approximate
                    'skills_count': len(skills)
                })
                
                # Cleanup
                os.unlink(tmp_path)
                
                return {
                    'success': True,
                    'raw_text': raw_text,
                    'cleaned_text': cleaned_text,
                    'skills': skills,
                    'file_status': file_status,
                    'normalization_summary': norm_summary
                }
                
            except Exception as e:
                file_status.update({
                    'parse_status': 'error',
                    'status_icon': '❌',
                    'error': str(e)
                })
                os.unlink(tmp_path)
                return {
                    'success': False,
                    'error': str(e),
                    'file_status': file_status
                }
                
        except Exception as e:
            self.logger.error(f"Error processing file: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_status': {
                    'file_name': uploaded_file.name,
                    'parse_status': 'error',
                    'status_icon': '❌',
                    'error': str(e)
                }
            }
    
    def analyze_gap(self, resume_skills, jd_skills):
        """Perform enhanced gap analysis using Milestone 3"""
        # Convert skills to simple lists for Milestone 3
        resume_skill_names = [s['name'] if isinstance(s, dict) else s for s in resume_skills]
        jd_skill_names = [s['name'] if isinstance(s, dict) else s for s in jd_skills]
        
        # Use Milestone 3 analyzer if available
        if self.analyzer:
            try:
                result = self.analyzer.analyze(resume_skill_names, jd_skill_names)
                
                # Convert Milestone 3 result to expected format
                if hasattr(result, 'get_statistics'):
                    stats = result.get_statistics()
                    return {
                        'matched_skills': [m.jd_skill for m in result.matched_skills],
                        'partial_matches': [m.jd_skill for m in result.partial_matches],
                        'missing_skills': result.missing_skills,  # Keep as SkillMatch objects for now
                        'overall_score': stats['overall_score'],
                        'similarity_matrix': getattr(result, 'similarity_matrix', None),
                        'priority_gaps': self._generate_priority_gaps(result.missing_skills, jd_skill_names)
                    }
                else:
                    # Fallback for different result format
                    return {
                        'matched_skills': result.get('matched_skills', []),
                        'partial_matches': result.get('partial_matches', []),
                        'missing_skills': result.get('missing_skills', []),
                        'overall_score': result.get('overall_score', 0),
                        'similarity_matrix': result.get('similarity_matrix', None),
                        'priority_gaps': self._generate_priority_gaps(result.get('missing_skills', []), jd_skill_names)
                    }
            except Exception as e:
                self.logger.error(f"Error using Milestone 3 analyzer: {e}")
                # Fall back to simple analysis
                return self._fallback_analysis(resume_skill_names, jd_skill_names)
        else:
            # Use fallback analysis
            return self._fallback_analysis(resume_skill_names, jd_skill_names)
    
    def _fallback_analysis(self, resume_skills, jd_skills):
        """Fallback analysis when Milestone 3 is not available"""
        # Simple set-based analysis
        resume_set = set(resume_skills)
        jd_set = set(jd_skills)
        
        matched = list(resume_set.intersection(jd_set))
        missing = list(jd_set - resume_set)
        
        # Calculate overall score
        total_skills = len(jd_skills)
        if total_skills > 0:
            overall_score = (len(matched) * 100) / total_skills
        else:
            overall_score = 0
        
        return {
            'matched_skills': matched,
            'partial_matches': [],  # No partial matches in fallback
            'missing_skills': missing,
            'overall_score': overall_score,
            'similarity_matrix': None,
            'priority_gaps': self._generate_priority_gaps(missing, jd_skills)
        }
    
    def _generate_priority_gaps(self, missing_skills, jd_skills):
        """Generate priority gaps from missing skills"""
        priority_gaps = []
        total_skills = len(jd_skills)
        
        for skill in missing_skills:
            # Handle both string and SkillMatch objects
            if isinstance(skill, str):
                skill_name = skill
                similarity = 0.0
            elif hasattr(skill, 'jd_skill'):  # SkillMatch object
                skill_name = skill.jd_skill
                similarity = skill.similarity
            else:
                continue  # Skip if we can't determine the skill name
            
            # Calculate importance based on JD frequency
            importance = jd_skills.count(skill_name) / total_skills if total_skills > 0 else 0
            priority = 'high' if importance > 0.05 else 'medium' if importance > 0.02 else 'low'
            
            priority_gaps.append({
                'skill': skill_name,
                'priority': priority,
                'importance': importance,
                'similarity': similarity,
                'suggested_action': self._get_suggested_action(skill_name)
            })
        
        # Sort by importance
        priority_gaps.sort(key=lambda x: x['importance'], reverse=True)
        return priority_gaps[:10]  # Top 10 gaps
    
    def _get_suggested_action(self, skill):
        """Get suggested action for missing skill"""
        actions = {
            'technical': f"Take an online course in {skill} and build a project",
            'soft': f"Practice {skill} through team projects and workshops",
            'tools': f"Complete tutorials and get hands-on experience with {skill}",
            'certifications': f"Pursue {skill} certification to validate your skills"
        }
        
        # Default action
        return f"Learn {skill} through online courses and practical experience"

# ATS Score Checker Class (unchanged from original)
class ATSScoreChecker:
    """Analyze resume against ATS criteria"""
    
    def __init__(self):
        self.logger = self._setup_logger()
    
    def calculate_ats_score(self, resume_text, jd_text, resume_skills, jd_skills):
        """Calculate overall ATS score based on multiple factors"""
        # Initialize scores for different factors
        keyword_match_score = self._calculate_keyword_match_score(resume_skills, jd_skills)
        formatting_score = self._calculate_formatting_score(resume_text)
        section_completeness_score = self._calculate_section_completeness_score(resume_text)
        readability_score = self._calculate_readability_score(resume_text)
        experience_relevance_score = self._calculate_experience_relevance_score(resume_text, jd_text)
        
        # Calculate weighted overall score
        weights = {
            'keyword_match': 0.4,
            'formatting': 0.15,
            'section_completeness': 0.15,
            'readability': 0.1,
            'experience_relevance': 0.2
        }
        
        overall_score = (
            keyword_match_score * weights['keyword_match'] +
            formatting_score * weights['formatting'] +
            section_completeness_score * weights['section_completeness'] +
            readability_score * weights['readability'] +
            experience_relevance_score * weights['experience_relevance']
        )
        
        # Determine score category
        if overall_score >= 0.8:
            score_category = "excellent"
        elif overall_score >= 0.6:
            score_category = "good"
        elif overall_score >= 0.4:
            score_category = "average"
        else:
            score_category = "poor"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            keyword_match_score, formatting_score, section_completeness_score,
            readability_score, experience_relevance_score, resume_text, jd_text
        )
        
        return {
            'overall_score': overall_score,
            'score_category': score_category,
            'factor_scores': {
                'keyword_match': {
                    'score': keyword_match_score,
                    'category': self._get_score_category(keyword_match_score),
                    'recommendations': recommendations['keyword_match']
                },
                'formatting': {
                    'score': formatting_score,
                    'category': self._get_score_category(formatting_score),
                    'recommendations': recommendations['formatting']
                },
                'section_completeness': {
                    'score': section_completeness_score,
                    'category': self._get_score_category(section_completeness_score),
                    'recommendations': recommendations['section_completeness']
                },
                'readability': {
                    'score': readability_score,
                    'category': self._get_score_category(readability_score),
                    'recommendations': recommendations['readability']
                },
                'experience_relevance': {
                    'score': experience_relevance_score,
                    'category': self._get_score_category(experience_relevance_score),
                    'recommendations': recommendations['experience_relevance']
                }
            },
            'missing_keywords': self._find_missing_keywords(resume_text, jd_text),
            'formatting_issues': self._identify_formatting_issues(resume_text)
        }
    
    def _calculate_keyword_match_score(self, resume_skills, jd_skills):
        """Calculate keyword matching score"""
        if not jd_skills:
            return 0.5  # Default score if no JD skills
        
        # Count matching skills
        resume_set = set(skill.lower() if isinstance(skill, str) else skill['name'].lower() for skill in resume_skills)
        jd_set = set(skill.lower() if isinstance(skill, str) else skill['name'].lower() for skill in jd_skills)
        
        matched = resume_set.intersection(jd_set)
        match_ratio = len(matched) / len(jd_set)
        
        return match_ratio
    
    def _calculate_formatting_score(self, resume_text):
        """Calculate formatting score based on ATS-friendly formatting"""
        score = 0.5  # Base score
        
        # Check for common formatting issues
        issues = 0
        
        # Check for tables (bad for ATS)
        if '|' in resume_text and '\n' in resume_text:
            table_lines = [line for line in resume_text.split('\n') if '|' in line and line.count('|') > 2]
            if table_lines:
                issues += 0.2
        
        # Check for multiple columns (bad for ATS)
        lines = resume_text.split('\n')
        if len(lines) > 20:
            # Simple heuristic for multiple columns
            avg_line_length = sum(len(line) for line in lines) / len(lines)
            if avg_line_length < 40:  # Likely multiple columns
                issues += 0.15
        
        # Check for headers/footers (bad for ATS)
        if 'page' in resume_text.lower() and ('of' in resume_text.lower() or '/' in resume_text):
            issues += 0.1
        
        # Check for special characters
        special_chars = ['•', '■', '◆', '★', '✓', '✗']
        for char in special_chars:
            if char in resume_text:
                issues += 0.05
        
        # Adjust score based on issues
        score = max(0.1, score - issues)
        
        return min(1.0, score)
    
    def _calculate_section_completeness_score(self, resume_text):
        """Calculate score based on presence of important resume sections"""
        score = 0
        total_sections = 6
        
        # Check for key sections
        sections = [
            ('contact', ['email', 'phone', 'address', 'linkedin', 'github']),
            ('summary', ['summary', 'objective', 'profile', 'about']),
            ('experience', ['experience', 'work', 'employment', 'job']),
            ('education', ['education', 'university', 'college', 'degree']),
            ('skills', ['skills', 'competencies', 'abilities', 'expertise']),
            ('projects', ['projects', 'portfolio', 'work'])
        ]
        
        text_lower = resume_text.lower()
        
        for section_name, keywords in sections:
            if any(keyword in text_lower for keyword in keywords):
                score += 1
        
        return score / total_sections
    
    def _calculate_readability_score(self, resume_text):
        """Calculate readability score"""
        # Simple readability metrics
        sentences = resume_text.split('.')
        words = resume_text.split()
        
        if not sentences or not words:
            return 0.5
        
        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)
        
        # Score based on sentence length (ideal is 15-20 words)
        if 15 <= avg_sentence_length <= 20:
            sentence_score = 1.0
        elif 10 <= avg_sentence_length < 15 or 20 < avg_sentence_length <= 25:
            sentence_score = 0.8
        elif 5 <= avg_sentence_length < 10 or 25 < avg_sentence_length <= 30:
            sentence_score = 0.6
        else:
            sentence_score = 0.4
        
        # Check for paragraphs that are too long
        paragraphs = [p for p in resume_text.split('\n\n') if p.strip()]
        long_paragraphs = sum(1 for p in paragraphs if len(p.split()) > 100)
        
        paragraph_score = max(0.2, 1.0 - (long_paragraphs / len(paragraphs)) * 0.5) if paragraphs else 0.5
        
        # Calculate overall readability score
        readability_score = (sentence_score * 0.6 + paragraph_score * 0.4)
        
        return readability_score
    
    def _calculate_experience_relevance_score(self, resume_text, jd_text):
        """Calculate score based on relevance of experience to job description"""
        # Extract key terms from JD
        jd_words = set(word.lower() for word in re.findall(r'\b\w+\b', jd_text) if len(word) > 3)
        resume_words = set(word.lower() for word in re.findall(r'\b\w+\b', resume_text) if len(word) > 3)
        
        # Calculate overlap
        overlap = len(jd_words.intersection(resume_words))
        relevance_score = overlap / len(jd_words) if jd_words else 0.5
        
        return relevance_score
    
    def _find_missing_keywords(self, resume_text, jd_text):
        """Find important keywords from JD that are missing in resume"""
        # Extract potential keywords from JD (simple approach)
        jd_words = re.findall(r'\b\w+\b', jd_text.lower())
        resume_words = re.findall(r'\b\w+\b', resume_text.lower())
        
        # Filter out common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
        
        jd_keywords = [word for word in jd_words if word not in common_words and len(word) > 3]
        resume_keywords = [word for word in resume_words if word not in common_words and len(word) > 3]
        
        # Find missing keywords
        missing_keywords = []
        for keyword in jd_keywords:
            if keyword not in resume_keywords and jd_words.count(keyword) > 1:  # Only consider if it appears more than once
                missing_keywords.append(keyword)
        
        # Return top missing keywords
        return list(set(missing_keywords))[:10]
    
    def _identify_formatting_issues(self, resume_text):
        """Identify specific formatting issues"""
        issues = []
        
        # Check for tables
        if '|' in resume_text and '\n' in resume_text:
            table_lines = [line for line in resume_text.split('\n') if '|' in line and line.count('|') > 2]
            if table_lines:
                issues.append("Tables detected - ATS systems may not parse tables correctly")
        
        # Check for multiple columns
        lines = resume_text.split('\n')
        if len(lines) > 20:
            avg_line_length = sum(len(line) for line in lines) / len(lines)
            if avg_line_length < 40:
                issues.append("Possible multiple-column format - ATS systems read left to right")
        
        # Check for headers/footers
        if 'page' in resume_text.lower() and ('of' in resume_text.lower() or '/' in resume_text):
            issues.append("Page numbers detected - not necessary for ATS")
        
        # Check for special characters
        special_chars = ['■', '◆', '★', '✓', '✗']
        found_chars = [char for char in special_chars if char in resume_text]
        if found_chars:
            issues.append(f"Special characters detected: {', '.join(found_chars)} - use standard bullet points instead")
        
        return issues
    
    def _generate_recommendations(self, keyword_score, formatting_score, section_score, 
                                readability_score, experience_score, resume_text, jd_text):
        """Generate specific recommendations based on scores"""
        recommendations = {
            'keyword_match': [],
            'formatting': [],
            'section_completeness': [],
            'readability': [],
            'experience_relevance': []
        }
        
        # Keyword match recommendations
        if keyword_score < 0.7:
            missing_keywords = self._find_missing_keywords(resume_text, jd_text)
            if missing_keywords:
                recommendations['keyword_match'].append(f"Add these keywords from the job description: {', '.join(missing_keywords[:5])}")
            recommendations['keyword_match'].append("Mirror the language used in the job description")
        
        # Formatting recommendations
        if formatting_score < 0.7:
            recommendations['formatting'].append("Remove tables and use a single-column layout")
            recommendations['formatting'].append("Use standard bullet points (- or *) instead of special characters")
            recommendations['formatting'].append("Remove headers, footers, and page numbers")
        
        # Section completeness recommendations
        if section_score < 0.7:
            text_lower = resume_text.lower()
            if not any(keyword in text_lower for keyword in ['summary', 'objective', 'profile']):
                recommendations['section_completeness'].append("Add a professional summary section")
            if not any(keyword in text_lower for keyword in ['skills', 'competencies']):
                recommendations['section_completeness'].append("Add a dedicated skills section")
            if not any(keyword in text_lower for keyword in ['projects', 'portfolio']):
                recommendations['section_completeness'].append("Consider adding a projects section")
        
        # Readability recommendations
        if readability_score < 0.7:
            recommendations['readability'].append("Keep sentences between 15-20 words on average")
            recommendations['readability'].append("Break up long paragraphs (more than 100 words)")
        
        # Experience relevance recommendations
        if experience_score < 0.7:
            recommendations['experience_relevance'].append("Quantify your achievements with metrics")
            recommendations['experience_relevance'].append("Use action verbs that match the job description")
        
        return recommendations
    
    def _get_score_category(self, score):
        """Get category for a score"""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "average"
        else:
            return "poor"
    
    def _setup_logger(self):
        logger = logging.getLogger('ATSScoreChecker')
        if not logger.handlers:
            logger.setLevel(logging.INFO)
        return logger

# Initialize the main analyzer
analyzer = AISkillGapAnalyzer()

# Render Hero Section
def render_hero():
    st.markdown("""
    <div class="hero-container">
        <div class="floating-shape" style="width: 100px; height: 100px; border-radius: 50%; background: white; top: 10%; right: 10%;"></div>
        <div class="floating-shape" style="width: 60px; height: 60px; border-radius: 50%; background: white; bottom: 20%; left: 15%;"></div>
        <h1 class="hero-title">🧠 AI Skill Gap Analyzer Pro</h1>
        <p class="hero-subtitle">Transform Your Career with Intelligent Skill Analysis</p>
    </div>
    """, unsafe_allow_html=True)

# Render Progress Steps with Navigation
def render_progress():
    steps = [
        ("📄 Upload", 1),
        ("🔍 Extract", 2),
        ("📊 Analyze", 3),
        ("🎯 Gaps", 4),
        ("📈 Visualize", 5),
        ("🤖 ATS", 6)
    ]
    
    st.markdown("""
    <div class="progress-container">
        <div class="progress-line {}"></div>
    """.format(
        "progress-line-active" if st.session_state.current_step > 1 else ""
    ), unsafe_allow_html=True)
    
    cols = st.columns(len(steps))
    for i, (title, step) in enumerate(steps):
        with cols[i]:
            status = ""
            if st.session_state.current_step > step:
                status = "completed"
            elif st.session_state.current_step == step:
                status = "active"
            
            # Make completed steps clickable for navigation
            clickable = "clickable" if st.session_state.max_step_reached > step else ""
            
            st.markdown(f"""
            <div class="progress-step {status} {clickable}">
                <div class="progress-circle">
                    {step if status != "completed" else "✓"}
                </div>
                <div style="font-size: 0.9rem; font-weight: 500;">
                    {title}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Add button for navigation if step is completed
            if st.session_state.max_step_reached > step and st.session_state.current_step != step:
                if st.button(f"Go to {title}", key=f"nav_{step}", help=f"Navigate to {title}"):
                    st.session_state.current_step = step
                    st.rerun()

# Sidebar with Settings
def render_sidebar():
    with st.sidebar:
        st.markdown("### ⚙️ Analysis Settings")
        
        # Model selection
        model_options = ["spaCy base model", "Custom NER", "Keyword list"]
        st.session_state.selected_model = st.selectbox(
            "Extraction Model",
            model_options,
            index=model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else 0
        )
        
        # Confidence threshold
        st.session_state.confidence_threshold = st.slider(
            "Confidence Threshold",
            0.0, 1.0, st.session_state.confidence_threshold, 0.05
        )
        
        # Similarity threshold
        st.session_state.similarity_threshold = st.slider(
            "Similarity Threshold",
            0.0, 1.0, st.session_state.similarity_threshold, 0.05
        )
        
        # Embedding model
        st.session_state.embedding_model = st.selectbox(
            "Embedding Model",
            list(analyzer.embedding_models.keys()),
            index=list(analyzer.embedding_models.keys()).index(st.session_state.embedding_model) if st.session_state.embedding_model in analyzer.embedding_models else 0
        )
        
        st.markdown("---")
        
        # Export options
        st.markdown("### 📥 Export Options")
        export_format = st.selectbox("Format", ["PDF", "CSV", "JSON"])
        
        if st.button("Generate Report"):
            if export_format == "PDF":
                generate_pdf_report()
            elif export_format == "CSV":
                generate_csv_report()
            else:
                generate_json_report()
        
        st.markdown("---")
        
        # Reset button
        if st.button("🔄 Start New Analysis", type="secondary"):
            for key in list(st.session_state.keys()):
                if key != 'current_step':
                    del st.session_state[key]
            st.session_state.current_step = 1
            st.session_state.processing_complete = False
            st.session_state.max_step_reached = 1
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 About")
        st.info("""
        **AI Skill Gap Analyzer Pro**
        
        This tool analyzes your resume against job descriptions to:
        - Extract skills using advanced NLP
        - Identify skill gaps
        - Provide personalized learning paths
        - Check ATS compatibility
        
        Version: 4.0 Enhanced with Milestone 3 Integration
        """)

# Step 1: File Upload with Status
def render_file_upload():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">📄 Step 1: Upload Your Documents</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        st.markdown("### 📋 Resume")
        resume_file = st.file_uploader(
            "Upload your resume",
            type=['pdf', 'docx', 'txt'],
            key="resume_upload",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if resume_file:
            st.session_state.resume_file = resume_file
            st.success(f"✅ Resume uploaded: {resume_file.name}")
    
    with col2:
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        st.markdown("### 💼 Job Description")
        jd_file = st.file_uploader(
            "Upload job description",
            type=['pdf', 'docx', 'txt'],
            key="jd_upload",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if jd_file:
            st.session_state.jd_file = jd_file
            st.success(f"✅ Job description uploaded: {jd_file.name}")
    
    # Alternative text input
    with st.expander("📝 Or paste text directly"):
        col1, col2 = st.columns(2)
        with col1:
            resume_text = st.text_area("Paste Resume Text", height=200, key="resume_text_input")
            if resume_text:
                st.session_state.resume_text = resume_text
        with col2:
            jd_text = st.text_area("Paste Job Description", height=200, key="jd_text_input")
            if jd_text:
                st.session_state.jd_text = jd_text
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process button
    if (st.session_state.resume_file or st.session_state.resume_text) and \
       (st.session_state.jd_file or st.session_state.jd_text):
        if st.button("🚀 Process Documents", type="primary", use_container_width=True):
            process_documents()

# Process Documents with Status Tracking
def process_documents():
    with st.spinner("🔄 Processing documents..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Clear previous status
            st.session_state.file_status = []
            
            # Process Resume
            status_text.text("Processing resume...")
            progress_bar.progress(20)
            
            if st.session_state.resume_file:
                resume_result = analyzer.process_file(st.session_state.resume_file, "resume")
                st.session_state.file_status.append(resume_result['file_status'])
            else:
                resume_result = {
                    'success': True,
                    'raw_text': st.session_state.resume_text,
                    'cleaned_text': st.session_state.resume_text,
                    'skills': analyzer.skill_extractor.extract_skills(
                        st.session_state.resume_text,
                        st.session_state.selected_model,
                        st.session_state.confidence_threshold
                    ),
                    'file_status': {
                        'file_name': "Pasted Resume",
                        'file_type': 'TXT',
                        'parse_status': 'success',
                        'status_icon': '✅'
                    },
                    'normalization_summary': {
                        'original_length': len(st.session_state.resume_text),
                        'cleaned_length': len(st.session_state.resume_text),
                        'removed_lines': 0,
                        'removed_chars': 0,
                        'ocr_used': False,
                        'ocr_confidence': 1.0
                    }
                }
            
            if resume_result['success']:
                st.session_state.cleaned_resume = resume_result['cleaned_text']
                st.session_state.resume_skills = resume_result['skills']
                st.session_state.normalization_summary['resume'] = resume_result['normalization_summary']
                progress_bar.progress(40)
            else:
                st.error(f"Error processing resume: {resume_result['error']}")
                return
            
            # Process Job Description
            status_text.text("Processing job description...")
            progress_bar.progress(60)
            
            if st.session_state.jd_file:
                jd_result = analyzer.process_file(st.session_state.jd_file, "jd")
                st.session_state.file_status.append(jd_result['file_status'])
            else:
                jd_result = {
                    'success': True,
                    'raw_text': st.session_state.jd_text,
                    'cleaned_text': st.session_state.jd_text,
                    'skills': analyzer.skill_extractor.extract_skills(
                        st.session_state.jd_text,
                        st.session_state.selected_model,
                        st.session_state.confidence_threshold
                    ),
                    'file_status': {
                        'file_name': "Pasted Job Description",
                        'file_type': 'TXT',
                        'parse_status': 'success',
                        'status_icon': '✅'
                    },
                    'normalization_summary': {
                        'original_length': len(st.session_state.jd_text),
                        'cleaned_length': len(st.session_state.jd_text),
                        'removed_lines': 0,
                        'removed_chars': 0,
                        'ocr_used': False,
                        'ocr_confidence': 1.0
                    }
                }
            
            if jd_result['success']:
                st.session_state.cleaned_jd = jd_result['cleaned_text']
                st.session_state.jd_skills = jd_result['skills']
                st.session_state.normalization_summary['jd'] = jd_result['normalization_summary']
                progress_bar.progress(80)
            else:
                st.error(f"Error processing job description: {jd_result['error']}")
                return
            
            # Update state
            st.session_state.current_step = 2
            st.session_state.processing_complete = True
            st.session_state.milestone1_complete = True
            st.session_state.milestone2_complete = True
            st.session_state.max_step_reached = 2
            status_text.text("✅ Processing complete!")
            st.success("🎉 Documents processed successfully!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Processing failed: {str(e)}")
        finally:
            progress_bar.empty()
            status_text.empty()

# Step 2: File Status and Text Preview
def render_file_status():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">📊 File Processing Status</div>', unsafe_allow_html=True)
    
    # Display file status
    for status in st.session_state.file_status:
        status_class = status['parse_status']
        st.markdown(f"""
        <div class="file-status {status_class}">
            <span class="file-status-icon">{status['status_icon']}</span>
            <div>
                <strong>{status['file_name']}</strong><br>
                Type: {status['file_type']} | Size: {status.get('file_size', 'N/A')}
                {f"| Pages: {status['pages']}" if 'pages' in status else ""}
                {f"| Words: {status['word_count']}" if 'word_count' in status else ""}
                {f"| Skills: {status['skills_count']}" if 'skills_count' in status else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if status.get('error'):
            st.error(f"Error: {status['error']}")
    
    # Display normalization summary
    if st.session_state.normalization_summary:
        st.markdown('<div class="card-header">🧹 Normalization Summary</div>', unsafe_allow_html=True)
        
        for doc_type, summary in st.session_state.normalization_summary.items():
            st.markdown(f"""
            <div class="norm-summary">
                <strong>{doc_type.title()}:</strong><br>
                Original: {summary['original_length']} chars → Cleaned: {summary['cleaned_length']} chars<br>
                Removed: {summary['removed_lines']} lines, {summary['removed_chars']} characters
                {f"| OCR Used: Yes (Confidence: {summary['ocr_confidence']:.1%})" if summary['ocr_used'] else ""}
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Step 3: Skill Extraction with Controls
def render_skill_extraction():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">🔍 Extracted Skills</div>', unsafe_allow_html=True)
    
    # Extraction controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Extraction Model:**")
        st.info(st.session_state.selected_model)
    
    with col2:
        st.markdown("**Confidence Threshold:**")
        st.info(f"{st.session_state.confidence_threshold:.2f}")
    
    with col3:
        st.markdown("**Total Skills:**")
        st.info(f"Resume: {len(st.session_state.resume_skills)} | JD: {len(st.session_state.jd_skills)}")
    
    # Display skills by category
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Resume Skills")
        
        # Group by category
        resume_by_category = defaultdict(list)
        for skill in st.session_state.resume_skills:
            resume_by_category[skill['category']].append(skill)
        
        for category in ['technical', 'soft', 'tools', 'certifications']:
            if category in resume_by_category:
                with st.expander(f"{category.title()} Skills ({len(resume_by_category[category])})"):
                    for skill in resume_by_category[category]:
                        col_name, col_conf, col_occ = st.columns([3, 1, 1])
                        with col_name:
                            st.markdown(f'<span class="skill-tag skill-matched">{skill["name"]}</span>', unsafe_allow_html=True)
                        with col_conf:
                            st.write(f"{skill['confidence']:.2f}")
                        with col_occ:
                            st.write(f"({skill['occurrences']})")
                        
                        # Show sentences on click
                        if skill['sentences']:
                            with st.expander("📝 Context", expanded=False):
                                for sentence in skill['sentences']:
                                    st.write(f"• {sentence}")
    
    with col2:
        st.markdown("### 💼 Job Description Skills")
        
        # Group by category
        jd_by_category = defaultdict(list)
        for skill in st.session_state.jd_skills:
            jd_by_category[skill['category']].append(skill)
        
        for category in ['technical', 'soft', 'tools', 'certifications']:
            if category in jd_by_category:
                with st.expander(f"{category.title()} Skills ({len(jd_by_category[category])})"):
                    for skill in jd_by_category[category]:
                        col_name, col_conf, col_occ = st.columns([3, 1, 1])
                        with col_name:
                            st.markdown(f'<span class="skill-tag skill-missing">{skill["name"]}</span>', unsafe_allow_html=True)
                        with col_conf:
                            st.write(f"{skill['confidence']:.2f}")
                        with col_occ:
                            st.write(f"({skill['occurrences']})")
                        
                        # Show sentences on click
                        if skill['sentences']:
                            with st.expander("📝 Context", expanded=False):
                                for sentence in skill['sentences']:
                                    st.write(f"• {sentence}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Analyze button
    if st.button("📊 Analyze Skill Gap", type="primary", use_container_width=True):
        perform_gap_analysis()

# Step 4: Gap Analysis Results
def perform_gap_analysis():
    with st.spinner("🔍 Analyzing skill gaps..."):
        try:
            result = analyzer.analyze_gap(st.session_state.resume_skills, st.session_state.jd_skills)
            
            if result:
                st.session_state.analysis_result = result
                st.session_state.current_step = 3
                st.session_state.milestone3_complete = True
                st.session_state.max_step_reached = 3
                st.success("✅ Gap analysis complete!")
                st.rerun()
            else:
                st.error("❌ Analysis failed. Please try again.")
        except Exception as e:
            st.error(f"Analysis error: {str(e)}")

def render_gap_analysis():
    if not st.session_state.analysis_result:
        return
    
    result = st.session_state.analysis_result
    
    # Metrics Dashboard
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">📊 Gap Analysis Results</div>', unsafe_allow_html=True)
    
    # Calculate metrics
    matched = len(result.get('matched_skills', []))
    partial = len(result.get('partial_matches', []))
    missing = len(result.get('missing_skills', []))
    overall_score = result.get('overall_score', 0)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{overall_score:.1f}%</div>
            <div class="metric-label">Match Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{matched}</div>
            <div class="metric-label">✅ Matched</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{partial}</div>
            <div class="metric-label">⚠️ Partial</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{missing}</div>
            <div class="metric-label">❌ Missing</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed Results
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### ✅ Matched Skills")
        for skill in result.get('matched_skills', [])[:10]:
            # Handle both string and SkillMatch objects
            skill_name = skill.jd_skill if hasattr(skill, 'jd_skill') else skill
            st.markdown(f'<span class="skill-tag skill-matched">{skill_name}</span>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### ⚠️ Partial Matches")
        for skill in result.get('partial_matches', [])[:10]:
            # Handle both string and SkillMatch objects
            skill_name = skill.jd_skill if hasattr(skill, 'jd_skill') else skill
            similarity = skill.similarity if hasattr(skill, 'similarity') else 0.7
            st.markdown(f'<span class="skill-tag skill-partial">{skill_name} ({similarity:.1%})</span>', unsafe_allow_html=True)
    
    with col3:
        st.markdown("### ❌ Missing Skills")
        for skill in result.get('missing_skills', [])[:10]:
            # Handle both string and SkillMatch objects
            skill_name = skill.jd_skill if hasattr(skill, 'jd_skill') else skill
            similarity = skill.similarity if hasattr(skill, 'similarity') else 0.0
            st.markdown(f'<span class="skill-tag skill-missing">{skill_name} ({similarity:.1%})</span>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # High Priority Gaps
    if result.get('priority_gaps'):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">🎯 High Priority Skill Gaps</div>', unsafe_allow_html=True)
        
        for gap in result.get('priority_gaps', [])[:5]:
            priority_class = gap['priority']
            similarity_text = f" (Similarity: {gap.get('similarity', 0):.1%})" if 'similarity' in gap else ""
            st.markdown(f"""
            <div class="priority-gap {priority_class}">
                <strong>{gap['skill']}</strong>{similarity_text} - {gap['priority'].title()} Priority<br>
                <small>Importance: {gap['importance']:.1%} | {gap['suggested_action']}</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Generate Learning Path button
    if st.button("🎓 Generate Learning Path", type="primary", use_container_width=True):
        generate_learning_path()

# Step 5: Visualizations
def render_visualizations():
    if not st.session_state.analysis_result:
        return
    
    result = st.session_state.analysis_result
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">📈 Visual Analytics</div>', unsafe_allow_html=True)
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Tag Cloud", "Radar Chart", "Heatmap", "Distribution"])
    
    with tab1:
        st.subheader("Skills Tag Cloud")
        # Create tag cloud for resume skills
        tag_cloud_img = analyzer.visualizer.create_tag_cloud(st.session_state.resume_skills)
        if tag_cloud_img:
            st.image(tag_cloud_img, use_container_width=True)
        else:
            st.info("No skills to display in tag cloud")
    
    with tab2:
        st.subheader("Skill Category Comparison")
        radar_chart = analyzer.visualizer.create_radar_chart(
            st.session_state.resume_skills,
            st.session_state.jd_skills
        )
        st.plotly_chart(radar_chart, use_container_width=True)
    
    with tab3:
        st.subheader("Similarity Heatmap")
        if 'similarity_matrix' in result and result['similarity_matrix'] is not None:
            heatmap = analyzer.visualizer.create_similarity_heatmap(
                result['similarity_matrix'],
                [s['name'] if isinstance(s, dict) else s for s in st.session_state.resume_skills],
                [s['name'] if isinstance(s, dict) else s for s in st.session_state.jd_skills]
            )
            st.plotly_chart(heatmap, use_container_width=True)
        else:
            st.info("Similarity matrix not available")
    
    with tab4:
        st.subheader("Skill Distribution")
        dist_chart = analyzer.visualizer.create_skill_distribution(st.session_state.resume_skills)
        st.plotly_chart(dist_chart, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Proceed to ATS Score
    if st.button("Next ➡️ ATS Score", type="primary", use_container_width=True):
        st.session_state.current_step = 6
        st.session_state.max_step_reached = 6
        st.rerun()

# Step 6: ATS Score Checker
def render_ats_score():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">🤖 ATS Score Checker</div>', unsafe_allow_html=True)
    
    # Calculate ATS score if not already done
    if not st.session_state.ats_score:
        with st.spinner("Analyzing your resume for ATS compatibility..."):
            ats_result = analyzer.ats_checker.calculate_ats_score(
                st.session_state.cleaned_resume,
                st.session_state.cleaned_jd,
                st.session_state.resume_skills,
                st.session_state.jd_skills
            )
            st.session_state.ats_score = ats_result['overall_score']
            st.session_state.ats_analysis = ats_result
    
    # Display overall ATS score
    score = st.session_state.ats_score
    score_category = st.session_state.ats_analysis['score_category']
    
    # Determine score color and text
    if score_category == 'excellent':
        score_class = 'ats-score-excellent'
        score_text = 'Excellent'
        score_desc = 'Your resume is highly optimized for ATS systems'
    elif score_category == 'good':
        score_class = 'ats-score-good'
        score_text = 'Good'
        score_desc = 'Your resume is well-optimized for ATS systems'
    elif score_category == 'average':
        score_class = 'ats-score-average'
        score_text = 'Average'
        score_desc = 'Your resume has some ATS optimization issues'
    else:
        score_class = 'ats-score-poor'
        score_text = 'Poor'
        score_desc = 'Your resume needs significant ATS optimization'
    
    # Display score circle
    st.markdown(f"""
    <div class="ats-score-container">
        <div class="ats-score-circle {score_class}">
            {int(score * 100)}%
        </div>
        <h3>{score_text}</h3>
        <p>{score_desc}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display factor scores
    st.subheader("ATS Optimization Factors")
    
    factor_scores = st.session_state.ats_analysis['factor_scores']
    
    for factor_name, factor_data in factor_scores.items():
        factor_score = factor_data['score']
        factor_category = factor_data['category']
        
        # Determine factor score color
        if factor_category == 'excellent':
            factor_class = 'ats-factor-excellent'
        elif factor_category == 'good':
            factor_class = 'ats-factor-good'
        elif factor_category == 'average':
            factor_class = 'ats-factor-average'
        else:
            factor_class = 'ats-factor-poor'
        
        # Display factor
        st.markdown(f"""
        <div class="ats-factor">
            <div class="ats-factor-header">
                <div class="ats-factor-title">{factor_name.replace('_', ' ').title()}</div>
                <div class="ats-factor-score {factor_class}">{int(factor_score * 100)}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display recommendations
        if factor_data['recommendations']:
            with st.expander(f"Recommendations for {factor_name.replace('_', ' ').title()}"):
                for rec in factor_data['recommendations']:
                    st.write(f"• {rec}")
    
    # Display missing keywords only if there are any
    if st.session_state.ats_analysis['missing_keywords']:
        st.markdown('<div class="ats-missing-keywords">', unsafe_allow_html=True)
        st.markdown('<div class="ats-missing-keywords-title">Missing Keywords</div>', unsafe_allow_html=True)
        st.markdown("Consider adding these keywords from the job description to your resume:")
        
        missing_keywords = st.session_state.ats_analysis['missing_keywords']
        keyword_tags = "".join([
            f'<span class="skill-tag skill-missing">{keyword}</span>'
            for keyword in missing_keywords
        ])
        st.markdown(keyword_tags, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Display formatting issues only if there are any
    if st.session_state.ats_analysis['formatting_issues']:
        st.markdown('<div class="ats-formatting-issues">', unsafe_allow_html=True)
        st.markdown('<div class="ats-formatting-issues-title">Formatting Issues</div>', unsafe_allow_html=True)
        for issue in st.session_state.ats_analysis['formatting_issues']:
            st.markdown(f'<div class="ats-formatting-issue">- {issue}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ATS optimization tips
    st.markdown('<div class="ats-tips">', unsafe_allow_html=True)
    st.markdown('<div class="ats-tips-title">General ATS Optimization Tips</div>', unsafe_allow_html=True)
    tips = [
        "Use Standard Formatting: Avoid tables, columns, and special characters that ATS systems can't parse.",
        "Include Keywords: Mirror the language and keywords from the job description.",
        "Use Standard Section Headers: Use common section titles like \"Experience\", \"Education\", \"Skills\".",
        "Quantify Achievements: Use numbers and metrics to demonstrate your impact.",
        "Keep It Simple: Use a clean, single-column layout with standard fonts.",
        "Avoid Headers/Footers: ATS systems may not read content in headers or footers.",
        "Use Standard Bullet Points: Stick to standard bullet points (- or *) instead of special characters.",
        "Save as Text-Based PDF: Ensure your PDF is text-based, not image-based."
    ]
    
    for tip in tips:
        st.markdown(f'<div class="ats-tip">- {tip}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Export Functions
def generate_pdf_report():
    """Generate and download PDF report"""
    try:
        html_content = analyzer.report_generator.generate_pdf_report(
            st.session_state.resume_skills,
            st.session_state.jd_skills,
            st.session_state.analysis_result,
            st.session_state.ats_score
        )

        # Convert to PDF (simplified - in production use proper PDF library)
        st.download_button(
            label="📥 Download PDF Report",
            data=html_content,
            file_name=f"skill_gap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            mime="text/html",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error generating PDF report: {str(e)}")

def generate_csv_report():
    """Generate and download CSV report"""
    try:
        csv_data = analyzer.report_generator.generate_csv_report(
            st.session_state.resume_skills,
            st.session_state.jd_skills,
            st.session_state.analysis_result
        )

        df = pd.DataFrame(csv_data[1:], columns=csv_data[0])
        csv = df.to_csv(index=False)

        st.download_button(
            label="📥 Download CSV Report",
            data=csv,
            file_name=f"skill_gap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error generating CSV report: {str(e)}")

def generate_json_report():
    """Generate and download JSON report"""
    try:
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'resume_skills': st.session_state.resume_skills,
            'jd_skills': st.session_state.jd_skills,
            'analysis_result': st.session_state.analysis_result,
            'ats_score': st.session_state.ats_score,
            'ats_analysis': st.session_state.ats_analysis,
            'settings': {
                'model': st.session_state.selected_model,
                'confidence_threshold': st.session_state.confidence_threshold,
                'similarity_threshold': st.session_state.similarity_threshold
            }
        }
        
        json_report = json.dumps(report_data, indent=2, default=str)
        
        st.download_button(
            label="📥 Download JSON Report",
            data=json_report,
            file_name=f"skill_gap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error generating JSON report: {str(e)}")

# Learning Path Generation
def generate_learning_path():
    """Generate learning path based on missing skills"""
    with st.spinner("🎓 Generating personalized learning path..."):
        try:
            missing_skills = st.session_state.analysis_result.get('missing_skills', [])
            priority_gaps = st.session_state.analysis_result.get('priority_gaps', [])
            
            # Generate learning recommendations
            learning_path = []
            for gap in priority_gaps[:5]:  # Top 5 gaps
                # Extract skill name from gap dictionary
                skill_name = gap['skill']
                
                # Determine priority and estimated time
                priority = gap['priority']
                estimated_time = '4-6 weeks' if priority == 'high' else '2-4 weeks'
                
                # Create resources with proper skill name
                resources = [
                    f"Online course: {skill_name} for Beginners",
                    f"Practice projects on {skill_name}",
                    f"Certification: {skill_name} Professional" if skill_name not in ['Communication', 'Leadership'] else f"Workshop: {skill_name} Training"
                ]
                
                learning_path.append({
                    'skill': skill_name,
                    'priority': priority,
                    'importance': gap['importance'],
                    'estimated_time': estimated_time,
                    'resources': resources,
                    'action': gap['suggested_action']
                })
            
            st.session_state.learning_path = learning_path
            st.session_state.current_step = 4
            st.session_state.max_step_reached = 4
            st.success("✅ Learning path generated!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error generating learning path: {str(e)}")

# In render_learning_path function:
def render_learning_path():
    if not st.session_state.learning_path:
        return
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">🎓 Your Personalized Learning Path</div>', unsafe_allow_html=True)
    
    for i, item in enumerate(st.session_state.learning_path, 1):
        priority_color = '#dc3545' if item['priority'] == 'high' else '#ffc107' if item['priority'] == 'medium' else '#17a2b8'
        
        st.markdown(f"""
        <div style="border-left: 4px solid {priority_color}; padding-left: 1rem; margin-bottom: 1.5rem;">
            <h4>{i}. {item['skill']} <span style="color: {priority_color};">({item['priority'].title()} Priority)</span></h4>
            <p><strong>Importance:</strong> {item['importance']:.1%}</p>
            <p><strong>Estimated Time:</strong> {item['estimated_time']}</p>
            <p><strong>Recommended Action:</strong> {item['action']}</p>
            <p><strong>Resources:</strong></p>
            <ul>
        """, unsafe_allow_html=True)
        
        for resource in item['resources']:
            st.markdown(f"<li>{resource}</li>", unsafe_allow_html=True)
        
        st.markdown("</ul></div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Proceed to visualizations
    if st.button("Next ➡️ View Visualizations", type="primary", use_container_width=True):
        st.session_state.current_step = 5
        st.session_state.max_step_reached = 5
        st.rerun()

# Main Application Flow
def main():
    # Render Hero
    render_hero()
    
    # Render Progress
    render_progress()
    
    # Render Sidebar
    render_sidebar()
    
    # Render content based on current step
    if st.session_state.current_step == 1:
        render_file_upload()
    elif st.session_state.current_step == 2:
        render_file_status()
        render_skill_extraction()
    elif st.session_state.current_step == 3:
        render_gap_analysis()
    elif st.session_state.current_step == 4:
        render_learning_path()
    elif st.session_state.current_step == 5:
        render_visualizations()
    elif st.session_state.current_step == 6:
        render_ats_score()
    
    # Navigation buttons
    if st.session_state.current_step > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Previous", key="prev_main"):
                st.session_state.current_step -= 1
                st.rerun()

if __name__ == "__main__":
    main()