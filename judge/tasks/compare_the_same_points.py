from difflib import SequenceMatcher


def calculate_similarity(source1, source2):
    sm = SequenceMatcher(None, source1, source2)
    similarity = sm.ratio() * 100
    return round(similarity, 2)
