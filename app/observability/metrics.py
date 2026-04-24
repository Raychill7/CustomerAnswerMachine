from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency",
    ["method", "path"],
)
TOOL_FAILURE_COUNT = Counter(
    "tool_failures_total",
    "Tool execution failures",
    ["tool_name"],
)


def render_metrics() -> bytes:
    return generate_latest()
