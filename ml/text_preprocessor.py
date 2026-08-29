"""
Text Preprocessor Module
Handles text normalization, cleaning, lemmatization, and tokenization for NLP.
"""

import re
import logging
from typing import List, Optional, Set

import spacy
from spacy.lang.en.stop_words import STOP_WORDS

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """Preprocess text for NLP tasks: cleaning, tokenization, lemmatization, stop-word removal."""

    def __init__(self, model_name: str = 'en_core_web_sm'):
        """
        Initialize the preprocessor with a spaCy model.

        Args:
            model_name: Name of the spaCy model to load
        """
        try:
            self.nlp = spacy.load(model_name, disable=['ner', 'parser'])  # Disable unused components for speed
            logger.info(f"Loaded spaCy model: {model_name}")
        except OSError:
            logger.warning(f"Model {model_name} not found, trying to download...")
            import subprocess
            import sys
            subprocess.check_call([sys.executable, '-m', 'spacy', 'download', model_name])
            self.nlp = spacy.load(model_name, disable=['ner', 'parser'])

        # Custom stop words - keep some that might be relevant for skills
        self.stop_words = set(STOP_WORDS)
        # Remove some technical stop words that could be relevant
        keep_words = {'in', 'on', 'at', 'by', 'for', 'with', 'from', 'to', 'of', 'and', 'or', 'not', 'as', 'is', 'be'}
        # Actually, let's keep the default stop words but we'll handle skill extraction differently

    def preprocess(self, text: str, remove_stopwords: bool = True, lemmatize: bool = True,
                   lowercase: bool = True, min_token_length: int = 2) -> str:
        """
        Full preprocessing pipeline.

        Args:
            text: Raw text to preprocess
            remove_stopwords: Whether to remove stop words
            lemmatize: Whether to lemmatize tokens
            lowercase: Whether to convert to lowercase
            min_token_length: Minimum token length to keep

        Returns:
            Preprocessed text as string
        """
        if not text or not text.strip():
            return ""

        doc = self.nlp(text)

        tokens = []
        for token in doc:
            # Skip punctuation, spaces, numbers-only
            if token.is_punct or token.is_space or token.like_num:
                continue

            # Get the token text
            token_text = token.lemma_ if lemmatize else token.text

            if lowercase:
                token_text = token_text.lower()

            # Filter by length
            if len(token_text) < min_token_length:
                continue

            # Remove stop words if requested
            if remove_stopwords and token_text in self.stop_words:
                continue

            # Keep only alphabetic tokens (with some exceptions for technical terms)
            if not self._is_valid_token(token_text):
                continue

            tokens.append(token_text)

        return ' '.join(tokens)

    def _is_valid_token(self, token: str) -> bool:
        """Check if token is valid (alphabetic or contains valid technical patterns)."""
        # Allow alphabetic tokens
        if token.isalpha():
            return True

        # Allow tokens with hyphens (e.g., machine-learning, full-stack)
        if '-' in token and all(part.isalpha() for part in token.split('-')):
            return True

        # Allow tokens with dots (e.g., node.js, c++, a.i.)
        if '.' in token:
            parts = token.split('.')
            if all(part.isalpha() or part == '' for part in parts):
                return True

        # Allow tokens with plus (e.g., c++, c#)
        if '+' in token:
            parts = token.split('+')
            if all(part.isalpha() for part in parts):
                return True

        # Allow tokens with # (e.g., c#, f#)
        if '#' in token:
            parts = token.split('#')
            if all(part.isalpha() for part in parts):
                return True

        return False

    def tokenize(self, text: str, remove_stopwords: bool = True,
                 lemmatize: bool = True, lowercase: bool = True) -> List[str]:
        """
        Tokenize text into list of tokens.

        Args:
            text: Raw text to tokenize
            remove_stopwords: Whether to remove stop words
            lemmatize: Whether to lemmatize tokens
            lowercase: Whether to convert to lowercase

        Returns:
            List of tokens
        """
        processed = self.preprocess(text, remove_stopwords, lemmatize, lowercase)
        return processed.split()

    def extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        doc = self.nlp(text)
        return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    def extract_noun_phrases(self, text: str) -> List[str]:
        """Extract noun phrases from text (useful for skill extraction)."""
        doc = self.nlp(text)
        return [chunk.text.strip().lower() for chunk in doc.noun_chunks if len(chunk.text.strip()) > 2]

    def extract_entities(self, text: str) -> List[tuple]:
        """Extract named entities from text."""
        # Need NER enabled for this
        nlp_ner = spacy.load('en_core_web_sm', disable=['parser'])
        doc = nlp_ner(text)
        return [(ent.text, ent.label_) for ent in doc.ents]

    def clean_for_tfidf(self, text: str) -> str:
        """
        Clean text specifically for TF-IDF vectorization.
        Keeps more tokens than general preprocessing but removes stop words.
        """
        if not text or not text.strip():
            return ""

        doc = self.nlp(text)

        tokens = []
        for token in doc:
            # Keep more tokens for TF-IDF
            if token.is_punct or token.is_space:
                continue

            token_text = token.lemma_.lower()

            # Keep tokens with minimum length 2
            if len(token_text) < 2:
                continue

            # Skip stop words
            if token_text in self.stop_words:
                continue

            # Keep alphanumeric and technical tokens
            if not re.match(r'^[a-zA-Z0-9\-\+\#\.]+$', token_text):
                continue

            tokens.append(token_text)

        return ' '.join(tokens)

    def extract_keywords(self, text: str, top_n: int = 50) -> List[str]:
        """
        Extract key terms from text using frequency and noun phrases.

        Args:
            text: Input text
            top_n: Number of top keywords to return

        Returns:
            List of keywords
        """
        # Get noun phrases
        noun_phrases = self.extract_noun_phrases(text)

        # Get individual tokens
        tokens = self.tokenize(text, remove_stopwords=True, lemmatize=True)

        # Combine and count frequencies
        from collections import Counter
        all_terms = noun_phrases + tokens
        freq = Counter(all_terms)

        # Filter out very common terms
        keywords = [term for term, count in freq.most_common(top_n)
                    if count > 1 or len(term.split()) > 1]  # Keep phrases or repeated terms

        return keywords


def get_preprocessor(model_name: str = 'en_core_web_sm') -> TextPreprocessor:
    """Get a singleton TextPreprocessor instance."""
    if not hasattr(get_preprocessor, '_instance'):
        get_preprocessor._instance = TextPreprocessor(model_name)
    return get_preprocessor._instance