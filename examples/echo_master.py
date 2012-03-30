from powerhose.router import Router


router = Router()
try:
    router.start()
finally:
    router.stop()
