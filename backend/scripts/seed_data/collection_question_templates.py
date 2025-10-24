"""
Question templates for collection_question_rules seeding.

Aggregates baseline questions from asset-type-specific modules.
"""

from .application_questions import APPLICATION_QUESTIONS
from .database_questions import DATABASE_QUESTIONS
from .network_questions import NETWORK_QUESTIONS
from .server_questions import SERVER_QUESTIONS
from .storage_questions import STORAGE_QUESTIONS

QUESTION_TEMPLATES = {
    "Application": APPLICATION_QUESTIONS,
    "Server": SERVER_QUESTIONS,
    "Database": DATABASE_QUESTIONS,
    "Network": NETWORK_QUESTIONS,
    "Storage": STORAGE_QUESTIONS,
}
