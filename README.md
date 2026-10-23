# GBM Price Simulator

Simulates 10,000 stock-price paths under Geometric Brownian Motion.

It also estimates European option values by calculating each path's terminal
payoff, averaging across all paths, and discounting at the risk-free rate.

## Run

```bash
python3 example.py
```

The function returns an array with shape `(N, 10000)`. Each row is a time step and each column is an independent simulated path.

`price_european_options(paths, K, r, T)` returns the Monte Carlo estimates for
a European call and put, using `max(S_T - K, 0)` and `max(K - S_T, 0)` respectively.

`price_american_option_lsm(paths, K, r, T, option_type="put", degree=2)`
prices an American call or put via Longstaff-Schwartz least-squares Monte Carlo.
At every pre-maturity time step, it fits a polynomial regression of discounted
future cash flows against the current price on in-the-money paths, then chooses
early exercise when the immediate payoff is greater than the continuation value.

## Web app

Install the dependencies and start the Streamlit interface:

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

The dashboard uses the classic wide Streamlit layout with inputs in the native
left sidebar. Light mode matches Quant Society’s off-white (#F8F6F2), and dark mode
uses classic grey. Switch with **⋮ → Light / Dark**. Website links start in off-white
using `embed_options=light_theme`; direct visits respect system/saved preferences. The default European call runs
once when the app opens. Submit **Run simulation** to apply inputs and generate a
new estimate; results remain stable across unrelated reruns.

Result cards show the option value, exercise style, and option type. The charts
show 50 sample paths, the median across all 10,000 paths, the strike price, and
the terminal-price distribution. Methodology and the inputs used for the current
result are available in expanders. The Python pricing engine in `gbm.py` is unchanged.

Use Streamlit 1.60 or later. Community Cloud should deploy `app.py` from the root
of this repository; `.streamlit/config.toml` provides both shared themes. Chart text follows the active foreground color immediately.

## Performance

See the [performance notes](PERFORMANCE.md) for caching, lazy loading, and preservation guarantees.
