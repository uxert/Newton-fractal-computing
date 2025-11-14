import multiprocessing

import h5py
import tifffile
import numpy as np
from multiprocessing import Process, Queue
import matplotlib.cm as cm
import uuid
import sys
import os


class TiledTiffWriter:
    """
    A class for writing large files tile-by-tile with compression.
    It compresses the file on-the-fly and writes to disk directly.
    Works only for square images, divided evenly into "square amount" of tiles.
    It works on h5 as intermediate step and then converts to tiff. Uncompressed data does not have to be loaded to ram
    at once
    """

    def __init__(self, filename, tile_queue: multiprocessing.Queue, sqrt_points_total, sqrt_tiles_amount, dtype=np.uint8,
                 compression='adobe_deflate', compression_level=9):
        """
        Initialize the TiledTiffWriter.

        Args:
            filename: Output TIFF filename
            sqrt_points_total: Number of pixels in one axis. Remember, only square images!
            sqrt_tiles_amount: Number of tiles along one axis. Remember, only square images divided evenly into square tiles!.
            dtype: NumPy data type
            compression: Compression method ('adobe_deflate', 'lzw', 'jpeg', None)
            compression_level: Compression level 1-9 (for deflate)
            queue_maxsize: Maximum number of tiles to buffer in queue
        """
        if sqrt_points_total % sqrt_tiles_amount != 0:
            raise ValueError("sqrt_points_total must be divisible by sqrt_tiles_amount")

        self.filename = filename
        self.h5_filename = f"{sqrt_points_total}-{uuid.uuid4()}.h5"
        self.h5_dset_name = "dset"
        self.sqrt_points_total = sqrt_points_total
        self.sqrt_tiles_amount = sqrt_tiles_amount
        self.tile_one_axis_size = int(sqrt_points_total // sqrt_tiles_amount)
        self.dtype = dtype
        self.compression = compression
        self.compression_level = compression_level


        self.total_tiles = sqrt_tiles_amount ** 2

        # Process and queue (initialized in start())
        self.tile_queue = tile_queue
        self.writer_process = None
        self._is_started = False

        print(f"TiledTiffWriter initialized: {self.total_tiles:_} tiles ({self.sqrt_tiles_amount}x{self.sqrt_tiles_amount})\n"
              f"Compression: {self.compression} | Compression level (relevant for deflate only): {self.compression_level}\n")


    def create_h5(self, height, width):
        print(f"Creating {height}x{width} HDF5 file")
        with h5py.File(self.h5_filename, "w") as f:
            _ = f.create_dataset(
                self.h5_dset_name,
                shape=(height, width ),
                dtype='uint8',
                chunks=(128, 128),  # chunk size for efficient access
                compression='gzip',
                compression_opts=self.compression_level  # compression level (1-9)
            )


    def write_one_tile(self, dset, tile_no, tile_data):
        tile_size = self.tile_one_axis_size
        tile_row = tile_no // self.sqrt_tiles_amount
        tile_col = tile_no % self.sqrt_tiles_amount

        start_row = tile_row * tile_size
        start_col = tile_col * tile_size

        dset[start_row:start_row + tile_size,
        start_col:start_col + tile_size] = tile_data + 1  # + 1 so -1 (for black) becomes 0

    def _writer_process_func(self):
        """
        The writer process function that runs in a separate process.
        Keeps the h5 file open and writes fragments as they arrive.
        Thanks to magic of h5 they can be out-of-order.
        """
        with h5py.File(self.h5_filename, "r+") as f:
            dset = f[self.h5_dset_name]
            while True:
                item = self.tile_queue.get(block=True)
                if item is None:
                    break

                tile_no, tile_data = item
                self.write_one_tile(dset, tile_no, tile_data)
        print("Writer process finished.")

    def move_h5_to_tiff(self):

        print("Waiting for writer process to finish...")
        self.writer_process.join()
        cmap = cm.get_cmap("tab10")
        # have to use np.uint16 for colormap. This is just the colormap, not the array with data which is still np.uint8
        colormap = np.zeros((256, 3), dtype=np.uint16)
        for i in range(1, 11):
            rgba = cmap(i - 1)  # this uses 0-9 indexing
            colormap[i, :] = (np.array(rgba[:3]) * 65535).astype(np.uint16)
        colormap = colormap.T

        print("Beginning transfer from h5 to tiff...")
        with h5py.File(self.h5_filename, "r") as f:
            dset = f[self.h5_dset_name]
            tifffile.imwrite(
                self.filename,
                data=dset,
                tile=(256, 256),
                compression='deflate',
                photometric='palette',
                colormap=colormap,
                bigtiff=True
            )
        os.remove(self.h5_filename)
        print("Transfer complete.")

    def start(self):
        """
        Create the file and start the writer process.
        Must be called before writing tiles.
        """
        if self._is_started:
            raise RuntimeError("Writer already started")

        # Create the TIFF structure
        self.create_h5(self.sqrt_points_total, self.sqrt_points_total)

        # Create queue and start writer process
        self.writer_process = Process(target=self._writer_process_func)
        self.writer_process.start()

        self._is_started = True
        print("Writer process ready to receive tiles")

