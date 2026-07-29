"""Streamlit interface for the Monte Carlo options pricing engine."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from gbm import price_american_option_lsm, price_european_options, simulate_gbm_paths


st.set_page_config(page_title="Options Pricer", page_icon="📈", layout="wide")

st.title("Monte Carlo Options Pricer")
st.caption("Estimate an option's value by simulating 10,000 possible future stock-price paths.")

with st.expander("New to options? Read this first"):
    st.markdown(
        """
        An **option** is a contract tied to a stock. A **call** gives its owner
        the right to buy the stock at the strike price; it generally becomes
        more valuable when the stock rises. A **put** gives the right to sell
        at the strike price; it generally becomes more valuable when the stock falls.

        This tool generates many possible future stock prices, calculates what
        the option would be worth in each scenario, and averages those results.
        The price shown is an estimate, not investment advice or a guaranteed value.
        """
    )

with st.sidebar:
    st.header("Model inputs")
    S0 = st.number_input(
        "Current stock price (S₀)", min_value=0.01, value=100.0, step=1.0,
        help="The stock's current market price. For example, enter 100 if one share costs $100 today.",
    )
    K = st.number_input(
        "Strike price (K)", min_value=0.01, value=100.0, step=1.0,
        help="The fixed price at which the option lets you buy (call) or sell (put) the stock.",
    )
    T = st.number_input(
        "Time to maturity (years)", min_value=0.01, value=1.0, step=0.25,
        help="How long until the option expires. Enter 1 for one year, 0.5 for six months, or 0.25 for three months.",
    )
    sigma = st.number_input(
        "Volatility (σ)", min_value=0.0, value=0.20, step=0.01, format="%.2f",
        help="Expected yearly price movement as a decimal. 0.20 means 20% volatility; a larger number means a less predictable stock price.",
    )
    r = st.number_input(
        "Risk-free rate (r)", value=0.05, step=0.01, format="%.2f",
        help="Annual interest rate used to convert future money into today's value. Enter as a decimal: 0.05 means 5%.",
    )
    option_style = st.selectbox(
        "Exercise style", ("European", "American"),
        help="European options can be used only at expiry. American options can be used at any point up to expiry.",
    )
    option_type = st.selectbox(
        "Option type", ("Call", "Put"),
        help="Choose Call if you expect the stock to rise, or Put if you expect it to fall.",
    )
    N = st.number_input(
        "Time steps", min_value=2, value=252, step=1,
        help="How many points in time the simulation checks. 252 is roughly the number of trading days in a year; higher values are more detailed but slower.",
    )
    calculate = st.button("Calculate price", type="primary", use_container_width=True)


def make_path_figure(paths: np.ndarray, maturity: float) -> go.Figure:
    """Return a Plotly line chart containing 50 simulated paths."""
    times = np.linspace(maturity / paths.shape[0], maturity, paths.shape[0])
    figure = go.Figure()

    for path_number in range(min(50, paths.shape[1])):
        figure.add_trace(
            go.Scatter(
                x=times,
                y=paths[:, path_number],
                mode="lines",
                line={"width": 1},
                opacity=0.45,
                showlegend=False,
                hovertemplate="Time: %{x:.2f} years<br>Price: %{y:.2f}<extra></extra>",
            )
        )

    figure.update_layout(
        title="50 simulated stock-price paths",
        xaxis_title="Time (years)",
        yaxis_title="Stock price",
        template="plotly_white",
        margin={"l": 10, "r": 10, "t": 45, "b": 10},
    )
    return figure


if calculate:
    with st.spinner("Simulating 10,000 price paths..."):
        paths = simulate_gbm_paths(S0, r, sigma, T, int(N))

        if option_style == "European":
            european_call, european_put = price_european_options(paths, K, r, T)
            option_price = european_call if option_type == "Call" else european_put
        else:
            option_price = price_american_option_lsm(
                paths, K, r, T, option_type=option_type.lower()
            )

    st.subheader(f"{option_style} {option_type} option price")
    st.markdown(f"# ${option_price:,.2f}")
    st.plotly_chart(make_path_figure(paths, T), use_container_width=True)
else:
    st.info("Set the inputs in the sidebar, then select **Calculate price**.")
