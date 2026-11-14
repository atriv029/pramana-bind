import pytest

from pramana_bind.schema import (Avayava, Defeater, Fact, Hetu, Locus, Polarity,
                                 Pratijna, Quote, Resolution, Source, Udaharana, Verdict)
from pramana_bind.score import pbs
from pramana_bind.verdict import derive_full, derive_ow
from pramana_bind.world import build_world, counts

P, A = Polarity.present, Polarity.absent


_n = iter(range(10**6))


def fact(prop, pol=P, located=True, **kw):
    return Fact(prop=prop, polarity=pol, quote=f"q{next(_n)}", located=located, **kw)


def av(upanaya=fact("H"), loci=(), mention=None):
    return Avayava(
        pratijna=Pratijna(paksa="x", sadhya="y", paksa_mention=mention),
        hetu=Hetu(text="h"),
        udaharana=Udaharana(loci=[Locus(id=i, facts=fs) for i, fs in loci]),
        upanaya=upanaya,
    )


def defeater(rank, located=True, valid=True):
    return Defeater(quote=Quote(quote="d", source_id="D", located=located),
                    authority_rank=rank, inference_valid=valid)


SAPAKSA = ("L1", [fact("H"), fact("S")])
VIPAKSA = ("L2", [fact("H"), fact("S", A)])


def run(a, defeaters=(), source=None):
    return derive_full(build_world(a, defeaters, source))


def test_r0_unresolved_beats_everything():
    src = Source(resolution=Resolution.not_located)
    assert run(av(upanaya=None), source=src)[:2] == (Verdict.unresolved, "R0")
    src = Source(resolution=Resolution.ambiguous)
    assert run(av(loci=[SAPAKSA]), source=src)[0] is Verdict.unresolved


def test_r1_asraya():
    v, rule, sub = run(av(upanaya=fact("H", located=False), loci=[SAPAKSA]))
    assert (v, rule, sub.value) == (Verdict.asiddha, "R1", "asraya")


def test_r2_svarupa_when_only_mention_located():
    mention = Quote(quote="x", located=True)
    v, rule, sub = run(av(upanaya=fact("H", located=False), loci=[SAPAKSA], mention=mention))
    assert (v, rule, sub.value) == (Verdict.asiddha, "R2", "svarupa")


def test_r2_source_denies_hetu_of_paksa():
    assert run(av(upanaya=fact("H", A), loci=[SAPAKSA]))[1] == "R2"


def test_r2b_bhaga():
    v, rule, sub = run(av(upanaya=fact("H", scope="part"), loci=[SAPAKSA]))
    assert (v, rule, sub.value) == (Verdict.asiddha, "R2b", "bhaga")


def test_r3_badhita_needs_higher_rank_and_located_quote():
    a = av(loci=[SAPAKSA])
    assert run(a, [defeater(2)], Source(authority_rank=1))[:2] == (Verdict.badhita, "R3")
    assert run(a, [defeater(2, located=False)], Source(authority_rank=1))[0] is Verdict.valid
    assert run(a, [defeater(0)], Source(authority_rank=1))[0] is Verdict.valid


def test_r3_outranks_r5():
    a = av(loci=[SAPAKSA, VIPAKSA])
    assert run(a, [defeater(5)])[1] == "R3"


def test_r4_viruddha_inverted_holding():
    a = av(loci=[("p", [fact("S", A)])])
    assert run(a)[:2] == (Verdict.viruddha, "R4")
    assert run(av(loci=[VIPAKSA]))[1] == "R4"


def test_r5_savyabhicara():
    assert run(av(loci=[SAPAKSA, VIPAKSA]))[:2] == (Verdict.savyabhicara, "R5")


def test_silence_is_not_deviation():
    # H at L3, source silent on S there: open world keeps this valid
    a = av(loci=[SAPAKSA, ("L3", [fact("H")])])
    assert run(a)[0] is Verdict.valid


def test_r6_satpratipaksa():
    a = av(loci=[SAPAKSA])
    assert run(a, [defeater(0)])[:2] == (Verdict.satpratipaksa, "R6")
    assert run(a, [defeater(0, valid=False)])[0] is Verdict.valid


def test_r5_before_r6():
    assert run(av(loci=[SAPAKSA, VIPAKSA]), [defeater(0)])[1] == "R5"


def test_r7_uncorroborated_and_r8_valid():
    assert run(av())[:2] == (Verdict.uncorroborated, "R7")
    assert run(av(loci=[("p", [fact("S")])]))[1] == "R7"  # p itself is not sapaksa
    assert run(av(loci=[SAPAKSA]))[:2] == (Verdict.valid, "R8")


def test_unlocated_facts_do_not_enter_world():
    a = av(loci=[SAPAKSA, ("L2", [fact("H"), fact("S", A, located=False)])])
    w = build_world(a)
    assert counts(w)["n_minus"] == 0
    assert derive_ow(w) == (Verdict.valid, "R8")


def test_conflicting_cell_is_unknown_and_reported():
    a = av(loci=[SAPAKSA, ("L2", [fact("H"), fact("S"), fact("S", A)])])
    w = build_world(a)
    assert ("L2", "S") in w.conflicts
    assert counts(w) == {"n_plus": 1, "n_minus": 0, "known": 1}


def test_pbs_matches_blueprint_example():
    w = build_world(av(loci=[SAPAKSA, VIPAKSA]))
    v, _ = derive_ow(w)
    s = pbs(w, v)
    assert s == pytest.approx({"G": 1.0, "V": 0.2, "D": 1.0, "value": 0.2})


def test_pbs_g_and_d():
    a = av(loci=[SAPAKSA, ("L2", [fact("H"), fact("S", located=False)])])
    w = build_world(a, [defeater(0)])
    s = pbs(w, derive_ow(w)[0])
    assert s["G"] == pytest.approx(4 / 5)
    assert s["D"] == 0.5
    w = build_world(av(loci=[SAPAKSA]), [defeater(9)])
    assert pbs(w, derive_ow(w)[0])["value"] == 0.0
    w = build_world(av(upanaya=fact("H", located=False)))
    assert pbs(w, Verdict.asiddha)["G"] == 0.0
