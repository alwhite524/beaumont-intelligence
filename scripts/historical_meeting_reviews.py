"""Load reviewed historical meeting batches for the agenda and center builders."""
import json
from pathlib import Path


def load_reviews():
    result = {}
    for path in sorted((Path(__file__).resolve().parents[1] / 'data/council').glob('*-meeting-review.json')):
        batch = json.loads(path.read_text(encoding='utf-8'))
        if result.keys() & batch.keys():
            raise ValueError(f'Duplicate meeting review in {path.name}')
        result.update(batch)
    return result
