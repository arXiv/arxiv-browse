"""Setup GCP trace and logging."""

def setup_trace(name, app):
    """Setup GCP trace and logging."""
    from opentelemetry import trace
    from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.propagators.cloud_trace_propagator import (
        CloudTraceFormatPropagator,
    )
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # https://cloud.google.com/trace/docs/setup/python-ot#initialize_flask
    set_global_textmap(CloudTraceFormatPropagator())
    tracer_provider = TracerProvider()
    cloud_trace_exporter = CloudTraceSpanExporter()
    tracer_provider.add_span_processor(
        BatchSpanProcessor(cloud_trace_exporter)
    )
    trace.set_tracer_provider(tracer_provider)
    tracer = trace.get_tracer(name)
    FlaskInstrumentor().instrument_app(app)
    return tracer
