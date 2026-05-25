from data.dataset.labels import INTENTS
from data.dataset.models import DatasetSample, TokenAnnotation
from data.dataset.pipeline import DatasetValidator
from data.dataset.settings import MAX_SAMPLE_COUNT


def test_validator_accepts_configured_maximum_dataset_size() -> None:
    samples = [_sample(index) for index in range(MAX_SAMPLE_COUNT)]

    report = DatasetValidator().validate(
        {
            "train": samples[:700],
            "validation": samples[700:850],
            "test": samples[850:],
        }
    )

    assert report.is_valid


def test_validator_rejects_dataset_size_above_configured_maximum() -> None:
    samples = [_sample(index) for index in range(MAX_SAMPLE_COUNT + 1)]

    report = DatasetValidator().validate(
        {
            "train": samples[:701],
            "validation": samples[701:851],
            "test": samples[851:],
        }
    )

    assert not report.is_valid
    assert any("100-1000 samples" in error for error in report.errors)


def _sample(index: int) -> DatasetSample:
    text = f"Sample query {index}"
    # Rotate intents so large validation fixtures keep project intent coverage.
    intent = INTENTS[index % len(INTENTS)]
    return DatasetSample(
        text=text,
        intent=intent,
        entities=[],
        tokens=[TokenAnnotation(token=text, tag="O", start=0, end=len(text))],
    )
