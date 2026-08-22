

def test_doctor_reports_gated_weight_access(monkeypatch):
    """The 15 GB of TRELLIS weights download fine and every model loads before
    the GATED image tower fails with a 403 - minutes in, after the expensive
    part. Doctor answers it up front instead."""
    from voxkiln import engine

    class Gated(Exception):
        pass

    Gated.__name__ = "GatedRepoError"

    def refuse(repo, filename):
        raise Gated("403 Client Error")

    monkeypatch.setattr("huggingface_hub.hf_hub_download", refuse)
    check = engine._gated_weight_check()
    assert check["accessible"] is False
    assert check["reason"] == "GatedRepoError"
    assert "huggingface.co/facebook/dinov3" in check["fix"]
    assert "gated" in check["fix"]


def test_doctor_reports_gated_weights_available(monkeypatch):
    from voxkiln import engine

    monkeypatch.setattr("huggingface_hub.hf_hub_download", lambda repo, filename: "/tmp/x")
    assert engine._gated_weight_check()["accessible"] is True
