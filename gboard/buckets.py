import numpy as np


class Buckets:

    def __init__(self, particles, scale, n_buckets=10):
        self.shape = particles.shape
        self.scale = scale
        self.particles = particles
        self.n_buckets = n_buckets

        self.bar_width = int(self.shape[1] * scale / n_buckets)

    def initialize(self):
        seps = np.linspace(0,
                           (self.shape[0] - 1) * self.scale,
                           self.n_buckets + 1)
        self.x_separators = np.ceil(seps).astype(np.int32)

        self.count = np.zeros_like(self.x_separators)

    def run_step(self):
        row_idx = self.particles.row_idx
        col_idx = self.particles.col_idx

        at_base_level = np.argwhere(row_idx == self.shape[0] - 1)

        self.count, _ = np.histogram(col_idx[at_base_level],
                                     bins=self.x_separators / self.scale)

    @property
    def all_in_buckets(self):
        return sum(self.count) == self.particles.n_particles

    @property
    def bar_heights(self):
        n_particles = self.particles.n_particles

        return (self.count / (0.75 * n_particles) * 120).astype(np.int32)

    def reset(self):
        self.initialize()
