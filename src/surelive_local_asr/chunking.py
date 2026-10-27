"""Bounded PCM reads and timestamp ownership at long-media chunk boundaries."""
import math, re

RATE = 16000
CHUNK_SECONDS = 300
CONTEXT_SECONDS = 1

def windows(sample_count, chunk_seconds=CHUNK_SECONDS):
    step = int(chunk_seconds * RATE)
    if step <= 0: raise ValueError('Invalid chunk size')
    for start in range(0, sample_count, step):
        end = min(sample_count, start + step)
        yield start, end, max(0, start - RATE * CONTEXT_SECONDS), min(sample_count, end + RATE * CONTEXT_SECONDS)

def owned_words(words, offset, begin, end, duration):
    result = []
    for word in words:
        start, stop = word.start + offset, word.end + offset
        if not math.isfinite(start) or not math.isfinite(stop) or stop < start: continue
        center = (start + stop) / 2
        if center < begin or center >= end: continue
        start, stop = max(0., start), min(duration, stop)
        if stop <= start: continue
        result.append({'word':word.word, 'start':start, 'end':stop})
    return result

def append_chunk(rows, words):
    # Only remove an identical, acoustically overlapping boundary token. Preserve repetitions at distinct times.
    if rows and words and rows[-1]['words']:
        previous = rows[-1]['words'][-1]
        normalized = lambda value: re.sub(r'\W+', '', value.casefold())
        while words and normalized(words[0]['word']) and normalized(words[0]['word']) == normalized(previous['word']) and words[0]['start'] < previous['end'] and abs(words[0]['start'] - previous['start']) < .5:
            words.pop(0)
    if words: rows.append({'words':words})
