# Dashboard performance

Random simulations remain per session: a fresh visitor or explicit Run generates its own draw, while ordinary reruns preserve the existing result. No global cache reuses random pricing results between viewers.

The two static Plotly outputs use bounded four-entry caches keyed by a unique per-draw identifier and the app implementation timestamp. The corresponding result is not mutated. This avoids repeatedly constructing and serializing the same 50 trajectories and terminal-price distribution. Optional details are loaded only when expanded. No paths, time steps, precision, or chart samples are reduced.

Tests verify deterministic pricing, American selection, chart updates after submitting new inputs, persistence, and independent viewer draws. The Python pricing engine is unchanged.
