"""FIXTURES ONLY. Canned extractor replies for unit tests. Nothing in this file
is model output and none of it may appear in empirical results."""
import json

SRC = ("Whoever commits theft shall be punished with imprisonment of either description for a term which may "
       "extend to three years. Theft in a dwelling house shall be punished with imprisonment which may extend "
       "to seven years. A child under seven years of age commits no offence.")
CLAIM = "Everyone who commits theft is punished with up to three years."

DIRECT = {"polarity": "present", "scope": "full", "quantifier": "all", "modality": "certain",
          "quote": "Whoever commits theft shall be punished with imprisonment of either description for a term "
                   "which may extend to three years"}
REPLY = {
    "pratijna": {"paksa": "anyone who commits theft", "sadhya": "punished with up to three years",
                 "quantifier": "all", "modality": "certain", "paksa_quote": "Whoever commits theft"},
    "direct": [DIRECT], "conditions": [],
    "hetu": "commits theft", "upanaya": {"polarity": "present", "scope": "full", "quote": "Whoever commits theft"},
    "loci": [{"id": "L1", "label": "theft in a dwelling", "facts": [
        {"prop": "H", "polarity": "present", "quote": "Theft in a dwelling house"},
        {"prop": "S", "polarity": "absent", "quote": "may extend to seven years"},
        {"prop": "S", "polarity": "absent", "quote": "this quote is not in the source"}]}],
}
PLAIN = {**REPLY, "loci": []}  # the direct statement only


def canned(reply):
    """An ask_fn that returns a fixed reply (FIXTURE, not a model)."""
    return lambda prompt: "Here you go:\n" + json.dumps(reply)


def reply(paksa="p", sadhya="s", q="all", m="certain", direct=(), conditions=(), loci=(), upanaya=None,
          paksa_quote=None, hetu=None):
    return {"pratijna": {"paksa": paksa, "sadhya": sadhya, "quantifier": q, "modality": m, "paksa_quote": paksa_quote},
            "direct": list(direct), "conditions": list(conditions), "hetu": hetu, "upanaya": upanaya,
            "loci": list(loci)}


def d(quote, polarity="present", scope="full", q="all", m="certain"):
    return {"polarity": polarity, "scope": scope, "quantifier": q, "modality": m, "quote": quote}
