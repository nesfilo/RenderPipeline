"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""
from __future__ import division
from rplibs.six.moves import range

from panda3d.core import SamplerState

from rpcore.globals import Globals
from rpcore.render_stage import RenderStage

class PSSMShadowStage(RenderStage):

    """ This stage generates the depth-maps used for rendering PSSM """

    required_inputs = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, "PSSMShadowStage", pipeline)
        self.num_splits = 3
        self.split_resolution = 512
        self.split_regions = []

    @property
    def produced_pipes(self):
        return {
            "PSSMShadowAtlas": self._target['depth'],
            "PSSMShadowAtlasPCF": (self._target['depth'], self.make_pcf_state()),
        }

    def make_pcf_state(self):
        state = SamplerState()
        state.set_minfilter(SamplerState.FT_shadow)
        state.set_magfilter(SamplerState.FT_shadow)
        return state

    def get_shadow_tex(self):
        return self._target["depth"]

    def create(self):
        self._target = self.make_target("ShadowMap")
        self._target.set_source(None, Globals.base.win)
        self._target.size = (self.split_resolution * self.num_splits, self.split_resolution)
        self._target.add_depth_texture(bits=32)
        self._target.create_overlay_quad = False
        self._target.color_write = False
        self._target.prepare_scene_render()

        # Remove all unused display regions
        internal_buffer = self._target.get_internal_buffer()
        internal_buffer.remove_all_display_regions()
        internal_buffer.get_display_region(0).set_active(False)

        # Prepare the display regions
        for i in range(self.num_splits):
            region = internal_buffer.make_display_region(
                i / self.num_splits,
                i / self.num_splits + 1 / self.num_splits, 0, 1)
            region.set_clear_depth(1)
            region.set_clear_color_active(False)
            region.set_clear_depth_active(True)
            region.set_sort(25 + i)
            region.set_active(True)
            self.split_regions.append(region)

    def set_shader_input(self, *args):
        Globals.render.set_shader_input(*args)