"""
Bespoke probes and actions for one scenario.

Plain functions, importable through PYTHONPATH. Arguments and return values
must be JSON-serialisable. Raise to signal failure. Bound every call.
"""

import time
import urllib.error
import urllib.request


def latency_percentile_ms(
    url: str,
    samples: int = 20,
    percentile: float = 0.95,
    timeout: float = 2.0,
) -> float:
    """
    Latency percentile of `samples` sequential GET requests, in ms. A failed
    or timed out request counts as `timeout` so errors cannot hide in a good
    percentile.
    """
    durations = []
    for _ in range(samples):
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                r.read()
            durations.append((time.perf_counter() - start) * 1000)
        except (urllib.error.URLError, TimeoutError, OSError):
            durations.append(timeout * 1000)
    durations.sort()
    index = min(len(durations) - 1, int(percentile * len(durations)))
    return round(durations[index], 1)


def error_ratio(url: str, samples: int = 20, timeout: float = 2.0) -> float:
    """Ratio of requests that failed or returned a 5xx, between 0 and 1."""
    return round(_bad_ratio(url, samples, timeout, None), 3)


def burn_rate(
    url: str,
    slo_target: float,
    samples: int = 20,
    latency_threshold_ms: float | None = None,
    timeout: float = 2.0,
) -> float:
    """
    Error budget burn rate over `samples` requests: the ratio of bad requests
    divided by the budget `1 - slo_target`. 1.0 consumes the budget exactly
    over the SLO window; 14.4 consumes 2% of a 30-day budget in one hour.

    A request is bad when it fails, returns a 5xx or, when
    `latency_threshold_ms` is given, is slower than it. Use the threshold and
    target of the real SLO.
    """
    budget = 1.0 - slo_target
    if budget <= 0:
        raise ValueError("slo_target must be lower than 1")
    bad = _bad_ratio(url, samples, timeout, latency_threshold_ms)
    return round(bad / budget, 2)


def _bad_ratio(
    url: str, samples: int, timeout: float, latency_threshold_ms: float | None
) -> float:
    bad = 0
    for _ in range(samples):
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                r.read()
        except urllib.error.HTTPError as x:
            bad += x.code >= 500
            continue
        except (urllib.error.URLError, TimeoutError, OSError):
            bad += 1
            continue
        elapsed_ms = (time.perf_counter() - start) * 1000
        if (
            latency_threshold_ms is not None
            and elapsed_ms > latency_threshold_ms
        ):
            bad += 1
    return bad / samples
