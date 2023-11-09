from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import requests
from io import BytesIO

import os

class BannerGenerator:
    def __init__(self, output, githubname):
        self.output = output
        self.githubname = githubname
        self.images = []
        self.font_req = requests.get("https://github.com/canonical/Ubuntu-fonts/raw/main/fonts/ttf/Ubuntu-Regular.ttf")
        self.duration = 70 # 70 milliseconds per frame
        self.invert_direction = False
        
    def generate_images(self, projects):
        if len(projects) == 0:
            return
        if self.output == '':
            return
        for project in projects:
            try:
                self.generate_images_for_project(project)
            except:
                print("Error generating image for project: " + project['name'])
                continue
            
    def generate_images_for_project(self, project):
        if self.output == '':
            return
        
        fontBig = ImageFont.truetype(BytesIO(self.font_req.content), 50)
        fontSmall = ImageFont.truetype(BytesIO(self.font_req.content), 20)
        nameY = 300
        
        #get logo url
        logo_url = project['logo_small_url']
        if logo_url == '':
            logo_url = project['logo_url']
        if logo_url == '':
            return

        # get logo
        response = requests.get(logo_url)
        logo = Image.open(BytesIO(response.content))
        
        # resize logo
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
                
            x = -300 + offset
            nX = 800 - x
            
            if self.invert_direction:
                temp = x
                x = nX
                nX = temp
            
            offset += stepSize
            
            draw.text((400, 20), "@" + self.githubname, (255, 255, 255), font=fontSmall, anchor="mm")
            
            im.paste(logo, (int(x - (newWidth / 2)), nameY - newHight - 50), logo)
            draw.text((nX, nameY), project['name'], (255, 255, 255), font=fontBig, anchor="mm")
            draw.text((x, nameY + 50), project['description'], (255, 255, 255), font=fontSmall, anchor="mm")
            self.images.append(im)
        
    def save(self):
        if self.output == '':
            return
        if not os.path.isfile(self.output):
            os.makedirs(os.path.dirname(self.output), exist_ok=True)
        self.images[0].save(self.output, save_all=True, append_images=self.images[1:], optimize=False, duration=self.duration, loop=0, disposal=2)
