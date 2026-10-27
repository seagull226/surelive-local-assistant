import unittest
from types import SimpleNamespace as Word
from chunking import RATE, windows, owned_words, append_chunk

class ChunkingTests(unittest.TestCase):
    def test_two_hour_reads_are_bounded_and_cover_tail(self):
        chunks=list(windows(7500*RATE))
        self.assertEqual(len(chunks),25)
        self.assertEqual(chunks[-1][1],7500*RATE)
        self.assertTrue(all(d-c<=302*RATE for a,b,c,d in chunks))
        self.assertTrue(all(a[1]==b[0] for a,b in zip(chunks,chunks[1:])))

    def test_context_ownership_and_global_offsets(self):
        words=[Word(word=' before',start=.2,end=.4),Word(word=' boundary',start=.8,end=1.2),Word(word=' after',start=1.5,end=2)]
        result=owned_words(words,299,300,600,7500)
        self.assertEqual([w['word'] for w in result],[' boundary',' after'])
        self.assertEqual(result[0]['start'],299.8)
        previous=owned_words([Word(word=' boundary',start=299.8,end=300.2)],0,0,300,7500)
        self.assertEqual(previous,[])

    def test_overlap_duplicate_but_preserve_spoken_repetition(self):
        rows=[{'words':[{'word':'yes,','start':299.8,'end':300.2}]}]
        append_chunk(rows,[{'word':' Yes','start':299.9,'end':300.3},{'word':'yes','start':300.4,'end':300.6}])
        self.assertEqual(len([w for r in rows for w in r['words']]),2)

    def test_invalid_words_and_duration(self):
        words=[Word(word='bad',start=float('nan'),end=2),Word(word='reverse',start=3,end=2),Word(word='tail',start=9.5,end=10.1)]
        self.assertEqual(owned_words(words,0,0,10,10),[{'word':'tail','start':9.5,'end':10}])
        self.assertEqual(list(windows(0)),[])
        with self.assertRaises(ValueError): list(windows(10,0))

if __name__=='__main__': unittest.main()
