from gbm import (
    price_american_option_lsm,
    price_european_options,
    simulate_gbm_paths,
)


if __name__ == "__main__":
    S0, r, sigma, T, N, K = 100.0, 0.05, 0.20, 1.0, 252, 100.0
    paths = simulate_gbm_paths(S0, r, sigma, T, N)
    call_price, put_price = price_european_options(paths, K, r, T)
    american_put_price = price_american_option_lsm(paths, K, r, T, option_type="put")

    print(f"Shape: {paths.shape}")
    print(f"Mean terminal price: {paths[-1].mean():.2f}")
    print(f"European call price (K={K:.2f}): {call_price:.2f}")
    print(f"European put price (K={K:.2f}): {put_price:.2f}")
    print(f"American put price, LSM (K={K:.2f}): {american_put_price:.2f}")
