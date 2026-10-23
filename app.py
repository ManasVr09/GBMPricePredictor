"""Quant Society interface for the existing Monte Carlo options engine."""

from pathlib import Path
from uuid import uuid4

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from gbm import price_american_option_lsm, price_european_options, simulate_gbm_paths


st.set_page_config(
    page_title="Monte Carlo options pricer",
    page_icon=":material/query_stats:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Plotly's native template mutes chart text. Inherit the page foreground for
# readable labels in either mode, including instant client-side theme changes.
st.html("""<style>
[data-testid="stPlotlyChart"] svg text { fill: currentColor !important; }
</style>""")

SERIES_COLOR = "#2884CD"


def result_card(label, value, *, text=False, help=None, width=250):
    """Wrap full labels and text outcomes; reserve large metric type for short numbers."""
    with st.container(border=True, width=width):
        st.markdown(label, help=help)
        if text or len(str(value)) > 8:
            st.subheader(str(value), anchor=False)
        else:
            st.metric(label, value, label_visibility="collapsed")


def chart_layout(figure: go.Figure, *, height: int) -> go.Figure:
    """Use inherited foreground text so charts follow live appearance changes."""
    figure.update_layout(
        template="streamlit",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "sans-serif", "size": 14},
        height=height,
        margin={"l": 65, "r": 20, "t": 15, "b": 15},
        showlegend=False,
    )
    figure.update_xaxes(showgrid=False, zeroline=False, automargin=True, title_standoff=18, tickfont={"size": 14}, title_font={"size": 15})
    figure.update_yaxes(zeroline=False, automargin=True, gridcolor="rgba(128,128,128,0.25)", title_standoff=18, tickfont={"size": 14}, title_font={"size": 15})
    return figure


def path_figure(result: dict) -> go.Figure:
    """Show 50 sample paths and the median of all 10,000 paths."""
    times = result["times"]
    figure = go.Figure()
    for path in result["sample_paths"].T:
        figure.add_trace(go.Scatter(
            x=times, y=path, mode="lines", line={"width": 1, "color": SERIES_COLOR},
            opacity=0.38, hoverinfo="skip",
        ))
    figure.add_trace(go.Scatter(
        x=times, y=result["median_path"], mode="lines",
        line={"width": 2.5, "color": SERIES_COLOR}, name="Median path",
        hovertemplate="Year %{x:.2f}<br>Median price $%{y:,.2f}<extra></extra>",
    ))
    figure.add_hline(y=result["strike"], line_dash="dash", line_color="#9A7A45",
                     annotation_text="Strike", annotation_position="top left")
    figure.update_xaxes(title="Time (years)")
    figure.update_yaxes(title="Stock price ($)")
    return chart_layout(figure, height=340)


def expiry_figure(result: dict) -> go.Figure:
    figure = go.Figure(go.Histogram(
        x=result["terminal_prices"], nbinsx=55,
        marker={"color": SERIES_COLOR, "line": {"color": "#FFFFFF", "width": 0.5}},
        opacity=0.8,
        hovertemplate="Stock price $%{x:,.2f}<br>Paths %{y:,}<extra></extra>",
    ))
    figure.add_vline(x=result["strike"], line_dash="dash", line_color="#9A7A45")
    figure.update_xaxes(title="Stock price at expiry ($)")
    figure.update_yaxes(title="Number of paths")
    return chart_layout(figure, height=270)


@st.cache_data(max_entries=4, show_spinner=False)
def render_paths(draw_key: tuple[str, int], _result: dict) -> None:
    # The unique per-draw key prevents different viewers/runs from sharing random results.
    st.plotly_chart(path_figure(_result), width="stretch", theme="streamlit", config={"displayModeBar": False})


@st.cache_data(max_entries=4, show_spinner=False)
def render_expiry(draw_key: tuple[str, int], _result: dict) -> None:
    st.plotly_chart(expiry_figure(_result), width="stretch", theme="streamlit", config={"displayModeBar": False})


