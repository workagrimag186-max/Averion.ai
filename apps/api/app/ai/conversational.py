"""
Conversational Intent Detection and Response Generation

Handles small talk, greetings, and casual conversation separately from RAG queries.
"""

import re
from typing import Tuple


# Conversational patterns for intent detection
GREETING_PATTERNS = [
    r'\b(hi|hello|hey|greetings|good\s+(morning|afternoon|evening|day))\b',
]

WELLBEING_PATTERNS = [
    r'\bhow\s+(are|r)\s+you\b',
    r'\bhow\s+is\s+it\s+going\b',
    r'\bhow.*day\b',
    r'\bhow.*doing\b',
]

CAPABILITY_PATTERNS = [
    r'\bwhat\s+can\s+you\s+do\b',
    r'\bwhat\s+are\s+you\s+capable\s+of\b',
    r'\bwhat\s+do\s+you\s+do\b',
    r'\bhelp\s+me\b',
    r'\bwhat\s+are\s+your\s+(features|capabilities)\b',
]

GRATITUDE_PATTERNS = [
    r'\b(thank\s+you|thanks|thx|ty|appreciate\s+it)\b',
]

FAREWELL_PATTERNS = [
    r'\b(bye|goodbye|see\s+you|farewell|take\s+care)\b',
]

INTRODUCTION_PATTERNS = [
    r'\bnice\s+to\s+meet\s+you\b',
    r'\bpleasure\s+to\s+meet\s+you\b',
    r'\bglad\s+to\s+meet\s+you\b',
]

IDENTITY_PATTERNS = [
    r'\bwho\s+are\s+you\b',
    r'\bwhat\s+are\s+you\b',
    r'\byour\s+name\b',
]


def is_conversational_query(query: str) -> Tuple[bool, str]:
    """
    Detect if a query is conversational/small-talk rather than a document question.
    
    Args:
        query: User's input text
        
    Returns:
        Tuple of (is_conversational, intent_type)
        intent_type can be: 'greeting', 'wellbeing', 'capability', 'gratitude', 
                           'farewell', 'introduction', 'identity', or 'unknown'
    """
    if not query or not query.strip():
        return False, 'unknown'
    
    query_lower = query.lower().strip()
    
    # Check for greetings
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return True, 'greeting'
    
    # Check for wellbeing questions
    for pattern in WELLBEING_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return True, 'wellbeing'
    
    # Check for capability questions
    for pattern in CAPABILITY_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return True, 'capability'
    
    # Check for gratitude
    for pattern in GRATITUDE_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return True, 'gratitude'
    
    # Check for farewells
    for pattern in FAREWELL_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return True, 'farewell'
    
    # Check for introductions
    for pattern in INTRODUCTION_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return True, 'introduction'
    
    # Check for identity questions
    for pattern in IDENTITY_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return True, 'identity'
    
    return False, 'unknown'


def generate_conversational_response(intent_type: str, query: str = "") -> str:
    """
    Generate a natural, friendly response for conversational queries.
    
    Args:
        intent_type: Type of conversational intent
        query: Original user query (optional, for context)
        
    Returns:
        Friendly, human-like response string
    """
    responses = {
        'greeting': [
            "Hello! I'm here to help you find information from your documents. What would you like to know?",
            "Hi there! I can answer questions based on your uploaded documents. How can I assist you today?",
            "Hey! Ready to help you explore your documents. What can I do for you?",
        ],
        'wellbeing': [
            "I'm doing well and ready to help! What would you like to work on today?",
            "I'm here and ready to assist you with your documents. What can I help you find?",
            "I don't experience days like humans do, but I'm functioning perfectly and eager to help! What questions do you have?",
        ],
        'capability': [
            "I can help you find information from your uploaded documents! Just ask me questions, and I'll search through your files to provide accurate answers with citations. You can upload PDFs, Word documents, and text files.",
            "I'm designed to answer questions based on your document library. Upload your files, ask questions, and I'll retrieve relevant information with source citations. I can handle various document formats including PDFs and DOCX files.",
            "Great question! I can search through your uploaded documents to answer questions, provide summaries, and cite sources. Think of me as your personal document assistant. What would you like to explore?",
        ],
        'gratitude': [
            "You're welcome! Let me know if you need anything else.",
            "Happy to help! Feel free to ask more questions anytime.",
            "My pleasure! I'm here whenever you need assistance with your documents.",
        ],
        'farewell': [
            "Goodbye! Come back anytime you need help with your documents.",
            "Take care! I'll be here when you return.",
            "See you later! Feel free to return whenever you have questions.",
        ],
        'introduction': [
            "Nice to meet you too! I'm excited to help you explore your documents. What would you like to know?",
            "The pleasure is mine! I'm here to make finding information in your documents easy. How can I assist you?",
            "Great to meet you! Let's get started—what questions do you have about your documents?",
        ],
        'identity': [
            "I'm an AI assistant designed to help you find information in your documents. I use advanced search technology to answer your questions with accurate citations from your uploaded files.",
            "I'm your document assistant! I can search through your uploaded files, answer questions, and provide source citations. Think of me as your personal research helper.",
            "I'm an AI-powered document assistant. My job is to help you quickly find information from your document library and provide accurate, cited answers to your questions.",
        ],
    }
    
    # Get response list for the intent type
    response_list = responses.get(intent_type, [
        "I'm here to help you with your documents. What would you like to know?"
    ])
    
    # For now, return the first response (can be randomized later)
    return response_list[0]


# Made with Bob