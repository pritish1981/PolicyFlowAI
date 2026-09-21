from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send


class HealthAwareTrustedHostMiddleware:
    """Validate browser/API hosts while allowing ALB target liveness probes."""

    def __init__(self, app: ASGIApp, allowed_hosts: list[str]) -> None:
        self.app = app
        self.trusted = TrustedHostMiddleware(app, allowed_hosts=allowed_hosts)

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope.get("type") == "http" and scope.get("path") == "/health":
            await self.app(scope, receive, send)
            return
        await self.trusted(scope, receive, send)
