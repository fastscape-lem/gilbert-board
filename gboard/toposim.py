import math

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
import fastscapelib_fortran as fs


class TopographySimulator:

    def __init__(self, shape=(170, 170), length=(2e4, 1e4)):
        self.shape = np.array(shape)
        self.length = np.array(length)
        self.spacing = self.length / (self.shape - 1)

        # shaded relief
        self.cycle_length = 300
        self.cycle_start = 0.3
        self.cmap = plt.cm.copper

    def get_sun_light(self):
        t = self.step + self.cycle_start * self.cycle_length

        azdeg = 365 * (t % self.cycle_length) / self.cycle_length
        altdeg = max(140 * abs(math.sin(t * math.pi / self.cycle_length)) - 70,
                     0)

        return azdeg, altdeg

    def set_erosion_params(self, kf=1e-4, kd=1e-2, g=1., p=1., u=0.):
        kfa = np.full(self.topography.size, kf)
        kda = np.full(self.topography.size, kd)

        fs.fastscape_set_erosional_parameters(
            kfa, kf, 0.4, 1.,
            kda, kd, g, g, p
        )

        # plateau uplift
        scarp_row_idx = self.shape[0] // 2
        ua = np.zeros_like(self.topography)
        ua[:scarp_row_idx, :] = u
        fs.fastscape_set_u(ua)

    def initialize(self):
        self.step = 0

        fs.fastscape_set_nx_ny(*self.shape)
        fs.fastscape_setup()
        fs.fastscape_set_xl_yl(*self.length)

        scarp_row_idx = self.shape[0] // 2

        self.topography = np.random.random_sample(self.shape)
        self.topography[:scarp_row_idx, :] += 1000.

        fs.fastscapecontext.h = self.topography.ravel(order='F')

        bc = 100
        fs.fastscape_set_bc(bc)

        self.set_erosion_params()

        fs.fastscape_set_dt(2e3)

        self.receivers = np.arange(self.topography.size).reshape(self.shape)

    def set_receivers(self):
        weights = fs.fastscapecontext.mwrec
        mrec = fs.fastscapecontext.mrec.astype('int') - 1

        cum_weights = np.cumsum(weights, axis=0)
        rand = np.random.uniform(size=self.topography.size)
        rec_idx = np.argmax(cum_weights >= rand, axis=0)
        rec = mrec[rec_idx, range(self.topography.size)]

        # base level
        srec = fs.fastscapecontext.rec.astype('int') - 1
        at_base_level = np.argwhere(srec == np.arange(self.topography.size))
        rec[at_base_level] = srec[at_base_level]

        self.receivers = rec.reshape(self.shape, order='F')

    def run_step(self):
        self.step += 1

        fs.fastscape_execute_step()
        self.topography = fs.fastscapecontext.h.reshape(self.shape, order='F')

        self.set_receivers()

    @property
    def shaded_topography(self):
        dx, dy = self.spacing

        ls = LightSource(*self.get_sun_light())

        vmax=max(1200, self.topography.max())

        rgb = ls.shade(
            self.topography, cmap=self.cmap,
            blend_mode='overlay', vert_exag=4,
            dx=dx, dy=dy, vmin=-300, vmax=vmax
        )

        return rgb * 255

    def reset(self):
        fs.fastscape_destroy()
        self.initialize()
