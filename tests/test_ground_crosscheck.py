import random

from pravrudhi.application.nyaya_gold import _worlds
from pravrudhi.application.nyaya_validity import derive_verdict

from pramana_bind.crosscheck import _name, closed_to_world3, crosscheck_closed
from pramana_bind.ground import ground
from pramana_bind.schema import Avayava, Fact, Hetu, Locus, Pratijna, Udaharana
from pramana_bind.verdict import derive_ow
from pramana_bind.world import build_world

T = "Section 5 applies to minors. It does not apply to adults. Minors are exempt.  Adults   pay in full."


def test_ground_sets_system_offsets_and_keeps_refusals():
    av = Avayava(
        pratijna=Pratijna(paksa="minors", sadhya="exempt"),
        hetu=Hetu(text="section 5"),
        upanaya=Fact(prop="H", polarity="present", quote="Section 5 applies to minors", start=999, end=1000),
        udaharana=Udaharana(loci=[Locus(id="L1", facts=[
            Fact(prop="S", polarity="present", quote="Adults pay in full"),      # whitespace-collapsed
            Fact(prop="H", polarity="present", quote="applies to seniors"),      # not in text
            Fact(prop="H", polarity="present", quote="apply"),                   # occurs once
            Fact(prop="H", polarity="present", quote="inors"),                   # occurs twice -> ambiguous
        ])]),
    )
    g, reasons = ground(av, {"T": T})
    assert (g.upanaya.start, g.upanaya.end, g.upanaya.offsets_source) == (0, 27, "system")
    f = g.udaharana.loci[0].facts
    assert f[0].located and T[f[0].start:f[0].end].split() == ["Adults", "pay", "in", "full"]
    assert not f[1].located and reasons["udaharana.L1.1"] == "quote_not_found"
    assert f[2].located
    assert not f[3].located and reasons["udaharana.L1.3"] == "ambiguous_quote"
    assert av.upanaya.start == 999  # input untouched
    w = build_world(g)
    assert w.weight_total == 5 and w.weight_located == 3


def test_gold_set_crosscheck_full_agreement():
    r = crosscheck_closed(per_class=100)
    assert r["n"] == 600
    assert r["derive_verdict"]["agree"] == 600
    assert r["gold_label"]["agree"] == 600
    assert r["disagreements"] == []


def test_exhaustive_agreement_on_random_closed_worlds():
    props = ["smoke", "fire", "water", "earth", "motion", "sound", "heat", "vapour"]
    n = 0
    for world in _worlds(random.Random(7), 300):
        for paksa in list(world) + ["nowhere"]:
            for s in props:
                for h in props:  # includes h == s (self-pervasion)
                    mine = _name(derive_ow(closed_to_world3(world, paksa, (h, s)), sadhya=s, hetu=h)[0])
                    assert mine == derive_verdict(world, paksa, s, h), (world, paksa, s, h)
                    n += 1
    assert n > 50000
