#!/usr/bin/env python3
"""
Test script for theme-based boosting in RAG systems.
Demonstrates how theme detection can improve retrieval for narrative content.
"""
import sys
from pprint import pprint
from app.services.theme_tagging import tag_themes, analyze_query, simulate_theme_boost

# Test queries that previously had issues
SAMPLE_QUERIES = [
    "Was Holmes a witness at a wedding?",
    "Tell me about Holmes being a witness at a wedding",
    "What happened when Holmes was at the church?",
    "Describe the scene where Holmes is at St. Monica",
    "Was there a wedding in the story?",
    "What role did Holmes play at the wedding?",
]

# Passages that contain the relevant information
SAMPLE_PASSAGES = [
    "Holmes was always averse to recognizing women, but he was particularly obstinate in this case.",
    "The King of Bohemia needed Holmes's help with a compromising photograph.",
    "I had seen little of Holmes lately. My marriage had drifted us away from each other.",
    "On March 4th, we were both in a cab, heading to the Church of St. Monica in the Edgeware Road.",
    "Holmes had been engaged as a witness at the wedding of Miss Mary Sutherland.",
    "The ceremony at St. Monica was brief, with Holmes standing witness as the bride and groom exchanged vows.",
    "The King feared that Irene Adler would use the photograph to compromise him before his marriage.",
    "After the wedding at St. Monica, Holmes remarked that being a witness had given him unique insights.",
]

def display_theme_analysis(query):
    """Display theme analysis for a query"""
    print(f"\n{'='*80}")
    print(f"QUERY: {query}")
    print(f"{'='*80}")

    themes, elements = analyze_query(query)
    print(f"DETECTED THEMES: {', '.join(themes.keys()) if themes else 'None'}")
    print(f"NARRATIVE ELEMENTS: {', '.join(elements) if elements else 'None'}")

    if themes:
        print("\nTHEME DETAILS:")
        for theme, keywords in themes.items():
            print(f"  - {theme}: {', '.join(keywords)}")

def test_theme_boosting():
    """Test theme-based boosting on sample queries and passages"""
    # Analyze each query
    for query in SAMPLE_QUERIES:
        display_theme_analysis(query)

    # Test boosting on key passages
    print("\n\n" + "="*80)
    print("BOOST SIMULATION FOR KEY QUERY")
    print("="*80)

    # Use the most specific query about the wedding witness
    key_query = "Tell me about Holmes being a witness at a wedding"
    print(f"QUERY: {key_query}")

    # Sort passages by boost score
    passage_scores = []
    for i, passage in enumerate(SAMPLE_PASSAGES):
        boost = simulate_theme_boost(key_query, passage)
        passage_scores.append((boost, i, passage))

    # Sort by boost in descending order
    passage_scores.sort(reverse=True)

    # Display passages with boost values
    print("\nPASSAGES RANKED BY THEME BOOSTING:")
    for boost, i, passage in passage_scores:
        print(f"\nPassage #{i+1} - Boost: {boost:.2f} ({boost*100:.0f}%)")
        print(f"  \"{passage}\"")

        # Show why this passage got boosted
        if boost > 0:
            themes = tag_themes(passage)
            elements = [elem for elem in ["witness", "wedding", "church", "ceremony", "bride"]
                        if elem in passage.lower()]
            if themes:
                print(f"  Themes: {', '.join(themes.keys())}")
            if elements:
                print(f"  Narrative elements: {', '.join(elements)}")

def main():
    """Main function"""
    print("THEME-BASED BOOSTING DEMO")
    print("========================")
    test_theme_boosting()

if __name__ == "__main__":
    main()