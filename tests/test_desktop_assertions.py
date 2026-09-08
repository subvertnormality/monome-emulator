import math,unittest
from desktop_assertions import continuity,exits

class DesktopAssertions(unittest.TestCase):
    def test_clean_sine_and_short_dropouts(self):
        rate=44100;clean=[round(.2*32768*math.sin(2*math.pi*440*i/rate))/32768 for i in range(rate)]
        continuity(clean,rate,440)
        for offset in (rate//2,rate-40):
            damaged=clean.copy();damaged[offset:offset+25]=[0]*25
            with self.assertRaises(AssertionError):continuity(damaged,rate,440)
    def test_unrelated_crashes_and_missing_service_rejected(self):
        rows=[dict(service=n,returncode=2 if n=='desktop-audio' else 0) for n in ('desktop-audio','matron','sclang','crone','jack')]
        exits(rows,2)
        for index in range(1,len(rows)):
            bad=[r.copy() for r in rows];bad[index]['returncode']=-11
            with self.assertRaises(AssertionError):exits(bad,2)
        with self.assertRaises(AssertionError):exits(rows[:-1],2)
if __name__=='__main__':unittest.main()
