from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from prometheus_client import start_http_server, Counter
import time

# Resource attributes for the service
resource = Resource(attributes={
    "service.name": "prime-number-service"
})

# Set up the Tracer Provider
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)

# OTLP Exporter for traces
otlp_span_exporter = OTLPSpanExporter(endpoint="localhost:4317")  # Use the Docker service name
span_processor = BatchSpanProcessor(otlp_span_exporter)
trace_provider.add_span_processor(span_processor)

# Set up the Meter Provider for metrics
metrics.set_meter_provider(MeterProvider())
meter = metrics.get_meter("prime-meter")
prime_counter = meter.create_counter("prime_number_counter", "Counts the number of prime numbers found")

# Create a Prometheus counter
prometheus_counter = Counter('prime_number_counter', 'Counts the number of prime numbers found')

# Start Prometheus metrics server
start_http_server(8000)

# Create a tracer
tracer = trace.get_tracer("prime.tracer")

def is_prime(n):
    """Check if a number is prime."""
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def find_primes(start, end):
    """Find and return prime numbers in a specified range."""
    primes = []
    with tracer.start_as_current_span("find_primes") as span:
        span.set_attributes({"start": start, "end": end})
        
        for number in range(start, end + 1):
            if is_prime(number):
                primes.append(number)
                prime_counter.add(1)  # Increment the counter for each prime found
                prometheus_counter.inc()  # Increment Prometheus counter
                span.add_event("Prime Found", {"number": number})

    return primes

if __name__ == "__main__":
    start_range = 1
    end_range = 100
    print(f"Finding primes between {start_range} and {end_range}...")
    
    primes = find_primes(start_range, end_range)
    print(f"Prime numbers found: {primes}")
