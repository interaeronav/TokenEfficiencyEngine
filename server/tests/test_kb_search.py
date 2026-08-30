# -- A45: SI-B10 REOPENED, with three live misfires from a real session -----


def test_document_meta_words_are_not_identity_evidence():
    """'Which GNU licence and which version is this file?' hit a careers file
    through the single word `file`. Corpus frequency does not save you here -
    `file` is in 1.2% of identity fields, rare AND meaningless."""
    from tee.kb.search import identity_hits

    rec = {
        "id": "gxgd.portfolio",
        "title": "Portfolio and breaking in — the practical career file",
        "tags": [],
    }
    q = "Which GNU licence and which version is this file? Quote the title line."
    assert identity_hits(q, rec) == [], "meta words must not attest relevance"


def test_repeating_a_word_does_not_promote_it_out_of_the_judged_band():
    """One distinct word is one piece of evidence. Saying 'licence' twice used
    to score 2 and skip the rerank judge entirely."""
    from tee.kb.search import identity_hits

    rec = {
        "id": "envasset.libraries",
        "title": "Asset libraries and sources — a licence-stated register",
        "tags": [],
    }
    q = "What licence is Orthanc released under? State the exact licence name and version."
    assert identity_hits(q, rec) == ["licence"], "duplicates must not inflate the band"


def test_in_domain_questions_still_score_strongly():
    """The floor must not have been raised onto real questions."""
    from tee.kb.search import identity_hits

    paving = {
        "id": "05-block-paving",
        "title": "Concrete block paving — bedding and jointing sand",
        "tags": ["paving"],
    }
    hits = identity_hits("what bedding sand spec applies to concrete block paving", paving)
    assert len(hits) >= 3, hits
