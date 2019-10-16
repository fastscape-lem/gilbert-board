from threading import Thread

from ipycanvas import MultiCanvas, hold_canvas
from ipywidgets import (Button, FloatSlider, IntSlider,
                        HBox, VBox, Layout)

from .toposim import TopographySimulator
from .particles import Particles
from .buckets import Buckets


class Board:

    def __init__(self, scale=3):
        self.scale = scale

        self.toposim = TopographySimulator()
        self.particles = Particles(self.toposim, scale)
        self.buckets = Buckets(self.particles, scale)

        self.buckets_height = 150

        canvas_size = (scale * self.toposim.shape[0],
                       scale * self.toposim.shape[1] + self.buckets_height)

        self.canvas = MultiCanvas(ncanvases=3, size=canvas_size)
        self.canvas[0].scale(scale)
        self.canvas[1].global_alpha = 0.4

        self.start_button = Button(description="Start",
                                   icon='play')
        self.stop_button = Button(description="Stop/Reset",
                                  icon='stop',
                                  disabled=True)

        self.start_button.on_click(self.start)
        self.stop_button.on_click(self.stop)

        slider_style = {'description_width': 'initial'}

        self.n_particles_slider = IntSlider(
            value=10000, min=500, max=15000, step=500,
            description='Number of particles', style=slider_style
        )
        self.n_particles_slider.observe(self.on_change_n_particles,
                                        names='value')

        self.kf_slider = FloatSlider(
            value=1e-4, min=5e-5, max=3e-4, step=1e-5,
            description='River incision coefficient', style=slider_style,
            readout_format='.2e'
        )

        self.g_slider = FloatSlider(
            value=1., min=0.5, max=1.5, step=0.1,
            description='River transport coefficient', style=slider_style,
        )

        self.kd_slider = FloatSlider(
            value=0.02, min=0., max=0.1, step=0.01,
            description='Hillslope diffusivity', style=slider_style,
        )

        self.p_slider = FloatSlider(
            value=1., min=0., max=10., step=0.2,
            description='Flow partition exponent', style=slider_style,
        )

        self.process = None
        self._running = False

    def on_change_n_particles(self, change):
        self.particles.n_particles = change.new
        self.initialize()

    def toggle_disabled(self):
        widgets = [self.start_button,
                   self.stop_button,
                   self.n_particles_slider,
                   self.kf_slider,
                   self.g_slider,
                   self.kd_slider,
                   self.p_slider]

        for w in widgets:
            w.disabled = not w.disabled

    def initialize(self):
        self.toposim.initialize()
        self.draw_topography()

        self.particles.initialize()
        self.draw_particles()

        self.buckets.initialize()
        self.draw_buckets()

    def run(self):
        while self._running and not self.buckets.all_in_buckets:
            self.toposim.run_step()
            self.draw_topography()

            self.particles.run_step()
            self.draw_particles()

            self.buckets.run_step()
            self.draw_buckets()

        self.stop_button.description = "Reset"
        self.stop_button.icon = "retweet"

    def set_erosion_params(self):
        self.toposim.set_erosion_params(
            kf=self.kf_slider.value,
            g=self.g_slider.value,
            kd=self.kd_slider.value,
            p=self.p_slider.value
        )

    def start(self, b):
        self.process = Thread(target=self.run)
        self.set_erosion_params()
        self._running = True
        self.process.start()
        self.toggle_disabled()

    def stop(self, b):
        self._running = False
        self.process.join()
        self.reset()
        self.toggle_disabled()

    def reset(self):
        self.toposim.reset()
        self.draw_topography()

        self.particles.reset()
        self.draw_particles()

        self.buckets.reset()
        self.draw_buckets()

        self.stop_button.description = "Stop/Reset"
        self.stop_button.icon = "stop"

    def draw_topography(self):
        with hold_canvas(self.canvas[0]):
            self.canvas[0].clear()
            self.canvas[0].put_image_data(
                self.toposim.shaded_topography, 0, 0
            )

    def draw_particles(self):
        x, y = self.particles.positions

        with hold_canvas(self.canvas[1]):
            self.canvas[1].clear()
            self.canvas[1].fill_style = '#3378b8'
            self.canvas[1].fill_rects(x, y, self.particles.sizes)

    def draw_buckets(self):
        xsize, ysize = self.canvas[2].size

        with hold_canvas(self.canvas[2]):
            self.canvas[2].clear()

            self.canvas[2].font = '20px serif'

            for i, x in enumerate(self.buckets.x_separators[0:-1]):
                k = i + 1
                if k < 10:
                    str_k = f'0{k}'
                else:
                    str_k = str(k)

                self.canvas[2].fill_text(str_k, x + 15, ysize - 120)

            self.canvas[2].fill_style = 'black'
            self.canvas[2].fill_rects(
                self.buckets.x_separators,
                self.toposim.shape[0] * self.scale,
                1, self.buckets_height
            )

            self.canvas[2].fill_style = '#3378b8'
            self.canvas[2].fill_rects(
                self.buckets.x_separators + 5,
                ysize - self.buckets.bar_heights,
                self.buckets.bar_width - 10,
                self.buckets.bar_heights
            )

            self.canvas[2].fill_style = 'black'
            self.canvas[2].fill_rect(0, ysize - 3, xsize, 3)
            self.canvas[2].fill_rect(0, ysize - 155, xsize, 10)

    def show(self):
        self.initialize()

        play_box = HBox((self.start_button, self.stop_button))

        sliders = [self.n_particles_slider,
                   self.kf_slider,
                   self.g_slider,
                   self.kd_slider,
                   self.p_slider]

        for s in sliders:
            s.layout = Layout(width='400px')

        control_box = VBox([play_box] + sliders)
        control_box.layout = Layout(grid_gap='10px')

        main_box = HBox((self.canvas, control_box))
        main_box.layout = Layout(grid_gap='30px')

        return main_box
