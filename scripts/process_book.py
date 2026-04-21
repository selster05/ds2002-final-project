#!/usr/bin/env python3
"""
Process a text file: tokenize, lemmatize with NLTK WordNetLemmatizer,
count unique words, and write word counts to an output file.
Usage: python process_text.py <input.txt> <output_file>
"""

import re
import sys
from collections import Counter

import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet

# Ensure NLTK data is available
nltk.download("wordnet", quiet=True)
nltk.download("omw-1.4", quiet=True)
nltk.download("averaged_perceptron_tagger_eng", quiet=True)


def parse_args():
    if len(sys.argv) != 3:
        print("Usage: python process_text.py <input.txt> <output_file>", file=sys.stderr)
        sys.exit(1)
    return sys.argv[1], sys.argv[2]


def tokenize(text):
    """
    Extract tokens (words) from text.
    Tokens are the minimal units we count: here, each contiguous sequence of
    letters is one token. We lowercase so "The" and "the" are the same token.
    """
    text = text.lower()
    return re.findall(r"\b[a-z]+\b", text)


def _penn_to_wn(tag):
    """Map Penn Treebank tag to WordNet POS (n/v/a/r). Default to noun."""
    if tag.startswith("N"):
        return wordnet.NOUN
    if tag.startswith("V"):
        return wordnet.VERB
    if tag.startswith("J"):
        return wordnet.ADJ
    if tag.startswith("R"):
        return wordnet.ADV
    return wordnet.NOUN


def lemmatize_words(words, lemmatizer):
    """
    Lemmatize each token to its dictionary form (lemma).
    Lemmatization reduces inflected forms to a single base form using a
    lexicon and grammar (e.g. "running" -> "run", "whispered" -> "whisper").
    We use POS tagging so verb forms are reduced correctly (WordNetLemmatizer
    needs the part of speech: e.g. "whispering" as verb -> "whisper").
    """
    # pos_tag returns (word, Penn_tag); we need WordNet pos for the lemmatizer
    tagged = nltk.pos_tag(words)
    return [lemmatizer.lemmatize(w, pos=_penn_to_wn(tag)) for w, tag in tagged]


def process_file(input_path, output_path):
    with open(input_path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    # Tokens: individual words from the text (e.g. "running", "runs", "run" are 3 tokens).
    words = tokenize(text)
    lemmatizer = WordNetLemmatizer()
    # Lemmas: base forms of those words (e.g. "run" for all three), so we count unique concepts.
    lemmas = lemmatize_words(words, lemmatizer)
    counts = Counter(lemmas)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("word,count\n")
        for word, count in sorted(counts.items()):
            f.write(f"{word},{count}\n")
    return len(words), len(counts)


def main():
    input_path, output_path = parse_args()
    total_tokens, unique_words = process_file(input_path, output_path)
    print(f"Total tokens (words): {total_tokens}, unique words (lemmatized): {unique_words}")
    print(f"Wrote word counts to {output_path}")


if __name__ == "__main__":
    main()