from PIL import Image, ImageSequence
from PIL import ImageDraw
from PIL import ImageFont

import requests
from io import BytesIO

import os
import json

class BannerGenerator:
    def __init__(self):
        self.output = "banners/banner.gif"
        self.images = []
        self.font_req = requests.get("https://github.com/canonical/Ubuntu-fonts/raw/main/fonts/ttf/Ubuntu-Regular.ttf")
        self.duration = 40 # 5000
        self.invert_direction = False
        
    def generate_images(self, projects):
        for project in projects:
            self.generate_images_for_project(project)
            
    def generate_images_for_project(self, project):

        fontBig = ImageFont.truetype(BytesIO(self.font_req.content), 50)
        fontSmall = ImageFont.truetype(BytesIO(self.font_req.content), 20)
        nameY = 300
        
        
        
        logo_url = project['logo_small_url']
        if logo_url == '':
            logo_url = project['logo_url']
        if logo_url == '':
            return

        response = requests.get(logo_url)
        logo = Image.open(BytesIO(response.content))
        width = logo.size[0]
        height = logo.size[1]
        newHight = 150
        ratio = height / newHight
        newWidth = int(width / ratio)
        if newWidth > 400:
            newWidth = 400
            ratio = width / newWidth
            newHight = int(height / ratio)
        logo = logo.resize((newWidth, newHight), Image.Resampling.LANCZOS)
        offset = 0
        self.invert_direction = not self.invert_direction
        for i in range(50):
            im = Image.new('RGBA', (800, 450), (0, 0, 0, 0))
            draw = ImageDraw.Draw(im)
            stepSize = 57
            if i >= 10 and i < 40:
                stepSize = 5
                
            x = -250 + offset
            nX = 1050 - x
            
            if self.invert_direction:
                temp = x
                x = nX
                nX = temp
                
            
            offset += stepSize
            
            draw.text((400, 20), "@phil1436", (255, 255, 255), font=fontSmall, anchor="mm")
            draw.text((x, nameY), project['name'], (255, 255, 255), font=fontBig, anchor="mm")
            draw.text((nX, nameY + 50), project['description'], (255, 255, 255), font=fontSmall, anchor="mm")

            im.paste(logo, (int((800 - newWidth)/2), nameY - newHight - 50), logo)
            self.images.append(im)
        
    def save(self):
            self.images[0].save(self.output,
                save_all=True, append_images=self.images[1:], optimize=False, duration=self.duration, loop=0, disposal=2)
