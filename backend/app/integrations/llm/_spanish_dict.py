"""Spanish-to-English occupational vocabulary for resume polish.

Extracted from spanish_polish.py to keep that module under the file-size
warning threshold.
"""

from __future__ import annotations

# Curated Spanish -> English occupational dict.  Keys are lowercase
# Spanish phrases; values are English equivalents the scorer's
# INDUSTRY_KEYWORDS / TITLE_FAMILY taxonomies recognize.
SPANISH_ENGLISH: dict[str, str] = {
    # Healthcare
    "enfermería": "nursing",
    "enfermera": "nurse",
    "enfermero": "nurse",
    "asistente de enfermería": "certified nursing assistant",
    "auxiliar de enfermería": "certified nursing assistant",
    "cna certificado": "certified nursing assistant",
    "técnico médico": "medical technician",
    "ayudante médico": "medical assistant",
    # Logistics / warehouse
    "montacargas": "forklift",
    "operador de montacargas": "forklift operator",
    "almacén": "warehouse",
    "almacenista": "warehouse worker",
    "bodega": "warehouse",
    "embalaje": "packing",
    "envío": "shipping",
    "recepción": "receiving",
    # Construction / trades
    "soldadura": "welding",
    "soldador": "welder",
    "carpintería": "carpentry",
    "carpintero": "carpenter",
    "albañil": "mason",
    "plomero": "plumber",
    "electricista": "electrician",
    "construcción": "construction",
    "obrero de construcción": "construction worker",
    # Customer service / clerical
    "servicio al cliente": "customer service",
    "atención al cliente": "customer service",
    "asistente administrativo": "administrative assistant",
    "secretaria": "secretary",
    "recepcionista": "receptionist",
    "cajera": "cashier",
    "cajero": "cashier",
    # Hospitality / food
    "cocinero": "cook",
    "ayudante de cocina": "kitchen helper",
    "lavaplatos": "dishwasher",
    "mesero": "server",
    "mesera": "server",
    "limpieza": "cleaning",
    "personal de limpieza": "cleaning staff",
    # Common verbs in resumes
    "experiencia": "experience",
    "años": "years",
    "trabajé": "worked",
    "trabajo": "work",
    "responsabilidades": "responsibilities",
    "habilidades": "skills",
    "certificación": "certification",
    "certificado": "certified",
    "licencia": "license",
    "diploma": "diploma",
    "secundaria": "high school",
    "preparatoria": "high school",
    "universidad": "university",
}

SPANISH_STOPWORDS: frozenset[str] = frozenset({
    "de", "la", "el", "y", "en", "los", "las", "un", "una", "del",
    "con", "por", "para", "que", "se", "su", "es", "al", "lo", "como",
})