with st.sidebar:
    st.header("Model inputs")
    with st.form("pricing_inputs", border=False):
        style = st.selectbox("Exercise style", ["European", "American"])
        kind = st.selectbox("Option type", ["Call", "Put"])
        spot = st.number_input("Stock price ($)", min_value=0.01, value=100.0, step=1.0)
        strike = st.number_input("Strike price ($)", min_value=0.01, value=100.0, step=1.0)
        maturity = st.number_input("Maturity (years)", min_value=0.01, value=1.0, step=0.25)
        volatility = st.number_input("Volatility", min_value=0.0, value=0.20, step=0.01, format="%.2f",
                                     help="Annual volatility as a decimal: 0.20 means 20%.")
        rate = st.number_input("Risk-free rate", value=0.05, step=0.01, format="%.2f",
                               help="Annual rate as a decimal: 0.05 means 5%.")
        steps = st.number_input("Time steps", min_value=2, value=252, step=1,
                                help="252 approximates the number of trading days in a year.")
        calculate = st.form_submit_button("Run simulation", type="primary", width="stretch")

st.title("Monte Carlo options pricer")
if calculate or "pricing_result" not in st.session_state:
    with st.spinner("Simulating 10,000 price paths…"):
        paths = simulate_gbm_paths(spot, rate, volatility, maturity, int(steps))
        if style == "European":
            call, put = price_european_options(paths, strike, rate, maturity)
            price = call if kind == "Call" else put
        else:
            price = price_american_option_lsm(paths, strike, rate, maturity, option_type=kind.lower())
        st.session_state["pricing_result"] = {
            "price": float(price), "style": style, "kind": kind,
            "spot": spot, "strike": strike, "maturity": maturity,
            "volatility": volatility, "rate": rate, "steps": int(steps),
            "times": np.linspace(0, maturity, int(steps) + 1),
            "sample_paths": np.vstack([np.full((1, 50), spot), paths[:, :50]]),
            "median_path": np.r_[spot, np.median(paths, axis=1)],
            "terminal_prices": paths[-1].copy(),
        }
        st.session_state["pricing_draw_id"] = uuid4().hex
        del paths

result = st.session_state["pricing_result"]
if "pricing_draw_id" not in st.session_state:
    st.session_state["pricing_draw_id"] = uuid4().hex
draw_key = (st.session_state["pricing_draw_id"], Path(__file__).stat().st_mtime_ns)
with st.container(horizontal=True):
    result_card("Estimated option value", f"${result['price']:,.2f}")
    result_card("Exercise style", result["style"], text=True)
    result_card("Option type", result["kind"], text=True)
with st.container(border=True):
    st.subheader("Simulated price paths")
    st.caption("50 sample paths · solid line: median of 10,000 paths · dashed line: strike price")
    render_paths(draw_key, result)
with st.container(border=True):
    st.subheader("Where prices finish")
    st.caption("The distribution of all 10,000 terminal prices under the risk-neutral GBM model.")
    render_expiry(draw_key, result)

details = st.expander('Simulation details', on_change="rerun", key="simulation_details")
if details.open:
    with details:
        st.dataframe({
            "Input": ["Stock price", "Strike price", "Maturity", "Volatility", "Risk-free rate", "Time steps", "Simulated paths"],
            "Value": [f"${result['spot']:,.2f}", f"${result['strike']:,.2f}", f"{result['maturity']:g} years",
                      f"{result['volatility']:.1%}", f"{result['rate']:.1%}", f"{result['steps']:,}", "10,000"],
        }, hide_index=True, width="stretch", height="content", row_height=40)
details = st.expander('How the model works', on_change="rerun", key="model_methodology")
if details.open:
    with details:
        st.write(
            "Geometric Brownian Motion simulates prices using a constant volatility and risk-free rate. "
            "European options use the average discounted payoff at expiry. American options use "
            "Longstaff–Schwartz regression to estimate when early exercise is preferable."
        )
        st.write(
            "A call pays max(stock price − strike, 0); a put pays max(strike − stock price, 0). "
            "European options exercise only at expiry; American options may exercise earlier."
        )
        st.caption(
            "The model assumes no dividends, no transaction costs, and constant parameters. "
            "Simulations contain sampling error; the path distribution is risk-neutral, not a forecast "
            "of real-world returns. American exercise is evaluated on the simulated time grid."
        )
st.divider()
st.caption("QUANT SOCIETY · Monte Carlo options pricer · Educational simulation, not investment advice.")
