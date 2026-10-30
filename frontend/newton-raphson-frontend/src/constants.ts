const DEFAULT_COEFFICIENTS = [-1.33, 0, 11, 0, 15];

export const DEFAULTS = {
    DEFAULT_COEFFICIENTS: DEFAULT_COEFFICIENTS,
    DEFAULT_COEFFICIENTS_PLACEHOLDER: DEFAULT_COEFFICIENTS.join(", "),
    DEFAULT_N: 400,
    DEFAULT_ITERS: 50,
}

export const MAP_CONFIG = {
    MIN_ZOOM: 0,
    MAX_ZOOM: 30,
    ZOOM_SNAP: 1,
    STARTING_VIEW: [0.0, 0.0],
    STARTING_ZOOM: 0,
    TILE_SIZE: 200, // how big should be one tile, smaller value will divide the same image into smaller fragments
}