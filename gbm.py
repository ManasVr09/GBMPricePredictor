"""Geometric Brownian Motion stock-price simulation."""

import numpy as np


def simulate_gbm_paths(S0: float, r: float, sigma: float, T: float, N: int) -> np.ndarray:
    """Simulate 10,000 future stock-price paths using Geometric Brownian Motion.

    Parameters
    ----------
    S0 : float
        Current stock price; must be positive.
    r : float
        Annualised risk-free interest rate, expressed as a decimal.
    sigma : float
        Annualised volatility, expressed as a decimal; must be non-negative.
    T : float
        Time to maturity in years; must be positive.
    N : int
        Number of simulation time steps; must be positive.

    Returns
    -------
    numpy.ndarray
        Simulated prices with shape ``(N, 10000)``. The first row represents
        the price after one time step, so the starting price is not included.
    """
    if S0 <= 0:
        raise ValueError("S0 must be positive.")
    if sigma < 0:
        raise ValueError("sigma must be non-negative.")
    if T <= 0:
        raise ValueError("T must be positive.")
    if N <= 0:
        raise ValueError("N must be positive.")

    n_paths = 10_000
    dt = T / N
    shocks = np.random.standard_normal((N, n_paths))
    log_returns = (r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * shocks

    return S0 * np.exp(np.cumsum(log_returns, axis=0))


def price_european_options(paths: np.ndarray, K: float, r: float, T: float) -> tuple[float, float]:
    """Estimate European call and put prices from simulated stock-price paths.

    The final stock price from every path is used to calculate the payoffs:
    ``max(S_T - K, 0)`` for the call and ``max(K - S_T, 0)`` for the put.
    The average payoff is discounted by ``exp(-r * T)``.

    Returns
    -------
    tuple[float, float]
        ``(call_price, put_price)``.
    """
    if paths.ndim != 2 or paths.shape[0] == 0:
        raise ValueError("paths must be a non-empty two-dimensional array.")
    if K <= 0:
        raise ValueError("K must be positive.")
    if T <= 0:
        raise ValueError("T must be positive.")

    terminal_prices = paths[-1]
    call_payoffs = np.maximum(terminal_prices - K, 0.0)
    put_payoffs = np.maximum(K - terminal_prices, 0.0)
    discount_factor = np.exp(-r * T)

    return discount_factor * call_payoffs.mean(), discount_factor * put_payoffs.mean()


def price_american_option_lsm(
    paths: np.ndarray,
    K: float,
    r: float,
    T: float,
    option_type: str = "put",
    degree: int = 2,
) -> float:
    """Price an American option using the Longstaff-Schwartz method.

    At each time step, the function regresses discounted future cash flows on
    the current stock price for in-the-money paths. It exercises paths where
    the immediate payoff exceeds the fitted continuation value.

    Parameters
    ----------
    paths : numpy.ndarray
        Simulated prices with shape ``(N, n_paths)``. The initial price is not
        included; the final row contains prices at maturity.
    K, r, T : float
        Strike, annualised risk-free rate, and maturity in years.
    option_type : {"call", "put"}
        American option type.
    degree : int
        Polynomial degree used for the least-squares continuation regression.
    """
    if paths.ndim != 2 or paths.shape[0] < 2:
        raise ValueError("paths must be a two-dimensional array with at least two time steps.")
    if K <= 0 or T <= 0:
        raise ValueError("K and T must be positive.")
    if option_type not in {"call", "put"}:
        raise ValueError("option_type must be 'call' or 'put'.")
    if degree < 0:
        raise ValueError("degree must be non-negative.")

    def payoff(stock_prices: np.ndarray) -> np.ndarray:
        if option_type == "call":
            return np.maximum(stock_prices - K, 0.0)
        return np.maximum(K - stock_prices, 0.0)

    n_steps = paths.shape[0]
    dt = T / n_steps
    step_discount = np.exp(-r * dt)

    # Values are held at the next exercise date, initially maturity.
    values = payoff(paths[-1])

    # Work backward from the penultimate date to the first simulated date.
    for step in range(n_steps - 2, -1, -1):
        values *= step_discount
        current_prices = paths[step]
        exercise_values = payoff(current_prices)
        in_the_money = exercise_values > 0

        # Fit continuation value only where exercising is a viable choice.
        n_itm = np.count_nonzero(in_the_money)
        if n_itm > degree:
            coefficients = np.polyfit(
                current_prices[in_the_money], values[in_the_money], degree
            )
            continuation_values = np.polyval(coefficients, current_prices[in_the_money])
            exercise_now = exercise_values[in_the_money] > continuation_values
            itm_indices = np.flatnonzero(in_the_money)
            values[itm_indices[exercise_now]] = exercise_values[itm_indices[exercise_now]]

    # The first simulated date is one time step after valuation date zero.
    return float(step_discount * values.mean())
