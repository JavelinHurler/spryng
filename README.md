# Spryng

Spryng is a python framework inspired by Spring from the java/kotlin ecosystem.

## Showcase

```python
# database.py

from spryng.application.module import Module

module = Module(__name__)

@module.component()
class Database:
    def __init__(self):
        self.vals = {}

    def getall(self):
        return list(self.vals.keys())

    def getone(self, key):
        return self.vals.get(key)

    def setone(self, key, value):
        self.vals[key] = value

    def delete(self, key):
        del self.vals[key]
```

```python
# controller.py

from http import HTTPStatus

from spryng.application.module import Module
from spryng.logging import LoggerManager, Logger

from spryng_web.decoration import route, controller, error_handler
from spryng_web.request import RequestHolder
from spryng_web.response import ResponseHolder

from .database import Database

module = Module(__name__)

class BaseController:
    @route(method="GET", path="/test")
    def test(self, req: RequestHolder) -> ResponseHolder:
        return ResponseHolder("test")

@module.component()
@LoggerManager.decorate
@controller(base_path="/api")
class TestController(BaseController):
    log: Logger

    def __init__(self, database: Database):
        self.database = database

    @route(method="GET", path="/")
    def get(self, request: RequestHolder) -> ResponseHolder:
        name = self.parse(request, "name")

        if name is None:
            res = self.database.getall()
            return ResponseHolder(body=str(res))

        res = self.database.getone(name)

        return ResponseHolder(body=str(res))

    @route(method="POST", path="/")
    def post(self, req: RequestHolder) -> ResponseHolder:
        name = self.parse(req, "name")
        value = self.parse(req, "value")

        if name is None or value is None:
            return ResponseHolder(body="Name or value is null", status=HTTPStatus.BAD_REQUEST)

        self.database.setone(name, value)
        return ResponseHolder(body=f"Set {name} to {value}", status=HTTPStatus.CREATED)

    @route(method="DELETE", path="/")
    def delete(self, req: RequestHolder) -> ResponseHolder:
        name = self.parse(req, "name")

        if name is None:
            return ResponseHolder(body="Name is null", status=HTTPStatus.BAD_REQUEST)

        self.database.delete(name)
        return ResponseHolder(body=f"Deleted {name}")


    @route(method="PUT", path="/")
    def put(self, req: RequestHolder) -> ResponseHolder:

        name = self.parse(req, "name")

        if name == "horst":
            raise ValueError("Horst")

        if name == "klaus":
            raise FileNotFoundError("Klaus")

        return ResponseHolder(body=f"Test")


    @error_handler(exception_types={ValueError})
    def handle_value_error(self, req: RequestHolder, error: ValueError) -> ResponseHolder:
        self.log.error(f"Got {error} for request {req.query}")

        return ResponseHolder(body="Caught value error", status=HTTPStatus.OK)


    def parse(self, req: RequestHolder, name):
        raw = req.query.get(name)

        if raw is None or len(raw) != 1:
            return None

        return next(iter(raw))
```

```python
# main.py

from spryng.application.app import Application

from spryng_web.server import Server
from spryng_web.module import module as web_module

from src import controller
from src import database

app = Application()
app.add_modules(
    controller.module,
    database.module,
    web_module
)
app.start()

server = app.get_component_exact(Server)

if __name__ == '__main__':
    server.start_dev("0.0.0.0", 8000)
```

Start server for prod:
```bash
gunicorn src.main:server
```

Start server for dev:
```bash
python3 main.py
```
