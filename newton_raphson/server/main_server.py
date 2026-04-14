import uvicorn
from fastapi import FastAPI

from ..compute import entrypoints
from ..compute.utils import get_zxy_complex_space

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/api/tiles/{z}/{x}/{y}")
def get_tiles(z: int, x: int, y: int):
    arr = get_zxy_complex_space(z, x, y, n=10)
    return {
        "real": arr.real.tolist(),
        "imag": arr.imag.tolist(),
        "shape": arr.shape,
        "dtype": str(arr.dtype),
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


