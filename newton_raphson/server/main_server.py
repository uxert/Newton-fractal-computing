try:
    import fastapi
    import uvicorn
except ImportError:
    raise ImportError("Install requirements/http-server to run FastAPI webserver")

from contextlib import asynccontextmanager
from typing import cast

import numpy as np
from fastapi import (
    FastAPI,
    Request,
)
from starlette.responses import StreamingResponse

from ..compute.data_models import Task
from ..compute.entrypoints import EntrypointsManager
from ..compute.utils import (
    get_zxy_complex_space_offset,
    produce_png_buffer_from_rcm,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.epm = EntrypointsManager()
    app.state.epm.spawn_local_workers_pool(2)

    yield
    app.state.epm.kill_all_workers()

app = FastAPI(lifespan=lifespan)

#  bare app.state doesn't support typing
def get_entrypoints_manager(request: Request) -> EntrypointsManager:
    return cast(EntrypointsManager, request.app.state.epm)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/api/tiles/{z}/{x}/{y}.png")
def get_tiles(request: Request, z: int, x: float, y: float):
    real, img = get_zxy_complex_space_offset(z, x, y)
    task = Task(0, np.polynomial.Polynomial((1, 0, 0, -1)), real, img)
    result = get_entrypoints_manager(request).submit_task_to_local_pool_and_wait(task, timeout_secs=2)
    if result is None:
        raise RuntimeError("Task failed, probably timeout")
    _, result = result
    buffer = produce_png_buffer_from_rcm(result)
    return StreamingResponse(buffer, media_type="image/png")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


