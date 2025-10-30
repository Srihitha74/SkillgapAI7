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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Hero Section with Animated Background */
    .hero-container {
        background: linear-gradient(135deg, 
            rgba(102, 126, 234, 0.9) 0%, 
            rgba(118, 75, 162, 0.9) 50%,
            rgba(102, 126, 234, 0.7) 100%);
        padding: 4rem 2rem;
        border-radius: 25px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.1),
            0 0 100px rgba(102, 126, 234, 0.2);
    }
    
    .hero-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, 
            transparent 0%, 
            rgba(255, 255, 255, 0.1) 50%, 
            transparent 100%);
        animation: shimmer 8s infinite linear;
        z-index: 1;
    }
    
    .hero-title {
        font-size: 4rem;
        font-weight: 800;
        margin-bottom: 1rem;
        animation: fadeInUp 1s ease-out;
        text-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        background: linear-gradient(135deg, #ffffff, #f0f0f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        position: relative;
        z-index: 2;
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        opacity: 0.95;
        animation: fadeInUp 1s ease-out 0.2s;
        animation-fill-mode: both;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        position: relative;
        z-index: 2;
    }

    /* Floating Shapes Animation */
    .floating-shape {
        position: absolute;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 50%;
        animation: float 6s ease-in-out infinite;
        z-index: 1;
    }
    
    .floating-shape:nth-child(1) {
        width: 120px;
        height: 120px;
        top: 10%;
        right: 10%;
        animation-delay: 0s;
    }
    
    .floating-shape:nth-child(2) {
        width: 80px;
        height: 80px;
        bottom: 20%;
        left: 15%;
        animation-delay: 2s;
    }
    
    .floating-shape:nth-child(3) {
        width: 60px;
        height: 60px;
        top: 60%;
        right: 20%;
        animation-delay: 4s;
    }

    /* Enhanced Progress Steps */
    .progress-container {
        display: flex;
        justify-content: space-between;
        margin: 3rem 0;
        position: relative;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .progress-step {
        flex: 1;
        text-align: center;
        position: relative;
        z-index: 2;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .progress-circle {
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 0.5rem;
        font-weight: bold;
        transition: all 0.3s ease;
        border: 2px solid rgba(255, 255, 255, 0.3);
        font-size: 1.2rem;
        color: white;
        position: relative;
        overflow: hidden;
    }
    
    .progress-step.active .progress-circle {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transform: scale(1.15);
        border: 2px solid rgba(255, 255, 255, 0.5);
        box-shadow: 
            0 0 30px rgba(102, 126, 234, 0.5),
            inset 0 0 20px rgba(255, 255, 255, 0.2);
    }
    
    .progress-step.completed .progress-circle {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        border: 2px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 0 20px rgba(40, 167, 69, 0.4);
    }
    
    .progress-step.clickable .progress-circle:hover {
        transform: scale(1.1);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        background: rgba(255, 255, 255, 0.2);
    }
    
    .progress-line {
        position: absolute;
        top: 35px;
        left: 10%;
        right: 10%;
        height: 4px;
        background: rgba(255, 255, 255, 0.2);
        z-index: 1;
        border-radius: 2px;
    }
    
    .progress-line-active {
        background: linear-gradient(90deg, 
            #28a745 0%, 
            #20c997 50%, 
            rgba(255, 255, 255, 0.2) 100%);
        box-shadow: 0 0 10px rgba(40, 167, 69, 0.5);
    }

    /* Enhanced Card Styles with Glass Morphism */
    .card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        transition: all 0.4s ease;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.1),
            inset 0 0 0 1px rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.1), 
            transparent);
        transition: left 0.6s ease;
    }
    
    .card:hover::before {
        left: 100%;
    }
    
    .card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.2),
            0 0 80px rgba(102, 126, 234, 0.3),
            inset 0 0 0 1px rgba(255, 255, 255, 0.2);
    }
    
    .card-header {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        color: white;
        display: flex;
        align-items: center;
        gap: 0.8rem;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    /* Enhanced Skill Tags with 3D Effect */
    .skill-tag {
        display: inline-block;
        padding: 0.6rem 1.2rem;
        margin: 0.4rem;
        border-radius: 25px;
        font-size: 0.95rem;
        font-weight: 600;
        transition: all 0.3s ease;
        cursor: pointer;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    .skill-tag::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.2), 
            transparent);
        transition: left 0.5s ease;
    }
    
    .skill-tag:hover::before {
        left: 100%;
    }
    
    .skill-tag:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 
            0 8px 20px rgba(0, 0, 0, 0.3),
            0 0 0 2px rgba(255, 255, 255, 0.1);
    }
    
    .skill-matched {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
    }
    
    .skill-partial {
        background: linear-gradient(135deg, #ffc107, #fd7e14);
        color: white;
        box-shadow: 0 4px 15px rgba(255, 193, 7, 0.3);
    }
    
    .skill-missing {
        background: linear-gradient(135deg, #dc3545, #e83e8c);
        color: white;
        box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
    }

    /* Enhanced Metric Cards with Neon Glow */
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        transition: all 0.4s ease;
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, 
            #667eea, #764ba2, #667eea, #764ba2);
        border-radius: 22px;
        z-index: -1;
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    
    .metric-card:hover::before {
        opacity: 1;
        animation: borderGlow 2s linear infinite;
    }
    
    .metric-card:hover {
        transform: translateY(-8px) scale(1.05);
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.3),
            0 0 60px rgba(102, 126, 234, 0.4);
    }
    
    .metric-value {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff, #e0e0e0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }
    
    .metric-label {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        margin-top: 0.8rem;
        font-weight: 600;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    }

    /* Enhanced Upload Area */
    .upload-area {
        border: 3px dashed rgba(102, 126, 234, 0.5);
        border-radius: 20px;
        padding: 3rem;
        text-align: center;
        background: rgba(255, 255, 255, 0.05);
        transition: all 0.4s ease;
        backdrop-filter: blur(10px);
        position: relative;
        overflow: hidden;
    }
    
    .upload-area::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, 
            rgba(102, 126, 234, 0.1), 
            rgba(118, 75, 162, 0.1));
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    
    .upload-area:hover::before {
        opacity: 1;
    }
    
    .upload-area:hover {
        border-color: rgba(102, 126, 234, 0.8);
        background: rgba(255, 255, 255, 0.1);
        box-shadow: 
            0 15px 30px rgba(0, 0, 0, 0.2),
            inset 0 0 0 2px rgba(102, 126, 234, 0.3);
        transform: translateY(-5px);
    }

    /* Enhanced Button Styles */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    
    .stButton button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.2), 
            transparent);
        transition: left 0.5s ease;
    }
    
    .stButton button:hover::before {
        left: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-3px);
        box-shadow: 
            0 8px 25px rgba(102, 126, 234, 0.4),
            0 0 0 2px rgba(255, 255, 255, 0.1);
    }
    
    .stButton button:active {
        transform: translateY(-1px);
    }

    /* Enhanced Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 0.8rem;
        gap: 0.5rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 12px;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.8);
        transition: all 0.3s ease;
        border: 1px solid transparent;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }

    /* New Animations */
    @keyframes shimmer {
        0% { transform: translateX(-100%) rotate(45deg); }
        100% { transform: translateX(100%) rotate(45deg); }
    }
    
    @keyframes borderGlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes float {
        0%, 100% { 
            transform: translateY(0px) rotate(0deg);
        }
        50% { 
            transform: translateY(-20px) rotate(180deg);
        }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0% { 
            box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7);
        }
        70% { 
            box-shadow: 0 0 0 20px rgba(102, 126, 234, 0);
        }
        100% { 
            box-shadow: 0 0 0 0 rgba(102, 126, 234, 0);
        }
    }

    /* Enhanced Sidebar */
    .css-1d391kg {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
    }
    
    .css-1d391kg .st-emotion-cache-16idsys p {
        color: white;
    }

    /* File Status Enhancements */
    .file-status {
        display: flex;
        align-items: center;
        padding: 1rem;
        margin: 0.8rem 0;
        border-radius: 15px;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .file-status:hover {
        transform: translateX(5px);
        background: rgba(255, 255, 255, 0.15);
    }
    
    .file-status.success {
        border-left: 6px solid #28a745;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.2);
    }
    
    .file-status.error {
        border-left: 6px solid #dc3545;
        box-shadow: 0 4px 15px rgba(220, 53, 69, 0.2);
    }
    
    .file-status-icon {
        margin-right: 1rem;
        font-size: 1.5rem;
        animation: bounce 2s infinite;
    }

    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {transform: translateY(0);}
        40% {transform: translateY(-10px);}
        60% {transform: translateY(-5px);}
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.5rem;
        }
        
        .hero-subtitle {
            font-size: 1.2rem;
        }
        
        .progress-step {
            font-size: 0.8rem;
        }
        
        .progress-circle {
            width: 50px;
            height: 50px;
            font-size: 1rem;
        }
        
        .metric-value {
            font-size: 2.2rem;
        }
        
        .card {
            padding: 1.5rem;
        }
    }

    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2, #667eea);
    }
        
    /* Enhanced ATS Score Container */
    .ats-score-container {
        text-align: center;
        padding: 3rem 2rem;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        border-radius: 25px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.2),
            inset 0 0 0 1px rgba(255, 255, 255, 0.1);
    }
    
    .ats-score-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, 
            transparent 0%, 
            rgba(255, 255, 255, 0.1) 50%, 
            transparent 100%);
        animation: shimmer 6s infinite linear;
        z-index: 1;
    }

    /* Enhanced ATS Score Circle with Animation */
    .ats-score-circle {
        width: 200px;
        height: 200px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 2rem;
        font-weight: bold;
        color: white;
        box-shadow: 
            0 0 50px rgba(102, 126, 234, 0.5),
            inset 0 0 20px rgba(255, 255, 255, 0.2);
        position: relative;
        z-index: 2;
        font-size: 3rem;
        font-weight: 800;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        border: 3px solid rgba(255, 255, 255, 0.3);
        animation: pulseScore 2s ease-in-out infinite;
        transition: all 0.4s ease;
    }
    
    .ats-score-circle::before {
        content: '';
        position: absolute;
        top: -10px;
        left: -10px;
        right: -10px;
        bottom: -10px;
        border-radius: 50%;
        background: conic-gradient(
            from 0deg,
            #667eea,
            #764ba2,
            #667eea
        );
        z-index: -1;
        animation: rotate 3s linear infinite;
        opacity: 0.7;
    }
    
    .ats-score-circle::after {
        content: '';
        position: absolute;
        top: 5px;
        left: 5px;
        right: 5px;
        bottom: 5px;
        border-radius: 50%;
        background: inherit;
        z-index: -1;
    }
    
    .ats-score-circle:hover {
        transform: scale(1.1) rotate(5deg);
        box-shadow: 
            0 0 80px rgba(102, 126, 234, 0.8),
            inset 0 0 30px rgba(255, 255, 255, 0.3);
    }

    /* ATS Score Categories with Enhanced Visuals */
    .ats-score-excellent {
        background: linear-gradient(135deg, #28a745, #20c997);
        animation: pulseExcellent 2s ease-in-out infinite !important;
    }
    
    .ats-score-good {
        background: linear-gradient(135deg, #17a2b8, #6f42c1);
        animation: pulseGood 2s ease-in-out infinite !important;
    }
    
    .ats-score-average {
        background: linear-gradient(135deg, #ffc107, #fd7e14);
        animation: pulseAverage 2s ease-in-out infinite !important;
    }
    
    .ats-score-poor {
        background: linear-gradient(135deg, #dc3545, #e83e8c);
        animation: pulsePoor 2s ease-in-out infinite !important;
    }

    /* Enhanced ATS Factor Cards */
    .ats-factor {
        margin: 1.5rem 0;
        padding: 1.5rem;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 15px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .ats-factor::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.1), 
            transparent);
        transition: left 0.5s ease;
    }
    
    .ats-factor:hover::before {
        left: 100%;
    }
    
    .ats-factor:hover {
        transform: translateX(10px);
        background: rgba(255, 255, 255, 0.12);
        box-shadow: 
            0 10px 25px rgba(0, 0, 0, 0.2),
            inset 0 0 0 1px rgba(255, 255, 255, 0.2);
    }
    
    .ats-factor-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .ats-factor-title {
        font-weight: 700;
        color: white;
        font-size: 1.1rem;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    }
    
    .ats-factor-score {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        color: white;
        font-size: 0.9rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .ats-factor-score:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
    
    .ats-factor-excellent {
        background: linear-gradient(135deg, #28a745, #20c997);
        animation: glowExcellent 3s ease-in-out infinite;
    }
    
    .ats-factor-good {
        background: linear-gradient(135deg, #17a2b8, #6f42c1);
        animation: glowGood 3s ease-in-out infinite;
    }
    
    .ats-factor-average {
        background: linear-gradient(135deg, #ffc107, #fd7e14);
        animation: glowAverage 3s ease-in-out infinite;
    }
    
    .ats-factor-poor {
        background: linear-gradient(135deg, #dc3545, #e83e8c);
        animation: glowPoor 3s ease-in-out infinite;
    }

    /* Progress Bar for ATS Factors */
    .ats-progress-container {
        width: 100%;
        height: 8px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        overflow: hidden;
        margin-top: 0.5rem;
    }
    
    .ats-progress-bar {
        height: 100%;
        border-radius: 10px;
        transition: width 1.5s ease-in-out;
        position: relative;
        overflow: hidden;
    }
    
    .ats-progress-bar::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.4), 
            transparent);
        animation: shimmer 2s infinite;
    }

    /* ATS Score Animations */
    @keyframes pulseScore {
        0%, 100% { 
            transform: scale(1);
            box-shadow: 
                0 0 50px rgba(102, 126, 234, 0.5),
                inset 0 0 20px rgba(255, 255, 255, 0.2);
        }
        50% { 
            transform: scale(1.05);
            box-shadow: 
                0 0 70px rgba(102, 126, 234, 0.8),
                inset 0 0 30px rgba(255, 255, 255, 0.3);
        }
    }
    
    @keyframes pulseExcellent {
        0%, 100% { 
            box-shadow: 
                0 0 50px rgba(40, 167, 69, 0.5),
                inset 0 0 20px rgba(255, 255, 255, 0.2);
        }
        50% { 
            box-shadow: 
                0 0 80px rgba(40, 167, 69, 0.8),
                inset 0 0 30px rgba(255, 255, 255, 0.3);
        }
    }
    
    @keyframes pulseGood {
        0%, 100% { 
            box-shadow: 
                0 0 50px rgba(23, 162, 184, 0.5),
                inset 0 0 20px rgba(255, 255, 255, 0.2);
        }
        50% { 
            box-shadow: 
                0 0 80px rgba(23, 162, 184, 0.8),
                inset 0 0 30px rgba(255, 255, 255, 0.3);
        }
    }
    
    @keyframes pulseAverage {
        0%, 100% { 
            box-shadow: 
                0 0 50px rgba(255, 193, 7, 0.5),
                inset 0 0 20px rgba(255, 255, 255, 0.2);
        }
        50% { 
            box-shadow: 
                0 0 80px rgba(255, 193, 7, 0.8),
                inset 0 0 30px rgba(255, 255, 255, 0.3);
        }
    }
    
    @keyframes pulsePoor {
        0%, 100% { 
            box-shadow: 
                0 0 50px rgba(220, 53, 69, 0.5),
                inset 0 0 20px rgba(255, 255, 255, 0.2);
        }
        50% { 
            box-shadow: 
                0 0 80px rgba(220, 53, 69, 0.8),
                inset 0 0 30px rgba(255, 255, 255, 0.3);
        }
    }
    
    @keyframes glowExcellent {
        0%, 100% { 
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.4);
        }
        50% { 
            box-shadow: 0 6px 25px rgba(40, 167, 69, 0.7);
        }
    }
    
    @keyframes glowGood {
        0%, 100% { 
            box-shadow: 0 4px 15px rgba(23, 162, 184, 0.4);
        }
        50% { 
            box-shadow: 0 6px 25px rgba(23, 162, 184, 0.7);
        }
    }
    
    @keyframes glowAverage {
        0%, 100% { 
            box-shadow: 0 4px 15px rgba(255, 193, 7, 0.4);
        }
        50% { 
            box-shadow: 0 6px 25px rgba(255, 193, 7, 0.7);
        }
    }
    
    @keyframes glowPoor {
        0%, 100% { 
            box-shadow: 0 4px 15px rgba(220, 53, 69, 0.4);
        }
        50% { 
            box-shadow: 0 6px 25px rgba(220, 53, 69, 0.7);
        }
    }
    
    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
             
    /* Enhanced High Priority Skill Gaps Section */
    .priority-gaps-container {
        background: linear-gradient(135deg, 
            rgba(220, 53, 69, 0.1) 0%, 
            rgba(220, 53, 69, 0.05) 100%);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        border: 1px solid rgba(220, 53, 69, 0.3);
        position: relative;
        overflow: hidden;
        box-shadow: 
            0 10px 30px rgba(220, 53, 69, 0.1),
            inset 0 0 0 1px rgba(255, 255, 255, 0.1);
    }

    .priority-gaps-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, 
            #dc3545, #e83e8c, #dc3545);
        animation: borderFlow 3s linear infinite;
    }

    .priority-gaps-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid rgba(220, 53, 69, 0.3);
    }

    .priority-gaps-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: white;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }

    .priority-gaps-count {
        background: linear-gradient(135deg, #dc3545, #e83e8c);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
        animation: pulse 2s infinite;
    }

    /* Enhanced Priority Gap Items */
    .priority-gap {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
        border-left: 6px solid;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 15px;
        transition: all 0.4s ease;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }

    .priority-gap::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.1), 
            transparent);
        transition: left 0.6s ease;
    }

    .priority-gap:hover::before {
        left: 100%;
    }

    .priority-gap:hover {
        transform: translateX(10px) scale(1.02);
        box-shadow: 
            0 8px 25px rgba(0, 0, 0, 0.2),
            0 0 30px rgba(220, 53, 69, 0.2);
    }

    /* Priority Level Specific Styles */
    .priority-gap.high {
        border-left-color: #dc3545;
        background: linear-gradient(135deg, 
            rgba(220, 53, 69, 0.15), 
            rgba(232, 62, 140, 0.1));
        animation: glowHigh 3s ease-in-out infinite;
    }

    .priority-gap.medium {
        border-left-color: #ffc107;
        background: linear-gradient(135deg, 
            rgba(255, 193, 7, 0.15), 
            rgba(253, 126, 20, 0.1));
        animation: glowMedium 3s ease-in-out infinite;
    }

    .priority-gap.low {
        border-left-color: #17a2b8;
        background: linear-gradient(135deg, 
            rgba(23, 162, 184, 0.15), 
            rgba(111, 66, 193, 0.1));
        animation: glowLow 3s ease-in-out infinite;
    }

    /* Priority Gap Content */
    .priority-gap-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.8rem;
    }

    .priority-gap-skill {
        font-size: 1.3rem;
        font-weight: 700;
        color: white;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .priority-gap-badge {
        padding: 0.4rem 1rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }

    .priority-gap.high .priority-gap-badge {
        background: linear-gradient(135deg, #dc3545, #e83e8c);
        color: white;
        animation: pulseRed 2s infinite;
    }

    .priority-gap.medium .priority-gap-badge {
        background: linear-gradient(135deg, #ffc107, #fd7e14);
        color: white;
        animation: pulseYellow 2s infinite;
    }

    .priority-gap.low .priority-gap-badge {
        background: linear-gradient(135deg, #17a2b8, #6f42c1);
        color: white;
        animation: pulseBlue 2s infinite;
    }

    .priority-gap-metrics {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }

    .priority-metric {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        font-size: 0.9rem;
    }

    .priority-metric-label {
        color: rgba(255, 255, 255, 0.8);
        font-weight: 500;
    }

    .priority-metric-value {
        color: white;
        font-weight: 700;
    }

    .priority-gap-action {
        background: rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 10px;
        border-left: 3px solid;
        margin-top: 0.8rem;
    }

    .priority-gap.high .priority-gap-action {
        border-left-color: #dc3545;
        background: linear-gradient(135deg, 
            rgba(220, 53, 69, 0.2), 
            rgba(232, 62, 140, 0.1));
    }

    .priority-gap.medium .priority-gap-action {
        border-left-color: #ffc107;
        background: linear-gradient(135deg, 
            rgba(255, 193, 7, 0.2), 
            rgba(253, 126, 20, 0.1));
    }

    .priority-gap.low .priority-gap-action {
        border-left-color: #17a2b8;
        background: linear-gradient(135deg, 
            rgba(23, 162, 184, 0.2), 
            rgba(111, 66, 193, 0.1));
    }

    .action-text {
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.95rem;
        line-height: 1.4;
        margin: 0;
    }

    /* Progress Bars for Skill Gaps */
    .skill-gap-progress {
        width: 100%;
        height: 8px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        overflow: hidden;
        margin: 0.5rem 0;
    }

    .skill-gap-progress-bar {
        height: 100%;
        border-radius: 10px;
        transition: width 1s ease-in-out;
        position: relative;
        overflow: hidden;
    }

    .priority-gap.high .skill-gap-progress-bar {
        background: linear-gradient(90deg, #dc3545, #e83e8c);
    }

    .priority-gap.medium .skill-gap-progress-bar {
        background: linear-gradient(90deg, #ffc107, #fd7e14);
    }

    .priority-gap.low .skill-gap-progress-bar {
        background: linear-gradient(90deg, #17a2b8, #6f42c1);
    }

    .skill-gap-progress-bar::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.4), 
            transparent);
        animation: shimmer 2s infinite;
    }

    /* Animations for Priority Gaps */
    @keyframes glowHigh {
        0%, 100% { 
            box-shadow: 0 4px 15px rgba(220, 53, 69, 0.2);
        }
        50% { 
            box-shadow: 0 6px 25px rgba(220, 53, 69, 0.4);
        }
    }

    @keyframes glowMedium {
        0%, 100% { 
            box-shadow: 0 4px 15px rgba(255, 193, 7, 0.2);
        }
        50% { 
            box-shadow: 0 6px 25px rgba(255, 193, 7, 0.4);
        }
    }

    @keyframes glowLow {
        0%, 100% { 
            box-shadow: 0 4px 15px rgba(23, 162, 184, 0.2);
        }
        50% { 
            box-shadow: 0 6px 25px rgba(23, 162, 184, 0.4);
        }
    }

    @keyframes pulseRed {
        0%, 100% { 
            transform: scale(1);
            box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
        }
        50% { 
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(220, 53, 69, 0.5);
        }
    }

    @keyframes pulseYellow {
        0%, 100% { 
            transform: scale(1);
            box-shadow: 0 2px 8px rgba(255, 193, 7, 0.3);
        }
        50% { 
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(255, 193, 7, 0.5);
        }
    }

    @keyframes pulseBlue {
        0%, 100% { 
            transform: scale(1);
            box-shadow: 0 2px 8px rgba(23, 162, 184, 0.3);
        }
        50% { 
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(23, 162, 184, 0.5);
        }
    }

    /* Skill Improvement Suggestions */
    .improvement-suggestions {
        margin-top: 2rem;
        padding: 1.5rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .suggestions-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: white;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .suggestion-item {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        transition: all 0.3s ease;
    }

    .suggestion-item:hover {
        background: rgba(255, 255, 255, 0.12);
        transform: translateX(5px);
    }

    .suggestion-icon {
        font-size: 1.5rem;
        flex-shrink: 0;
    }

    .suggestion-content {
        flex: 1;
    }

    .suggestion-title {
        font-weight: 600;
        color: white;
        margin-bottom: 0.3rem;
    }

    .suggestion-desc {
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.9rem;
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        .priority-gaps-header {
            flex-direction: column;
            gap: 1rem;
            align-items: flex-start;
        }
        
        .priority-gap-metrics {
            flex-direction: column;
            gap: 0.8rem;
        }
        
        .priority-gap-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.8rem;
        }
        
        .suggestion-item {
            flex-direction: column;
            align-items: flex-start;
            text-align: left;
        }
    }


    /* Enhanced ATS Tips Section */
    .ats-tips {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        border: 1px solid rgba(255, 255, 255, 0.15);
        position: relative;
        overflow: hidden;
    }
    
    .ats-tips::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, 
            #667eea, #764ba2, #667eea);
        animation: borderFlow 3s linear infinite;
    }
    
    .ats-tips-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: white;
        margin-bottom: 1.5rem;
        text-align: center;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .ats-tip {
        padding: 1rem;
        margin: 0.8rem 0;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
        color: rgba(255, 255, 255, 0.9);
    }
    
    .ats-tip:hover {
        background: rgba(255, 255, 255, 0.1);
        transform: translateX(5px);
        border-left: 4px solid #764ba2;
    }
    
    @keyframes borderFlow {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }

    /* ATS Score Rating Text */
    .ats-rating-text {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 1rem 0;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        animation: fadeInUp 1s ease-out;
    }
    
    .ats-rating-desc {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-bottom: 2rem;
        animation: fadeInUp 1s ease-out 0.2s;
        animation-fill-mode: both;
    }

    /* ATS Score Celebration Effects */
    .celebration-particle {
        position: absolute;
        width: 8px;
        height: 8px;
        background: gold;
        border-radius: 50%;
        animation: celebrate 2s ease-out forwards;
        z-index: 3;
    }
    
    @keyframes celebrate {
        0% {
            transform: translate(0, 0) scale(1);
            opacity: 1;
        }
        100% {
            transform: translate(var(--tx), var(--ty)) scale(0);
            opacity: 0;
        }
    }

    /* Responsive ATS Score */
    @media (max-width: 768px) {
        .ats-score-circle {
            width: 150px;
            height: 150px;
            font-size: 2.5rem;
        }
        
        .ats-factor-header {
            flex-direction: column;
            gap: 0.5rem;
            align-items: flex-start;
        }
        
        .ats-factor-score {
            align-self: flex-start;
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
# Enhanced Skill Extractor with Better Partial Matching
class EnhancedSkillExtractor:
    def __init__(self):
        # Expanded skill categories with variations and synonyms
        self.skill_categories = {
            'technical': [
                'Python', 'Java', 'JavaScript', 'JS', 'TypeScript', 'TS', 'SQL', 'NoSQL',
                'Machine Learning', 'ML', 'Deep Learning', 'DL', 'AI', 'Artificial Intelligence',
                'TensorFlow', 'TF', 'PyTorch', 'Keras', 'Scikit-learn', 'sklearn',
                'React', 'React.js', 'Angular', 'Vue', 'Node.js', 'Express.js',
                'Docker', 'Kubernetes', 'K8s', 'AWS', 'Amazon Web Services', 'Azure', 'GCP', 'Google Cloud',
                'Git', 'GitHub', 'GitLab', 'CI/CD', 'Continuous Integration', 'Continuous Deployment',
                'Microservices', 'REST API', 'GraphQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'Redis',
                'Elasticsearch', 'Kafka', 'Apache Kafka', 'Spark', 'Apache Spark', 'Hadoop',
                'Data Science', 'Data Analysis', 'Big Data', 'Computer Vision', 'NLP', 'Natural Language Processing',
                'C++', 'C#', 'Swift', 'Kotlin', 'Go', 'Golang', 'Rust', 'PHP', 'Ruby', 'Rails', 'Ruby on Rails',
                'Spring', 'Spring Boot', 'Django', 'Flask', 'FastAPI', 'Laravel'
            ],
            'soft': [
                'Communication', 'Verbal Communication', 'Written Communication',
                'Leadership', 'Team Leadership', 'Team Management',
                'Teamwork', 'Collaboration', 'Cross-functional Collaboration',
                'Problem Solving', 'Problem-solving', 'Critical Thinking', 'Analytical Thinking',
                'Creativity', 'Innovation', 'Adaptability', 'Flexibility',
                'Time Management', 'Project Management', 'Agile', 'Scrum', 'Kanban',
                'Collaboration', 'Team Collaboration', 'Analytical Skills', 'Decision Making',
                'Negotiation', 'Conflict Resolution', 'Emotional Intelligence', 'EQ',
                'Presentation Skills', 'Public Speaking', 'Mentoring', 'Coaching',
                'Strategic Planning', 'Business Acumen', 'Customer Service'
            ],
            'tools': [
                'Jira', 'Confluence', 'Slack', 'Microsoft Teams', 'Trello', 'Asana',
                'Figma', 'Sketch', 'Adobe XD', 'VS Code', 'Visual Studio Code', 'IntelliJ', 'Eclipse',
                'PyCharm', 'WebStorm', 'Postman', 'Docker Desktop', 'Kubernetes Dashboard',
                'Grafana', 'Prometheus', 'Jenkins', 'GitLab CI', 'GitHub Actions',
                'Tableau', 'Power BI', 'Excel', 'Microsoft Excel', 'Google Sheets',
                'Linux', 'Unix', 'Windows', 'macOS', 'Bash', 'Shell', 'Zsh'
            ],
            'certifications': [
                'AWS Certified', 'AWS Solutions Architect', 'Azure Certified', 'Google Cloud Certified',
                'PMP', 'Project Management Professional', 'Scrum Master', 'CSM', 'PSM',
                'CISSP', 'CompTIA', 'Security+', 'Network+', 'Cisco Certified', 'CCNA', 'CCNP',
                'Oracle Certified', 'OCA', 'OCP', 'Microsoft Certified', 'MCSA', 'MCSE',
                'Salesforce Certified', 'Administrator', 'Developer',
                'Kubernetes Certified', 'CKAD', 'CKA', 'CKS'
            ]
        }
        
        # Build comprehensive skill lookup with variations
        self.skill_lookup = {}
        self.skill_variations = {}
        
        for category, skills in self.skill_categories.items():
            for skill in skills:
                key = skill.lower()
                self.skill_lookup[key] = category
                
                # Create variations mapping
                if ' ' in skill:
                    # For multi-word skills, also check for acronyms and abbreviations
                    words = skill.split()
                    if len(words) > 1:
                        acronym = ''.join(word[0] for word in words if word[0].isupper())
                        if len(acronym) > 1:
                            self.skill_variations[acronym.lower()] = key
                
                # Handle common variations
                variations = self._generate_variations(skill)
                for variation in variations:
                    self.skill_variations[variation] = key
    
    def _generate_variations(self, skill):
        """Generate common variations of a skill"""
        variations = []
        skill_lower = skill.lower()
        
        # Common substitutions and variations
        variations_map = {
            '.js': 'js',
            '.net': 'net',
            '++': 'pp',
            '#': 'sharp',
            ' ': '-',
            ' ': '_',
            ' and ': ' & ',
            'aws ': 'amazon web services ',
            'gcp ': 'google cloud platform ',
            'ml ': 'machine learning ',
            'ai ': 'artificial intelligence ',
            'nlp ': 'natural language processing '
        }
        
        # Generate variations
        variations.append(skill_lower)
        variations.append(skill_lower.replace(' ', ''))
        
        for old, new in variations_map.items():
            if old in skill_lower:
                variations.append(skill_lower.replace(old, new))
                variations.append(skill_lower.replace(old, ''))
        
        return list(set(variations))
    
    def extract_skills(self, text, model_type='spaCy', confidence_threshold=0.6):
        """Enhanced skill extraction with better partial matching"""
        text_lower = text.lower()
        extracted_skills = []
        found_skills = set()
        
        # Normalize text for better matching
        normalized_text = self._normalize_text(text_lower)
        
        # Extract skills using multiple strategies
        strategies = [
            self._exact_match,
            self._variation_match,
            self._contextual_match,
            self._acronym_match
        ]
        
        for strategy in strategies:
            skills_found = strategy(normalized_text, text_lower)
            for skill_data in skills_found:
                skill_key = skill_data['name'].lower()
                if skill_key not in found_skills and skill_data['confidence'] >= confidence_threshold:
                    extracted_skills.append(skill_data)
                    found_skills.add(skill_key)
        
        # Sort by confidence and remove duplicates
        extracted_skills.sort(key=lambda x: x['confidence'], reverse=True)
        
        return extracted_skills
    
    def _exact_match(self, normalized_text, original_text):
        """Exact matching of skills"""
        skills_found = []
        
        for skill, category in self.skill_lookup.items():
            if skill in normalized_text:
                # Calculate confidence based on context and frequency
                confidence = self._calculate_confidence(skill, normalized_text, 'exact')
                occurrences = normalized_text.count(skill)
                
                skills_found.append({
                    'name': self._format_skill_name(skill),
                    'category': category,
                    'confidence': confidence,
                    'occurrences': occurrences,
                    'sentences': self._find_sentences(skill, original_text),
                    'match_type': 'exact'
                })
        
        return skills_found
    
    def _variation_match(self, normalized_text, original_text):
        """Match skills with variations"""
        skills_found = []
        
        for variation, original_skill in self.skill_variations.items():
            if variation in normalized_text and len(variation) > 2:
                category = self.skill_lookup.get(original_skill, 'technical')
                confidence = self._calculate_confidence(variation, normalized_text, 'variation')
                occurrences = normalized_text.count(variation)
                
                skills_found.append({
                    'name': self._format_skill_name(original_skill),
                    'category': category,
                    'confidence': confidence * 0.9,  # Slightly lower confidence for variations
                    'occurrences': occurrences,
                    'sentences': self._find_sentences(variation, original_text),
                    'match_type': 'variation'
                })
        
        return skills_found
    
    def _contextual_match(self, normalized_text, original_text):
        """Context-based matching for partial skills"""
        skills_found = []
        words = normalized_text.split()
        
        for i, word in enumerate(words):
            # Check for partial matches in technical terms
            if len(word) >= 3:  # Only consider words with 3+ characters
                for skill, category in self.skill_lookup.items():
                    if self._is_partial_match(word, skill):
                        confidence = self._calculate_contextual_confidence(word, skill, normalized_text, i, words)
                        if confidence >= 0.3:  # Lower threshold for partial matches
                            skills_found.append({
                                'name': self._format_skill_name(skill),
                                'category': category,
                                'confidence': confidence,
                                'occurrences': 1,
                                'sentences': self._find_context_sentence(i, words, original_text),
                                'match_type': 'contextual'
                            })
        
        return skills_found
    
    def _acronym_match(self, normalized_text, original_text):
        """Match acronyms and abbreviations"""
        skills_found = []
        
        # Common acronym patterns
        acronym_patterns = [
            r'\b[a-z]{2,5}\b',  # 2-5 letter acronyms
        ]
        
        import re
        for pattern in acronym_patterns:
            for match in re.finditer(pattern, normalized_text):
                acronym = match.group()
                if acronym in self.skill_variations:
                    original_skill = self.skill_variations[acronym]
                    category = self.skill_lookup.get(original_skill, 'technical')
                    
                    skills_found.append({
                        'name': self._format_skill_name(original_skill),
                        'category': category,
                        'confidence': 0.7,  # Medium confidence for acronyms
                        'occurrences': 1,
                        'sentences': self._find_sentences(acronym, original_text),
                        'match_type': 'acronym'
                    })
        
        return skills_found
    
    def _is_partial_match(self, word, skill):
        """Check if a word is a partial match for a skill"""
        skill_words = skill.split()
        
        # Single word skill
        if len(skill_words) == 1:
            skill_word = skill_words[0]
            return (word in skill_word or skill_word in word) and len(word) >= 3
        
        # Multi-word skill - check if word matches any part
        for skill_word in skill_words:
            if word == skill_word or (len(word) >= 3 and word in skill_word):
                return True
        
        return False
    
    def _calculate_confidence(self, skill, text, match_type):
        """Calculate confidence score based on multiple factors"""
        base_confidence = 0.5
        
        # Frequency bonus
        occurrences = text.count(skill)
        frequency_bonus = min(0.3, occurrences * 0.1)
        
        # Context bonus
        context_bonus = 0.0
        if any(section in text for section in ['skills', 'experience', 'projects', 'technical']):
            context_bonus += 0.2
        if any(section in text for section in ['education', 'certification', 'training']):
            context_bonus += 0.1
        
        # Match type bonus
        type_bonus = {
            'exact': 0.2,
            'variation': 0.1,
            'contextual': 0.0,
            'acronym': 0.1
        }.get(match_type, 0.0)
        
        # Length penalty for very short matches
        length_penalty = 0.0
        if len(skill) < 3:
            length_penalty = -0.2
        
        confidence = base_confidence + frequency_bonus + context_bonus + type_bonus + length_penalty
        
        return min(1.0, max(0.1, confidence))
    
    def _calculate_contextual_confidence(self, word, skill, text, position, words):
        """Calculate confidence for contextual/partial matches"""
        base_confidence = 0.3
        
        # Check surrounding words for technical context
        context_window = words[max(0, position-3):min(len(words), position+4)]
        context_text = ' '.join(context_window)
        
        # Boost confidence if surrounded by technical terms
        technical_indicators = ['development', 'programming', 'coding', 'software', 'engineering',
                               'framework', 'library', 'technology', 'tool', 'platform']
        
        context_bonus = 0.0
        for indicator in technical_indicators:
            if indicator in context_text:
                context_bonus += 0.05
        
        # Proximity to known skills
        proximity_bonus = 0.0
        for i in range(max(0, position-5), min(len(words), position+6)):
            if words[i] in self.skill_lookup:
                proximity_bonus += 0.02
        
        return min(0.8, base_confidence + context_bonus + proximity_bonus)
    
    def _normalize_text(self, text):
        """Normalize text for better matching"""
        import re
        
        # Remove special characters but keep important symbols
        text = re.sub(r'[^\w\s&+#\-]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Common normalizations
        replacements = {
            'nodejs': 'node.js',
            'reactjs': 'react.js',
            'angularjs': 'angular.js',
            'vuejs': 'vue.js',
            'aws ': 'amazon web services ',
            'gcp ': 'google cloud platform ',
            'azure ': 'microsoft azure ',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text.strip().lower()
    
    def _format_skill_name(self, skill):
        """Format skill name consistently"""
        # Capitalize first letter of each word for multi-word skills
        if ' ' in skill:
            return ' '.join(word.capitalize() for word in skill.split())
        else:
            return skill.capitalize()
    
    def _find_sentences(self, skill, text):
        """Find sentences containing the skill"""
        import re
        sentences = re.split(r'[.!?]+', text)
        skill_sentences = []
        
        for sentence in sentences:
            if skill.lower() in sentence.lower():
                clean_sentence = sentence.strip()
                if clean_sentence:
                    skill_sentences.append(clean_sentence)
        
        return skill_sentences[:3]
    
    def _find_context_sentence(self, word_index, words, original_text):
        """Find context sentence for partial matches"""
        start = max(0, word_index - 5)
        end = min(len(words), word_index + 6)
        context_words = words[start:end]
        
        # Reconstruct the original case from the context
        original_words = original_text.split()
        if len(original_words) >= end:
            original_context = original_words[start:end]
            return [' '.join(original_context)]
        
        return [' '.join(context_words)]

# Enhanced gap analysis with better partial matching
class EnhancedGapAnalyzer:
    def __init__(self):
        self.similarity_threshold = 0.6
    
    def analyze_skills_similarity(self, resume_skills, jd_skills):
        """Enhanced similarity analysis with better partial matching"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        # Extract skill names
        resume_skill_names = [skill['name'] if isinstance(skill, dict) else skill for skill in resume_skills]
        jd_skill_names = [skill['name'] if isinstance(skill, dict) else skill for skill in jd_skills]
        
        # Create combined skill list for vectorization
        all_skills = resume_skill_names + jd_skill_names
        
        # Use TF-IDF for semantic similarity
        vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))
        try:
            skill_vectors = vectorizer.fit_transform(all_skills)
            similarity_matrix = cosine_similarity(skill_vectors[:len(resume_skill_names)], 
                                                skill_vectors[len(resume_skill_names):])
        except:
            # Fallback to simple string matching
            return self._fallback_similarity(resume_skill_names, jd_skill_names)
        
        # Analyze matches
        matched_skills = []
        partial_matches = []
        missing_skills = []
        
        for j, jd_skill in enumerate(jd_skill_names):
            best_match_index = -1
            best_similarity = 0
            
            for i, resume_skill in enumerate(resume_skill_names):
                similarity = similarity_matrix[i][j]
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_index = i
            
            if best_similarity >= 0.9:
                matched_skills.append({
                    'jd_skill': jd_skill,
                    'resume_skill': resume_skill_names[best_match_index],
                    'similarity': best_similarity,
                    'match_type': 'exact'
                })
            elif best_similarity >= self.similarity_threshold:
                partial_matches.append({
                    'jd_skill': jd_skill,
                    'resume_skill': resume_skill_names[best_match_index],
                    'similarity': best_similarity,
                    'match_type': 'partial'
                })
            else:
                missing_skills.append({
                    'jd_skill': jd_skill,
                    'similarity': best_similarity,
                    'match_type': 'missing'
                })
        
        return {
            'matched_skills': matched_skills,
            'partial_matches': partial_matches,
            'missing_skills': missing_skills,
            'similarity_matrix': similarity_matrix,
            'overall_score': self._calculate_overall_score(matched_skills, partial_matches, jd_skills)
        }
    
    def _fallback_similarity(self, resume_skills, jd_skills):
        """Fallback similarity calculation using string matching"""
        from difflib import SequenceMatcher
        
        matched_skills = []
        partial_matches = []
        missing_skills = []
        
        for jd_skill in jd_skills:
            best_match = None
            best_similarity = 0
            
            for resume_skill in resume_skills:
                similarity = SequenceMatcher(None, jd_skill.lower(), resume_skill.lower()).ratio()
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = resume_skill
            
            if best_similarity >= 0.9:
                matched_skills.append({
                    'jd_skill': jd_skill,
                    'resume_skill': best_match,
                    'similarity': best_similarity,
                    'match_type': 'exact'
                })
            elif best_similarity >= self.similarity_threshold:
                partial_matches.append({
                    'jd_skill': jd_skill,
                    'resume_skill': best_match,
                    'similarity': best_similarity,
                    'match_type': 'partial'
                })
            else:
                missing_skills.append({
                    'jd_skill': jd_skill,
                    'similarity': best_similarity,
                    'match_type': 'missing'
                })
        
        return {
            'matched_skills': matched_skills,
            'partial_matches': partial_matches,
            'missing_skills': missing_skills,
            'similarity_matrix': None,
            'overall_score': self._calculate_overall_score(matched_skills, partial_matches, jd_skills)
        }
    
    def _calculate_overall_score(self, matched_skills, partial_matches, jd_skills):
        """Calculate overall match score"""
        if not jd_skills:
            return 0
        
        exact_match_score = len(matched_skills) * 1.0
        partial_match_score = len(partial_matches) * 0.5
        
        total_score = (exact_match_score + partial_match_score) / len(jd_skills)
        return min(1.0, total_score) * 100

# Update the main analyzer class
class AISkillGapAnalyzer:
    def __init__(self):
        self.logger = self._setup_logger()
        
        # Initialize enhanced components
        self.file_reader = EnhancedFileReader()
        self.skill_extractor = EnhancedSkillExtractor()
        self.gap_analyzer = EnhancedGapAnalyzer()
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
        
        # Initialize ATS Score Checker
        self.ats_checker = ATSScoreChecker()
    
    def analyze_gap(self, resume_skills, jd_skills):
        """Enhanced gap analysis with better partial matching"""
        # Use enhanced gap analyzer for better results
        result = self.gap_analyzer.analyze_skills_similarity(resume_skills, jd_skills)
        
        # Add priority gaps
        result['priority_gaps'] = self._generate_priority_gaps(
            result['missing_skills'], 
            [skill['name'] if isinstance(skill, dict) else skill for skill in jd_skills]
        )
        
        return result

# Enhanced debugging function
def debug_skill_extraction():
    """Debug function to test skill extraction"""
    test_text = """
    I have experience with Python, JavaScript, and React.js. 
    Worked on machine learning projects using TensorFlow and scikit-learn.
    Familiar with AWS services including EC2 and S3. 
    Used Docker and Kubernetes for containerization.
    """
    
    extractor = EnhancedSkillExtractor()
    skills = extractor.extract_skills(test_text, 'spaCy', 0.3)
    
    print("Extracted Skills:")
    for skill in skills:
        print(f"- {skill['name']} ({skill['category']}) - Confidence: {skill['confidence']:.2f} - Type: {skill['match_type']}")


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
        with st.spinner("🎯 Analyzing your resume for ATS compatibility..."):
            ats_result = analyzer.ats_checker.calculate_ats_score(
                st.session_state.cleaned_resume,
                st.session_state.cleaned_jd,
                st.session_state.resume_skills,
                st.session_state.jd_skills
            )
            st.session_state.ats_score = ats_result['overall_score']
            st.session_state.ats_analysis = ats_result
    
    # Display overall ATS score with enhanced visuals
    score = st.session_state.ats_score
    score_percentage = int(score * 100)
    score_category = st.session_state.ats_analysis['score_category']
    
    # Determine score color and text
    if score_category == 'excellent':
        score_class = 'ats-score-excellent'
        score_text = '🎉 Excellent!'
        score_desc = 'Your resume is highly optimized for ATS systems'
        emoji = "🚀"
    elif score_category == 'good':
        score_class = 'ats-score-good'
        score_text = '👍 Good Job!'
        score_desc = 'Your resume is well-optimized for ATS systems'
        emoji = "⭐"
    elif score_category == 'average':
        score_class = 'ats-score-average'
        score_text = '💡 Needs Improvement'
        score_desc = 'Your resume has some ATS optimization issues'
        emoji = "📝"
    else:
        score_class = 'ats-score-poor'
        score_text = '⚠️ Requires Attention'
        score_desc = 'Your resume needs significant ATS optimization'
        emoji = "🔧"
    
    # Display enhanced score circle
    st.markdown(f"""
    <div class="ats-score-container">
        <div class="ats-score-circle {score_class}">
            {score_percentage}%
        </div>
        <h3 class="ats-rating-text">{emoji} {score_text}</h3>
        <p class="ats-rating-desc">{score_desc}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display factor scores with progress bars
    st.subheader("📊 ATS Optimization Factors")
    
    factor_scores = st.session_state.ats_analysis['factor_scores']
    
    for factor_name, factor_data in factor_scores.items():
        factor_score = factor_data['score']
        factor_percentage = int(factor_score * 100)
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
        
        # Display factor with progress bar
        st.markdown(f"""
        <div class="ats-factor">
            <div class="ats-factor-header">
                <div class="ats-factor-title">{factor_name.replace('_', ' ').title()}</div>
                <div class="ats-factor-score {factor_class}">{factor_percentage}%</div>
            </div>
            <div class="ats-progress-container">
                <div class="ats-progress-bar {factor_class}" style="width: {factor_percentage}%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display recommendations
        if factor_data['recommendations']:
            with st.expander(f"💡 Recommendations for {factor_name.replace('_', ' ').title()}"):
                for rec in factor_data['recommendations']:
                    st.write(f"• {rec}")
    
    # Display missing keywords with enhanced styling
    if st.session_state.ats_analysis['missing_keywords']:
        st.markdown("---")
        st.subheader("🔍 Missing Keywords")
        st.markdown("Consider adding these keywords from the job description to your resume:")
        
        missing_keywords = st.session_state.ats_analysis['missing_keywords']
        keyword_html = "<div style='margin: 1rem 0;'>"
        for keyword in missing_keywords[:8]:  # Limit to 8 keywords for better display
            keyword_html += f'<span class="skill-tag skill-missing" style="margin: 0.3rem; animation: glowPoor 3s ease-in-out infinite;">{keyword}</span>'
        keyword_html += "</div>"
        st.markdown(keyword_html, unsafe_allow_html=True)
    
    # Display formatting issues
    if st.session_state.ats_analysis['formatting_issues']:
        st.markdown("---")
        st.subheader("⚙️ Formatting Issues")
        for issue in st.session_state.ats_analysis['formatting_issues']:
            st.markdown(f'<div class="ats-tip">⚠️ {issue}</div>', unsafe_allow_html=True)
    
    # Enhanced ATS optimization tips
    st.markdown("---")
    st.markdown("""
    <div class="ats-tips">
        <div class="ats-tips-title">💎 Pro ATS Optimization Tips</div>
    </div>
    """, unsafe_allow_html=True)
    
    tips = [
        "✨ Use Standard Formatting: Avoid tables, columns, and special characters that ATS systems can't parse",
        "🎯 Include Keywords: Mirror the language and keywords from the job description",
        "📝 Use Standard Section Headers: Use common section titles like 'Experience', 'Education', 'Skills'",
        "📊 Quantify Achievements: Use numbers and metrics to demonstrate your impact",
        "🎨 Keep It Clean: Use a simple, single-column layout with standard fonts",
        "🚫 Avoid Headers/Footers: ATS systems may not read content in headers or footers",
        "• Use Standard Bullets: Stick to standard bullet points instead of special characters",
        "📄 Save as Text-Based PDF: Ensure your PDF is text-based, not image-based"
    ]
    
    for tip in tips:
        st.markdown(f'<div class="ats-tip">{tip}</div>', unsafe_allow_html=True)
    
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