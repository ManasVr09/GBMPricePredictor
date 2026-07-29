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

The sidebar provides pricing inputs and European/American plus Call/Put
selections. The main page shows the calculated price and a Plotly chart of 50
sample simulated paths.
