import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if "kafka" not in sys.modules:
    kafka_module = types.ModuleType("kafka")

    class _DummyKafkaClient:
        def __init__(self, *args, **kwargs):
            return None

        def close(self):
            return None

    kafka_module.KafkaConsumer = _DummyKafkaClient
    kafka_module.KafkaProducer = _DummyKafkaClient
    sys.modules["kafka"] = kafka_module

os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "inventory")
os.environ.setdefault("POSTGRES_USER", "inventory_user")
os.environ.setdefault("POSTGRES_PASSWORD", "inventory_pass")
