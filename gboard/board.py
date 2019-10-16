from threading import Thread

from ipycanvas import MultiCanvas, hold_canvas
from ipywidgets import (Button, FloatSlider, IntSlider, HTML, Label,
                        HBox, VBox, Layout)

from .toposim import TopographySimulator
from .particles import Particles
from .buckets import Buckets


class Board:

    def __init__(self, scale=3, buckets_height=150):
        self.scale = scale
        self.buckets_height = buckets_height

        self.toposim = TopographySimulator()
        self.particles = Particles(self.toposim, scale)
        self.buckets = Buckets(self.particles, scale)

        self.setup_canvas()
        self.setup_play_widgets()
        self.setup_particles_widgets()
        self.setup_toposim_widgets()
        self.setup_layout()

        self.process = None
        self._running = False

    def setup_canvas(self):
        # canvas 0: topography
        # canvas 1: particles
        # canvas 2: buckets

        canvas_size = (
            self.scale * self.toposim.shape[0],
            self.scale * self.toposim.shape[1] + self.buckets_height
        )

        self.canvas = MultiCanvas(ncanvases=3, size=canvas_size)

        self.canvas[1].global_alpha = 0.4

    def setup_play_widgets(self):
        self.play_widgets = {
            'start': Button(description="Start", icon='play'),
            'stop': Button(description="Stop/Reset", icon='stop',
                           disabled=True)
        }

        self.play_widgets['start'].on_click(self.start)
        self.play_widgets['stop'].on_click(self.stop)

    def setup_particles_widgets(self):
        self.particles_labels = {
            'size': Label(value='Number of particles'),
            'speed': Label(value='Particle "speed"')
        }

        self.particles_widgets = {
            'size': IntSlider(
                value=10000, min=500, max=15000, step=500
            ),
            'speed': FloatSlider(
                value=0.5, min=0.1, max=1., step=0.1
            )
        }

        self.particles_widgets['size'].observe(
            self.on_change_size, names='value'
        )
        self.particles_widgets['speed'].observe(
            self.on_change_speed, names='value'
        )

    def on_change_size(self, change):
        self.particles.n_particles = change.new
        self.initialize()

    def on_change_speed(self, change):
        self.particles.speed_factor = change.new

    def setup_toposim_widgets(self):
        self.toposim_labels = {
            'kf': Label(value='River incision coefficient'),
            'g': Label(value='River transport coefficient'),
            'kd': Label(value='Hillslope diffusivity'),
            'p': Label(value='Flow partition exponent'),
            'u': Label(value='Plateau uplift rate')
        }

        self.toposim_widgets = {
            'kf': FloatSlider(
                value=1e-4, min=5e-5, max=3e-4, step=1e-5,
                readout_format='.1e'
            ),
            'g': FloatSlider(
                value=1., min=0.5, max=1.5, step=0.1,
                readout_format='.1f'
            ),
            'kd': FloatSlider(
                value=0.02, min=0., max=0.1, step=0.01,
            ),
            'p': FloatSlider(
                value=1., min=0., max=10., step=0.2,
                readout_format='.1f'
            ),
            'u': FloatSlider(
                value=0., min=0., max=1e-3, step=1e-5,
                readout_format='.1e'
            )
        }

    def set_erosion_params(self):
        self.toposim.set_erosion_params(
            kf=self.toposim_widgets['kf'].value,
            g=self.toposim_widgets['g'].value,
            kd=self.toposim_widgets['kd'].value,
            p=self.toposim_widgets['p'].value,
            u=self.toposim_widgets['u'].value
        )

    def setup_layout(self):
        play_box = HBox(tuple(self.play_widgets.values()))

        particles_hboxes = []
        for k in self.particles_widgets:
            self.particles_labels[k].layout = Layout(width='200px')
            self.particles_widgets[k].layout = Layout(width='200px')

            particles_hboxes.append(
                HBox([self.particles_labels[k], self.particles_widgets[k]])
            )

        particles_label = HTML(value='<b>Particles parameters</b>')
        particles_box = VBox(particles_hboxes)
        particles_box.layout = Layout(grid_gap='6px')

        toposim_hboxes = []
        for k in self.toposim_widgets:
            self.toposim_labels[k].layout = Layout(width='200px')
            self.toposim_widgets[k].layout = Layout(width='200px')

            toposim_hboxes.append(
                HBox([self.toposim_labels[k], self.toposim_widgets[k]])
            )

        toposim_label = HTML(
            value='<b>Landscape evolution model parameters</b>'
        )
        toposim_box = VBox(toposim_hboxes)
        toposim_box.layout = Layout(grid_gap='6px')

        control_box = VBox((
            play_box,
            particles_label,
            particles_box,
            toposim_label,
            toposim_box
        ))
        control_box.layout = Layout(grid_gap='10px')

        self.main_box = HBox((self.canvas, control_box))
        self.main_box.layout = Layout(grid_gap='30px')

    def initialize(self):
        self.toposim.initialize()
        self.draw_topography()

        self.particles.initialize()
        self.draw_particles()

        self.buckets.initialize()
        self.draw_buckets()

    def run(self):
        while self._running and not self.buckets.all_in_buckets:
            self.set_erosion_params()

            self.toposim.run_step()
            self.draw_topography()

            self.particles.run_step()
            self.draw_particles()

            self.buckets.run_step()
            self.draw_buckets()

        self.draw_winner()
        self.play_widgets['stop'].description = "Reset"
        self.play_widgets['stop'].icon = "retweet"

    def toggle_disabled(self):
        for w in self.play_widgets.values():
            w.disabled = not w.disabled

        w = self.particles_widgets['size']
        w.disabled = not w.disabled

    def start(self, b):
        self.process = Thread(target=self.run)
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

        self.play_widgets['stop'].description = "Stop/Reset"
        self.play_widgets['stop'].icon = "stop"

    def draw_topography(self):
        with hold_canvas(self.canvas[0]):
            self.canvas[0].save()
            self.canvas[0].clear()
            self.canvas[0].scale(self.scale)
            self.canvas[0].put_image_data(
                self.toposim.shaded_topography, 0, 0
            )
            self.canvas[0].restore()

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
            self.canvas[2].fill_style = 'black'

            for i, x in enumerate(self.buckets.x_separators[0:-1]):
                k = i + 1
                if k < 10:
                    str_k = f'0{k}'
                else:
                    str_k = str(k)

                self.canvas[2].fill_text(str_k, x + 15, ysize - 120)

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

    def draw_winner(self):
        xsize, ysize = self.canvas[2].size

        winner = self.buckets.count.argmax() + 1

        self.canvas[2].font = '50px serif'
        self.canvas[2].fill_style = '#3378b8'
        self.canvas[2].fill_text(f"{winner} wins!", xsize // 3 , ysize // 2.5)

    def show(self):
        self.initialize()

        return self.main_box
