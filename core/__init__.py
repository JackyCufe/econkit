"""EconKit 核心模块"""
from .data_loader import load_dataframe, detect_panel_structure, validate_panel_data, preprocess_data, generate_sample_data
from .smart_recommender import recommend_methods, get_method_categories
from .report_generator import generate_pdf_report

__all__ = [
    "load_dataframe",
    "detect_panel_structure",
    "validate_panel_data",
    "preprocess_data",
    "generate_sample_data",
    "recommend_methods",
    "get_method_categories",
    "generate_pdf_report",
]
