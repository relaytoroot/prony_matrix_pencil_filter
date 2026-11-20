"""Die Browserdaten müssen dieselbe Zerlegung wie die dargestellten Kurven zeigen."""

import numpy as np
import pytest

from prony_filter.labor_analysis import analyze
from prony_filter.labor_catalog import catalog


@pytest.mark.parametrize(("ziel", "restfrequenz"), [(2.2, 5.0), (5.0, 2.24)])
def test_zielfrequenz_tauscht_den_entfernten_signalanteil(ziel, restfrequenz):
    result = analyze(dict(f1=2.24, f2=5, a1=10, a2=2, d1=0.5, d2=0.2, order=4, target=ziel))
    zeit = np.asarray(result["time"])
    amplitude, abklingrate, phase = (2, 0.2, -0.4) if restfrequenz == 5 else (10, 0.5, 0.3)
    erwartet = amplitude * np.exp(-abklingrate * zeit) * np.cos(2 * np.pi * restfrequenz * zeit + phase)

    np.testing.assert_allclose(result["filtered"], erwartet, atol=1e-8)
    np.testing.assert_allclose(np.subtract(result["signal"], result["removed"]), erwartet, atol=1e-8)
    np.testing.assert_allclose(result["model"], result["signal"], atol=1e-8)
    assert result["pencil"]["rank"] == 4
    np.testing.assert_allclose(result["pencil"]["samples"], result["signal"][:4])
    for mode in result["modes"]:
        pol = complex(mode["poleReal"], mode["poleImag"])
        assert np.angle(pol) * result["analysisRate"] / (2*np.pi) == pytest.approx(mode["frequency"])


@pytest.mark.parametrize("quelle", ["positive", "negative"])
def test_messung_zeigt_leistungsantwort_auf_dem_richtigen_zeitraster(quelle):
    result = analyze({"source": quelle})
    assert result["time"][0] == pytest.approx(1)
    assert result["time"][-1] == pytest.approx(7)
    assert result["sampleRate"] == pytest.approx(4000)
    assert result["analysisRate"] == pytest.approx(100)
    assert (result["pencil"]["rows"], result["pencil"]["columns"], result["pencil"]["rank"]) == (345, 256, 12)
    assert any(m["selected"] and abs(m["frequency"] - 2.268) < 0.01 for m in result["modes"])
    np.testing.assert_allclose(np.subtract(result["signal"], result["removed"]), result["filtered"])


def test_generator_schaetzt_frei_gewaehlte_frequenz_ausserhalb_des_zielbands():
    result = analyze({"f1": 27.5, "a2": 0, "order": 2, "target": 1})
    assert len(result["modes"]) == 1
    mode = result["modes"][0]
    assert mode["frequency"] == pytest.approx(27.5)
    assert not mode["selected"]
    np.testing.assert_allclose(result["signal"], result["filtered"])


@pytest.mark.parametrize("versuch", [key for key, data in catalog().items() if "csvPath" in data])
def test_katalog_messdaten_und_voreinstellung(versuch):
    entry = catalog()[versuch]
    assert entry["sourceUrl"].startswith("https://") and entry["license"] and entry["attribution"]
    with entry["csvPath"].open(encoding="utf-8-sig") as stream:
        assert stream.readline().strip() == "time,signal"
        raw = np.loadtxt(stream, delimiter=",")
    assert np.isfinite(raw).all()
    np.testing.assert_allclose(np.diff(raw[:, 0]), 1 / entry["sampleRate"], rtol=2e-5)
    result = analyze({"source": versuch})
    assert result["sampleRate"] == pytest.approx(entry["sampleRate"], rel=2e-5)
    assert result["time"][0] >= entry["t0"]
    assert np.isfinite(result["fitError"])
    np.testing.assert_allclose(np.subtract(result["signal"], result["removed"]), result["filtered"])
    if result["fitError"] > .1:
        assert not any(mode["selected"] for mode in result["modes"])
