"""Краткая шпаргалка по python.libs.infra (копипаста в любой сервис)."""

# В Server.init_fast_api:
#   self.infra_support.mount(app)

# В хендлерах:
#   from python.libs.infra.decorators import require_s2s, idempotent, rate_limit, read_validated_upload
#
#   @app.post("/users")
#   @require_s2s
#   @idempotent("users.create")
#   @rate_limit("users.create", limit=30)
#   async def create_user(request: Request, body: ...):
#       ...
#
#   data, ctype, ext = await read_validated_upload(file)

# В use-case вместо event_bus:
#   await self.outbox.publish("user.created", event)
