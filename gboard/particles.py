import numpy as np


class Particles:

    def __init__(self, toposim, scale, n_particles=15000, speed_factor=0.5):
        self.n_particles = n_particles
        self.toposim = toposim
        self.shape = toposim.shape
        self.scale = scale
        self.speed_factor = speed_factor

        self.sizes = np.random.randint(2, 6, n_particles)

    def initialize(self):
        nrows, ncols = self.shape
        self.row_idx = np.random.randint(1, nrows // 2,
                                         size=self.n_particles)
        self.col_idx = np.random.randint(0, ncols,
                                         size=self.n_particles)

    def run_step(self):
        sel = self.toposim.receivers[self.row_idx, self.col_idx].ravel()

        # slower the evolution, particles don't always move
        n = int(self.n_particles * self.speed_factor)
        pidx = np.arange(self.n_particles)
        np.random.shuffle(pidx)
        move_idx = pidx[0:n]

        self.row_idx[move_idx] = sel[move_idx] % self.shape[0]
        self.col_idx[move_idx] = ((sel[move_idx] - self.row_idx[move_idx])
                                  // (self.shape[0]))

    @property
    def positions(self):
        x = self.col_idx * self.scale
        y = self.row_idx * self.scale

        return x.astype(np.int32), y.astype(np.int32)

    def reset(self):
        self.initialize()
