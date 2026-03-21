from app.core.config import settings
from app.providers.pos.stub import StubPOSProvider
from app.providers.labor.stub import StubLaborProvider

PROVIDER_REGISTRY = {
    "pos": {
        "stub": StubPOSProvider,
    },
    "labor": {
        "stub": StubLaborProvider,
    },
}

def get_pos_provider():
    provider_cls = PROVIDER_REGISTRY["pos"][settings.POS_PROVIDER]
    return provider_cls()

def get_labor_provider():
    provider_cls = PROVIDER_REGISTRY["labor"][settings.LABOR_PROVIDER]
    return provider_cls()
