from __future__ import annotations

from services.nlu.datasets import align_bio_tags
from services.nlu.labels import BIO_LABEL_TO_ID


def test_align_bio_tags_masks_special_and_continuation_tokens():
    word_ids = [None, 0, 0, 1, None]
    tags = ["B-PRODUCT", "B-VERSION"]

    aligned = align_bio_tags(word_ids, tags, BIO_LABEL_TO_ID)

    assert aligned == [
        -100,
        BIO_LABEL_TO_ID["B-PRODUCT"],
        -100,
        BIO_LABEL_TO_ID["B-VERSION"],
        -100,
    ]
