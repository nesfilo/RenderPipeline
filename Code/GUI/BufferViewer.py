
from functools import partial

from panda3d.core import Texture, Vec3, Shader, LVecBase2i
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectScrolledFrame import DirectScrolledFrame
from direct.gui.DirectGui import DGG

from ..Util.Generic import rgb_from_string
from ..Globals import Globals
from ..RenderTarget import RenderTarget
from TexturePreview import TexturePreview
from BetterOnscreenImage import BetterOnscreenImage
from BetterOnscreenText import BetterOnscreenText
from DraggableWindow import DraggableWindow


class BufferViewer(DraggableWindow):

    """ This class provides a view into the buffers to inspect them """

    _REGISTERED_ENTRIES = []

    @classmethod
    def register_entry(cls, entry):
        """ Adds a new target to the registered entries """
        cls._REGISTERED_ENTRIES.append(entry)

    @classmethod
    def unregister_entry(cls, entry):
        """ Removes a target from the registered entries """
        if entry in cls._REGISTERED_ENTRIES:
            cls._REGISTERED_ENTRIES.remove(entry)

    def __init__(self, pipeline):
        """ Constructs the buffer viewer """
        DraggableWindow.__init__(self, width=1400, height=800,
                                 title="Buffer- and Image-Browser")
        RenderTarget.RT_CREATE_HANDLER = self.register_entry
        self._pipeline = pipeline
        self._scroll_height = 3000
        self._stages = []
        self._create_shaders()
        self._create_components()
        self._tex_preview = TexturePreview()
        self._tex_preview.hide()
        self.hide()

    def toggle(self):
        """ Updates all the buffers and then toggles the buffer viewer """
        if self._visible:
            self._remove_components()
            self.hide()
        else:
            self._perform_update()
            self.show()

    def _create_shaders(self):
        """ Create the shaders to display the textures """
        self._display_2d_tex_shader = Shader.load(Shader.SL_GLSL,
            "Shader/GUI/vertex.glsl", "Shader/GUI/display2DTex.glsl")
        self._display_3d_tex_shader = Shader.load(Shader.SL_GLSL,
            "Shader/GUI/vertex.glsl", "Shader/GUI/display3DTex.glsl")
        self._display_2d_tex_array_shader = Shader.load(Shader.SL_GLSL,
            "Shader/GUI/vertex.glsl", "Shader/GUI/display2DTexArray.glsl")
        self._display_buffer_tex_shader = Shader.load(Shader.SL_GLSL,
            "Shader/GUI/vertex.glsl", "Shader/GUI/displayBufferTex.glsl")

    def _create_components(self):
        """ Creates the window components """
        DraggableWindow._create_components(self)

        self._content_frame = DirectScrolledFrame(
            frameSize=(0, self._width - 15, 0, self._height - 50),
            canvasSize=(0, self._width - 80, 0, self._scroll_height),
            autoHideScrollBars=False,
            scrollBarWidth=20.0,
            frameColor=(0, 0, 0, 0),
            verticalScroll_relief=False,
            horizontalScroll_relief=False,
            horizontalScroll_incButton_relief=False,
            horizontalScroll_decButton_relief=False,
            horizontalScroll_thumb_relief=False,
            parent=self._node,
            pos=(0, 1, -self._height - 10))
        self._content_node = self._content_frame.getCanvas().attach_new_node(
            "BufferComponents")
        self._content_node.set_scale(1, 1, -1)
        self._content_node.set_z(self._scroll_height)

    def _remove_components(self):
        """ Removes all components of the buffer viewer """
        self._content_node.removeChildren()
        self._tex_preview.hide()

    def _perform_update(self):
        """ Collects all entries, extracts their images and re-renders the
        window """

        # Collect texture stages
        self._stages = []
        for entry in self._REGISTERED_ENTRIES:
            if isinstance(entry, Texture):
                self._stages.append(entry)
            # Cant use isinstance or we get circular references
            elif str(entry.__class__).endswith("RenderTarget"):
                for target in entry.get_all_targets():
                    self._stages.append(entry[target])
            # Cant use isinstance or we get circular references
            elif str(entry.__class__).endswith("Image"):
                self._stages.append(entry.get_texture())
            else:
                self.warn("Unrecognized instance!", entry.__class__)

        self._render_stages()

    def _on_texture_hovered(self, hover_frame, evt=None):
        """ Internal method when a texture is hovered """
        hover_frame["frameColor"] = (0, 0, 0, 0.1)

    def _on_texture_blurred(self, hover_frame, evt=None):
        """ Internal method when a texture is blurred """
        hover_frame["frameColor"] = (0, 0, 0, 0)

    def _on_texture_clicked(self, tex_handle, evt=None):
        """ Internal method when a texture is blurred """
        self._tex_preview.present(tex_handle)

    def _render_stages(self):
        """ Renders the stages to the window """

        self._remove_components()
        entries_per_row = 5
        aspect = Globals.base.win.get_y_size() /\
            float(Globals.base.win.get_x_size())
        entry_width = 255
        entry_height = (entry_width - 20) * aspect + 55

        # Iterate over all stages
        for index, stage_tex in enumerate(self._stages):
            stage_name = stage_tex.get_name()
            stage_prefix = "-".join(stage_name.split("-")[:-1]) \
                if "-" in stage_name else stage_name

            xoffs = index % entries_per_row
            yoffs = index / entries_per_row

            node = self._content_node.attach_new_node("Preview")
            node.set_sz(-1)
            node.set_pos(30 + xoffs * entry_width, 1, yoffs * entry_height)

            r, g, b = rgb_from_string(stage_prefix, min_brightness=0.4)

            DirectFrame(parent=node,
                        frameSize=(0, entry_width - 10, 0, -entry_height + 10),
                        frameColor=(r, g, b, 1.0),
                        pos=(0, 0, 0))

            frame_hover = DirectFrame(parent=node,
                                      frameSize=(0, entry_width - 10, 0, -entry_height + 10),
                                      frameColor=(0, 0, 0, 0),
                                      pos=(0, 0, 0), state=DGG.NORMAL)
            frame_hover.bind(DGG.ENTER,
                             partial(self._on_texture_hovered, frame_hover))
            frame_hover.bind(DGG.EXIT,
                             partial(self._on_texture_blurred, frame_hover))
            frame_hover.bind(DGG.B1PRESS,
                             partial(self._on_texture_clicked, stage_tex))

            BetterOnscreenText(text=stage_name, x=10, y=26, parent=node,
                               size=15, color=Vec3(0.2))

            # Scale image so it always fits
            w, h = stage_tex.get_x_size(), stage_tex.get_y_size()
            scale_x = float(entry_width - 30) / max(1, w)
            scale_y = float(entry_height - 60) / max(1, h)
            scale_factor = min(scale_x, scale_y)

            if stage_tex.get_texture_type() == Texture.TT_buffer_texture:
                scale_factor = 1
                w = entry_width - 30
                h = entry_height - 60

            preview = BetterOnscreenImage(image=stage_tex, w=scale_factor * w,
                                          h=scale_factor * h, any_filter=False,
                                          parent=node, x=10, y=40,
                                          transparent=False)

            if stage_tex.get_z_size() <= 1:
                if stage_tex.get_texture_type() == Texture.TT_buffer_texture:
                    preview.set_shader(self._display_buffer_tex_shader)
                    preview.set_shader_input("viewSize", LVecBase2i(
                        int(scale_factor * w),
                        int(scale_factor * h)))
                else:
                    preview.set_shader(self._display_2d_tex_shader)
            else:
                if stage_tex.get_texture_type() == Texture.TT_2d_texture_array:
                    preview.set_shader(self._display_2d_tex_array_shader)
                else:
                    preview.set_shader(self._display_3d_tex_shader)