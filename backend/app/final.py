from .v2 import app
from .extensions import router as extended_router
from .scoped_nested import router as scoped_nested_router
from .security_middleware import install_nested_rbac_guard
from .admin_sync import sync_admin_password

app.include_router(extended_router)
app.include_router(scoped_nested_router)
install_nested_rbac_guard(app)
app.on_event("startup")(sync_admin_password)
