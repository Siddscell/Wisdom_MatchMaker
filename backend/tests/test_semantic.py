import numpy as np
import pytest

pytestmark = pytest.mark.slow


def test_ms_pipe_ranks_mild_steel_tube_first():
    from app.services.embedding import embed

    query = np.array(embed("MS pipe"))

    def similarity(text):
        return float(query @ np.array(embed(text)))

    tube = similarity("mild steel tube")
    assert tube > similarity("steel sheet")
    assert tube > similarity("cotton fabric")
