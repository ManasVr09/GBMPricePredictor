from pathlib import Path

import numpy as np
from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "app.py"


def test_default_result_survives_reruns_and_submitted_inputs_are_used(monkeypatch):
    monkeypatch.syspath_prepend(str(APP.parent))
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    initial = app.session_state["pricing_result"]["price"]
    app.run()
    assert app.session_state["pricing_result"]["price"] == initial
    for widget in app.number_input:
        if widget.label == "Volatility" or widget.label == "Risk-free rate":
            widget.set_value(0.0)
        elif widget.label == "Strike price ($)":
            widget.set_value(90.0)
        elif widget.label == "Time steps":
            widget.set_value(8)
    app.button[0].click().run()
    assert not app.exception
    result = app.session_state["pricing_result"]
    assert result["price"] == 10.0  # Constant $100 stock, $90 strike, zero discount.
    assert result["sample_paths"].shape == (9, 50)
    import json
    chart = app.get("plotly_chart")[0]
    assert json.loads(chart.proto.spec)["layout"]["shapes"][0]["y0"] == 90.0
    assert result["times"][0] == 0
    assert np.all(result["sample_paths"][0] == 100.0)


def test_american_put_uses_the_selected_exercise_style(monkeypatch):
    monkeypatch.syspath_prepend(str(APP.parent))
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    app.get("button_group")[0].set_value("American")
    app.get("button_group")[1].set_value("Put")
    for widget in app.number_input:
        if widget.label == "Time steps":
            widget.set_value(12)
    app.button[0].click().run()
    assert not app.exception
    result = app.session_state["pricing_result"]
    assert result["style"] == "American" and result["kind"] == "Put"
    assert np.isfinite(result["price"]) and result["price"] > 0


def test_separate_visitors_do_not_share_a_random_draw(monkeypatch):
    monkeypatch.syspath_prepend(str(APP.parent))
    first = AppTest.from_file(str(APP), default_timeout=30).run()
    second = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not first.exception and not second.exception
    assert first.session_state["pricing_draw_id"] != second.session_state["pricing_draw_id"]
    assert not np.array_equal(first.session_state["pricing_result"]["terminal_prices"],
                              second.session_state["pricing_result"]["terminal_prices"])
