from PIL import Image, ImageDraw, ImageFont, ImageOps
import os


class Nonsense:
    def __init__(self):
        path = os.path.dirname(__file__)
        self.font_path = os.path.join(path, 'crayon.ttf')
        self.image_path = os.path.join(path, 'nonsense.jpg')


    def create_image(self, days=0):
        if days < 0:
            raise NonenseException("Negative nonsense days is nonsense")

        if days > 9999:
            raise NonenseException("Nonsense out of bounds")

        days = str(days)

        original = Image.open(self.image_path)
        text_box = Image.new('L', (160, 160))

        overlay = ImageDraw.Draw(text_box)
        overlay.text(
            (0, 0),
            days,
            font=self._scale_font(days),
            fill=255)
        wrapper = text_box.rotate(-10, expand=1)

        original.paste(
            ImageOps.colorize(wrapper, (0,0,0), 'rgb(111, 109, 125)'),
            self._get_text_coordinates(days),
            wrapper)
        original.save("nonsense_1.jpg")

    def _scale_font(self, days):
        length = len(days)
        max_size = 200
        length * 40

        size = max_size
        if length == 1:
            size = max_size
        if length == 2:
            size = max_size - 40
        if length == 3:
            size = max_size - 85
        if length == 4:
            size = max_size - 120

        return ImageFont.truetype(self.font_path, size=size)

    def _get_text_coordinates(self, days):
        x_axis = 260
        y_axis = 615
        length = len(days)

        if length == 1:
            return (x_axis, y_axis)
        if length == 2:
            return (x_axis - 35, y_axis)
        if length == 3:
            return (x_axis - 42, y_axis + 15)
        if length == 4:
            return (x_axis - 38, y_axis + 35)


class NonenseException(Exception):
    def __init__(self, message):
        super(NonenseException, self).__init__(f"Nonsense infraction: {message}")
