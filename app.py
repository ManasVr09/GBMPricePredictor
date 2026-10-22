"""Quant Society interface for the existing Monte Carlo options engine."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from gbm import price_american_option_lsm, price_european_options, simulate_gbm_paths


st.set_page_config(
    page_title="Monte Carlo options pricer",
    page_icon=":material/query_stats:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

GREEN = "#16836B"


def chart_layout(figure: go.Figure, *, height: int) -> go.Figure:
    """Keep both charts consistent with the light research theme."""
    figure.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif", "size": 14, "color": "#454B46"},
        height=height,
        margin={"l": 12, "r": 12, "t": 15, "b": 15},
        showlegend=False,
    )
    figure.update_xaxes(showgrid=False, zeroline=False)
    figure.update_yaxes(gridcolor="#ECEEEA", zeroline=False)
    return figure


def path_figure(result: dict) -> go.Figure:
    """Show 50 sample paths and the median of all 10,000 paths."""
    times = result["times"]
    figure = go.Figure()
    for path in result["sample_paths"].T:
        figure.add_trace(go.Scatter(
            x=times, y=path, mode="lines", line={"width": 1, "color": GREEN},
            opacity=0.18, hoverinfo="skip",
        ))
    figure.add_trace(go.Scatter(
        x=times, y=result["median_path"], mode="lines",
        line={"width": 2.5, "color": GREEN}, name="Median path",
        hovertemplate="Year %{x:.2f}<br>Median price $%{y:,.2f}<extra></extra>",
    ))
    figure.add_hline(y=result["strike"], line_dash="dash", line_color="#A46E35",
                     annotation_text="Strike", annotation_position="top left")
    figure.update_xaxes(title="Time (years)")
    figure.update_yaxes(title="Stock price ($)")
    return chart_layout(figure, height=340)


def expiry_figure(result: dict) -> go.Figure:
    figure = go.Figure(go.Histogram(
        x=result["terminal_prices"], nbinsx=55,
        marker={"color": GREEN, "line": {"color": "#FFFFFF", "width": 0.5}},
        opacity=0.8,
        hovertemplate="Stock price $%{x:,.2f}<br>Paths %{y:,}<extra></extra>",
    ))
    figure.add_vline(x=result["strike"], line_dash="dash", line_color="#A46E35")
    figure.update_xaxes(title="Stock price at expiry ($)")
    figure.update_yaxes(title="Number of paths")
    return chart_layout(figure, height=270)


with st.container(horizontal_alignment="center"):
    with st.container(width=1200):
        st.markdown("### Monte Carlo options pricer")
        st.divider()
        inputs, output = st.columns([1.4, 4.6], gap="large")

        with inputs:
            st.markdown("**Model inputs**")
            with st.form("pricing_inputs", border=False):
                style = st.segmented_control("Exercise style", ["European", "American"], default="European", required=True)
                kind = st.segmented_control("Option type", ["Call", "Put"], default="Call", required=True)
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

        with output:
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
                    del paths

            result = st.session_state["pricing_result"]
            cards = st.columns(3)
            cards[0].metric("Estimated option value", f"${result['price']:,.2f}", border=True)
            cards[1].metric("Exercise style", result["style"], border=True)
            cards[2].metric("Option type", result["kind"], border=True)
            with st.container(border=True):
                st.subheader("Simulated price paths")
                st.caption("50 sample paths · solid line: median of 10,000 paths · dashed line: strike price")
                st.plotly_chart(path_figure(result), width="stretch", config={"displayModeBar": False})
            with st.container(border=True):
                st.subheader("Where prices finish")
                st.caption("The distribution of all 10,000 terminal prices under the risk-neutral GBM model.")
                st.plotly_chart(expiry_figure(result), width="stretch", config={"displayModeBar": False})

            with st.expander("Simulation details"):
                st.dataframe({
                    "Input": ["Stock price", "Strike price", "Maturity", "Volatility", "Risk-free rate", "Time steps", "Simulated paths"],
                    "Value": [f"${result['spot']:,.2f}", f"${result['strike']:,.2f}", f"{result['maturity']:g} years",
                              f"{result['volatility']:.1%}", f"{result['rate']:.1%}", f"{result['steps']:,}", "10,000"],
                }, hide_index=True, width="stretch", height="content", row_height=40)
            with st.expander("How the model works"):
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
