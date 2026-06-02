#!/usr/bin/env python3

from configparser import ConfigParser
from tkinter import *
from PIL import Image, ImageTk, ImageFont, ImageDraw
from csv import DictReader, DictWriter
import os
import sys
import textwrap

HEIGHT_IDX = 1
WIDTH_IDX = 0


def is_image(filename):
    return os.path.isfile(filename) and filename.lower().endswith(".jpg")

class MainWindow:
    def __init__(self):
        self.config = ConfigParser()
        self.config.read_file(open('input/settings.ini'))
        print("===config===")
        for s in self.config.sections():
            for (i,v) in self.config.items(s):
                print(f"{s}/{i} = {v}")
        print("=====")

        self.blurb_pt = self.config.getint('default', 'blurb_pt')
        self.font_blurb = ImageFont.truetype(self.config.get('default', 'blurb_font'), self.blurb_pt)

        self.stats_pt = self.config.getint('default', 'stats_pt')
        self.font_stats = ImageFont.truetype(self.config.get('default', 'stats_font'), self.stats_pt)

        self.stats_2pt = 2*self.config.getint('default', 'stats_pt')
        self.font_2stats = ImageFont.truetype(self.config.get('default', 'stats_font'), self.stats_2pt)

        self.jnum_pt = self.config.getint('default', 'jnum_pt')
        self.font_jnum = ImageFont.truetype(self.config.get('default', 'jnum_font'), self.jnum_pt)

        self.fname_pt = self.config.getint('default', 'fname_pt')
        self.font_fname = ImageFont.truetype(self.config.get('default', 'jnum_font'), self.fname_pt)

        self.lname_pt = self.config.getint('default', 'lname_pt')
        self.font_lname = ImageFont.truetype(self.config.get('default', 'jnum_font'), self.lname_pt)

        self.vertical_template = Image.open('input/' + self.config.get('default', 'template_vertical'))
        self.horizontal_template = Image.open('input/' + self.config.get('default', 'template_horizontal'))
        self.template_back = Image.open('input/' + self.config.get('default', 'template_back'))

        self.jnum_pos = {
                'v': (self.config.getint('default', 'jnum_pos_v_x'), self.config.getint('default', 'jnum_pos_v_y')),
                'h': (self.config.getint('default', 'jnum_pos_h_x'), self.config.getint('default', 'jnum_pos_h_y')),
        }
        self.lname_pos = {
                'v': (self.config.getint('default', 'lname_pos_v_x'), self.config.getint('default', 'lname_pos_v_y')),
                'h': (self.config.getint('default', 'lname_pos_h_x'), self.config.getint('default', 'lname_pos_h_y')),
        }
        self.fname_pos = {
                'v': (self.config.getint('default', 'fname_pos_v_x'), self.config.getint('default', 'fname_pos_v_y')),
                'h': (self.config.getint('default', 'fname_pos_h_x'), self.config.getint('default', 'fname_pos_h_y')),
        }

        self.images = [f for f in os.listdir('input') if is_image('input/'+f)]

        self.roster = {}
        with open('input/roster.csv') as csvfile:
            reader = DictReader(csvfile)
            self.roster = {row['Jersey Number']: row for row in reader}

        self.jokes = []
        with open('input/jokes.csv') as csvfile:
            reader = DictReader(csvfile)
            self.jokes = [row for row in reader]

        self.image_meta = {}
        with open('input/images.csv') as csvfile:
            reader = DictReader(csvfile)
            self.image_meta = {row['Image']: row for row in reader}
        if len(self.image_meta) > 0:
            first_key = list(self.image_meta.keys())[0]
            if 'X Offset' not in self.image_meta[first_key]:
                for k in self.image_meta:
                    self.image_meta[k]['X Offset'] = None
            if 'Y Offset' not in self.image_meta[first_key]:
                for k in self.image_meta:
                    self.image_meta[k]['Y Offset'] = None
            if 'Scale' not in self.image_meta[first_key]:
                for k in self.image_meta:
                    self.image_meta[k]['Scale'] = 1
            if 'Orientation' not in self.image_meta[first_key]:
                for k in self.image_meta:
                    self.image_meta[k]['Orientation'] = 'v'
        for filename in self.images:
            if filename not in self.image_meta:
                self.image_meta[filename] = {
                    'Image': filename,
                    'Jersey Number': None,
                    'X Offset': None,
                    'Y Offset': None,
                    'Scale': 1,
                    'Orientation': 'v',
                }
        for k in self.image_meta:
            if self.image_meta[k]['Jersey Number'] == '':
                self.image_meta[k]['Jersey Number'] = None
            if self.image_meta[k]['X Offset'] == '':
                self.image_meta[k]['X Offset'] = None
            if self.image_meta[k]['Y Offset'] == '':
                self.image_meta[k]['Y Offset'] = None

        self.root = Tk()

        # Poker card size
        # Poker size card template
        # 2.48" x 3.46"(full bleed of 2.72"x3.7") at 300DPI
        #
        # Safe Area Line
        # (2.28x3.27 inches(safe)/684x981 pixels in 300DPI)
        # Keep text and other important part of your design INSIDE the safe area.
        #
        # Cut Area Line
        # (2.48x3.46 inches(safe)/744x1038 pixels in 300DPI)
        # Finished dimensions of your design after cut.
        #
        # Bleed Line
        # (2.72x3.7 inches(safe)/816x1110 pixels in 300DPI)
        # Extend your design fully through this area to avoid the chance of any white lines appearing.

        self.width = 2.72
        self.height = 3.7
        self.aspect_ratio = self.width / self.height

        self.bleed_width = 2.72
        self.bleed_height = 3.7

        self.cut_width = 2.48
        self.cut_height = 3.46

        self.safe_width = 2.28
        self.safe_height = 3.27

        self.back_bleed_width = 2.72
        self.back_bleed_height = 3.7
        self.back_width = 2.72
        self.back_height = 3.7
        self.back_cut_width = 2.48
        self.back_cut_height = 3.46
        self.back_safe_width = 2.28
        self.back_safe_height = 3.27

        self.shift_flag = False
        self.ctrl_flag = False


        self.print_dpi = 300
        self.screen_dpi = 190

        self.back_cwidth = int(float(self.width * self.screen_dpi))
        self.back_cheight = int(float(self.height * self.screen_dpi))
        self.cwidth = int(float(self.width * self.screen_dpi))
        self.cheight = int(float(self.height * self.screen_dpi))
        self.orientation = 'v'
        self.template_overlay = self.vertical_template.resize((int(self.bleed_width * self.screen_dpi), int(self.bleed_height * self.screen_dpi)))

        self.canvas = Canvas(
            self.root,
            width=self.cwidth,
            height=self.cheight,
        )
        self.canvas.pack(side=LEFT)

        self.back_canvas = Canvas(
            self.root,
            width=self.cwidth,
            height=self.cheight,
        )
        self.back_canvas.pack(side=RIGHT)

        self.back_img = self.template_back.resize((int(self.back_cut_width * self.screen_dpi), int(self.back_cut_height * self.screen_dpi)))

        self.img = None
        self.pimg = None
        self.cimg = self.canvas.create_image(
            0,
            0,
            anchor=NW,
            image=self.pimg
        )

        self.back_pimg = ImageTk.PhotoImage(self.back_img)
        self.back_cimg = self.back_canvas.create_image(
            0,
            0,
            anchor=NW,
            image=self.back_pimg,
        )

        self.offset_x = None
        self.offset_y = None
        self.scale = 1

        self.filename_label = Label(self.root, text="")
        self.filename_label.pack(side=BOTTOM)

        first_key = list(self.image_meta.keys())[0]
        self.load_img(first_key)
        self.draw_img()


        self.root.bind("<KeyPress>", self.keypress_handler)
        self.root.bind("<KeyRelease>", self.keyrelease_handler)

    def count_table(self):
        counts = {}
        longest_fname = 0
        longest_lname = 0
        for (jnum, r) in self.roster.items():
            if len(r['First Name']) > longest_fname:
                longest_fname = len(r['First Name'])
            if len(r['Last Name']) > longest_lname:
                longest_lname = len(r['Last Name'])

            counts[jnum]={'v': 0,
                          'h': 0,
                          }
            for (k,v) in self.image_meta.items():
                if v['Jersey Number'] == jnum:
                    counts[jnum][v['Orientation']] += 1

        for (jnum, v) in self.roster.items():
            fname = v['First Name'].ljust(longest_fname)
            lname = v['Last Name'].ljust(longest_lname)
            print(f"{jnum:2} | {fname} | {lname} | {counts[jnum]['v']} | {counts[jnum]['h']}")

    def load_img(self, filename, show_table=True):
        if show_table:
            self.count_table()

        self.current_file = filename
        self.filename_label.config(text=self.current_file)

        print(f"loading {self.current_file}")
        if self.current_file not in self.image_meta:
            print(f"{self.current_file} not in input/images.cv")
            return
        imeta = self.image_meta[self.current_file]

        #print(f"{imeta=}")
        if imeta['Jersey Number'] is not None and imeta['Jersey Number'] not in self.roster:
            print(f"image {self.current_file} has jersey number {imeta['Jersey Number']}, but that is not in input/roster.csv")
            return

        self.oimg = Image.open('input/' + self.current_file)
        self.orientation = imeta['Orientation']
        self.scale = float(imeta['Scale'])
        if self.scale < 0.1:
            self.scale = 1

        self.set_orientation()

        aspr = self.oimg.size[WIDTH_IDX] / self.oimg.size[HEIGHT_IDX]

        if aspr > self.aspect_ratio:
            self.width = int(float(self.oimg.size[HEIGHT_IDX] * self.aspect_ratio))
            self.height = self.oimg.size[HEIGHT_IDX]
        else:
            self.width = self.oimg.size[WIDTH_IDX]
            self.height = int(float(self.oimg.size[WIDTH_IDX] / self.aspect_ratio))

        self.offset_x = imeta['X Offset']
        if self.offset_x is None:
            self.offset_x = (self.oimg.size[WIDTH_IDX] - self.width) // 2
        self.offset_x = int(float(self.offset_x))

        self.offset_y = imeta['Y Offset']
        if self.offset_y is None:
            self.offset_y = (self.oimg.size[HEIGHT_IDX] - self.height) // 2
        self.offset_y = int(float(self.offset_y))


        self.jnum = imeta['Jersey Number']

        self.text_state = None

        cropto = (
                int(float(self.offset_x)), 
                int(float(self.offset_y)),
                int(float(self.offset_x + (self.scale * self.width))),
                int(float(self.offset_y + (self.scale * self.height))),
                )

    def set_orientation(self):
        if self.orientation == 'v':
            if self.cwidth > self.cheight:
                self.aspect_ratio = 1/self.aspect_ratio
                (self.cut_height, self.cut_width) = self.cut_width, self.cut_height
                (self.bleed_height, self.bleed_width) = self.bleed_width, self.bleed_height
                (self.safe_height, self.safe_width) = self.safe_width, self.safe_height
                (self.height, self.width) = self.width, self.height
                (self.cheight, self.cwidth) = self.cwidth, self.cheight
                self.canvas.config(width=self.cwidth, height=self.cheight)
                self.template_overlay = self.vertical_template.resize((int(self.bleed_width * self.screen_dpi), int(self.bleed_height*self.screen_dpi)))
        else:
            if self.cwidth < self.cheight:
                self.aspect_ratio = 1/self.aspect_ratio
                (self.cut_height, self.cut_width) = self.cut_width, self.cut_height
                (self.bleed_height, self.bleed_width) = self.bleed_width, self.bleed_height
                (self.safe_height, self.safe_width) = self.safe_width, self.safe_height
                (self.height, self.width) = self.width, self.height
                (self.cheight, self.cwidth) = self.cwidth, self.cheight
                self.canvas.config(width=self.cwidth, height=self.cheight)
                self.template_overlay = self.horizontal_template.resize((int(self.bleed_width * self.screen_dpi), int(self.bleed_height * self.screen_dpi)))

    def draw_img(self):
        self.set_orientation()

        sw = self.safe_width * self.screen_dpi
        sh = self.safe_height * self.screen_dpi
        swo_x = int((self.cwidth - sw) / 2)
        swo_y = int((self.cheight - sh) / 2)

        cw = self.cut_width * self.screen_dpi
        ch = self.cut_height * self.screen_dpi
        cwo_x = int((self.cwidth - cw) / 2)
        cwo_y = int((self.cheight - ch) / 2)

        back_sw = self.back_safe_width * self.screen_dpi
        back_sh = self.back_safe_height * self.screen_dpi
        back_swo_x = int((self.back_cwidth - back_sw) / 2)
        back_swo_y = int((self.back_cheight - back_sh) / 2)

        back_cw = self.back_cut_width * self.screen_dpi
        back_ch = self.back_cut_height * self.screen_dpi
        back_cwo_x = int((self.back_cwidth - back_cw) / 2)
        back_cwo_y = int((self.back_cheight - back_ch) / 2)

        idx = list(self.image_meta.keys()).index(self.current_file)

        cropto = (
                int(float(self.offset_x)), 
                int(float(self.offset_y)),
                int(float(self.offset_x + (self.scale * self.width))),
                int(float(self.offset_y + (self.scale * self.height))),
        )
        self.img = self.oimg.crop(cropto)
        self.img = self.img.resize((self.cwidth, self.cheight))
        self.img.paste(self.template_overlay, (0,0), self.template_overlay)

        self.back_img = Image.new('RGB', (self.back_cwidth, self.back_cheight), color='white')
        self.template_back = self.template_back.resize((self.back_cwidth, self.back_cheight))
        self.back_img.paste(self.template_back, (0, 0), self.template_back)

        self.dimg = ImageDraw.Draw(self.img)
        self.back_dimg = ImageDraw.Draw(self.back_img)
        if self.jnum is not None:
            text_color = (0xcc,0xb0,0x1e)

            font = self.font_jnum
            ysize = self.jnum_pt
            lines = [self.jnum]

            if self.roster[self.jnum]['Position'] != '':
                lines = self.roster[self.jnum]['Position'].split(' ')
                font = self.font_fname
                ysize = self.fname_pt

            for (i,jnum) in enumerate(lines):
                jnum_x = self.jnum_pos[self.orientation][0]
                jnum_width = self.dimg.textlength(jnum, font=font)
                jnum_x -= jnum_width
                self.dimg.text((jnum_x, self.jnum_pos[self.orientation][1] + ((i)*ysize)), jnum, fill=text_color, font=font)

            if self.jnum in self.roster:
                fname = self.roster[self.jnum]['First Name']
                lname = self.roster[self.jnum]['Last Name'].upper()
                self.dimg.text(self.fname_pos[self.orientation], fname, fill=text_color, font=self.font_fname)
                self.dimg.text(self.lname_pos[self.orientation], lname, fill=text_color, font=self.font_lname)

                jnum_x=122
                jnum_width = self.dimg.textlength(self.jnum, font=self.font_jnum)
                jnum_x -= jnum_width/2

                self.back_dimg.text((jnum_x,90), self.jnum, fill=(0,0,0), font=self.font_jnum)

                self.back_dimg.text((210,40), fname, fill=(0,0,0), font=self.font_fname)
                self.back_dimg.text((210,70), lname, fill=(0,0,0), font=self.font_lname)
                
                r = self.roster[self.jnum]
                if r['School'] is not None and r['School'] != '':
                    self.back_dimg.text((210,110), f"School: {r['School']}", fill=(0,0,0), font=self.font_stats)
                if r['Height'] is not None and r['Height'] != '':
                    self.back_dimg.text((375,110), f"Ht: {r['Height']}", fill=(0,0,0), font=self.font_stats)
                if r['Throws'] is not None and r['Throws'] != '':
                    self.back_dimg.text((210,130), f"Throws: {r['Throws']}", fill=(0,0,0), font=self.font_stats)
                if r['Bats'] is not None and r['Bats'] != '':
                    self.back_dimg.text((375,130), f"Bats: {r['Bats']}", fill=(0,0,0), font=self.font_stats)
                if r['Walk Up Song'] is not None and r['Walk Up Song'] != '':
                    #self.back_dimg.text((190,170), "Walk-Up Song:", fill=(0,0,0), font=self.font_stats)
                    self.back_dimg.text((210,160), "♫ ", fill=(0,0,0), font=self.font_2stats)
                    self.back_dimg.text((235,160), r['Walk Up Song'], fill=(0,0,0), font=self.font_stats)
                    self.back_dimg.text((235,180), r['Walk Up Artist'], fill=(0,0,0), font=self.font_stats)

                W_width = self.dimg.textlength("W", font=self.font_blurb)
                max_line_len = self.back_cwidth // W_width * 1.5

                if r['Blurb'] != '' and r['Blurb'] is not None:
                    blurb_lines = [r['Blurb']]
                    for (i, line) in enumerate(blurb_lines):
                        newlines = textwrap.wrap(line, width=max_line_len)
                        blurb_lines[i] = newlines[0]
                        for (ii, nl) in enumerate(newlines[1:]):
                            blurb_lines.insert(i+ii+1, nl)

                    for (i, line) in enumerate(blurb_lines):
                        line_width = self.dimg.textlength(line, font=self.font_blurb)
                        x = (self.back_cwidth - line_width) // 2
                        self.back_dimg.text((x,220 + (i*self.blurb_pt)), line, fill=(0,0,0), font=self.font_blurb)

                joke = self.jokes[idx % len(self.jokes)]

                W_width = self.dimg.textlength("W", font=self.font_stats)
                max_line_len = self.back_cwidth // W_width

                joke_lines = [f"Q: {joke['Q']}", " ", f"A: {joke['A']}"]
                for (i, line) in enumerate(joke_lines):
                    newlines = textwrap.wrap(line, width=max_line_len)
                    if len(newlines) == 0:
                        newlines = [""]
                    joke_lines[i] = newlines[0]
                    for (ii, nl) in enumerate(newlines[1:]):
                        joke_lines.insert(i+ii+1, nl)

                min_x = self.back_cwidth
                text_color = (0xcc,0xb0,0x1e)
                for (i, line) in enumerate(joke_lines):
                    line_width = self.dimg.textlength(line, font=self.font_stats)
                    x = (self.back_cwidth - line_width) // 2
                    if x < min_x:
                        min_x = x

                circle_r = (len(joke_lines)+1)*self.stats_pt/2
                circle_x_l = min_x 
                circle_y = (600 - circle_r) 
                self.back_dimg.circle((circle_x_l, circle_y), circle_r, fill=(0,0, 0x80), outline=None)

                circle_x_r = self.back_cwidth - min_x 
                self.back_dimg.circle((circle_x_r, circle_y), circle_r, fill=(0,0, 0x80), outline=None)

                self.back_dimg.rectangle((circle_x_l, 600 - 2*circle_r, circle_x_r, 600), fill=(0,0,0x80), outline=None)

                self.back_dimg.polygon([
                    (410, 605), 
                    (circle_x_r, 600-circle_r), 
                    ((circle_x_l + circle_x_r) // 2, 600 - circle_r)
                ], fill=(0,0,0x80), outline=None)

                for (i, line) in enumerate(joke_lines):
                    line_width = self.dimg.textlength(line, font=self.font_stats)
                    x = (self.back_cwidth - line_width) // 2
                    if x < min_x:
                        min_x = x
                    self.back_dimg.text((x,600 - ((len(joke_lines)-i+0.5)*self.stats_pt)), line, fill=text_color, font=self.font_stats)

        self.dimg.text((0, 0), "Bleed area", font=self.font_stats)
        self.dimg.rectangle((swo_x, swo_y, self.cwidth - swo_x, self.cheight - swo_y), outline=(0,0,0), fill=None)
        self.dimg.text((swo_x, swo_y), "Safe line", font=self.font_stats)
        self.dimg.rectangle((cwo_x, cwo_y, self.cwidth - cwo_x, self.cheight - cwo_y), outline=(0,0,0), fill=None)
        self.dimg.text((cwo_x, cwo_y), "Cut line", font=self.font_stats)
        self.dimg.text((swo_x, swo_y+30), "Draft", font=self.font_2stats)

        self.back_dimg.text((0, 0), "Bleed area", font=self.font_stats, fill='black')
        self.back_dimg.rectangle((back_swo_x, back_swo_y, self.back_cwidth - swo_x, self.back_cheight - swo_y), outline=(0,0,0), fill=None)
        self.back_dimg.text((back_swo_x, back_swo_y), "Safe line", font=self.font_stats, fill='black')
        self.back_dimg.rectangle((cwo_x, cwo_y, self.back_cwidth - cwo_x, self.back_cheight - cwo_y), outline=(0,0,0), fill=None)
        self.back_dimg.text((back_cwo_x, back_cwo_y), "Cut line", font=self.font_stats, fill='black')
        self.back_dimg.text((back_swo_x, back_swo_y+30), "Draft", font=self.font_2stats, fill='black')


        if self.jnum is not None:
            self.back_img.convert('RGB').save('output/' + f"{self.jnum}_{idx}_back_{self.current_file}")
            self.img.save('output/' + f"{self.jnum}_{idx}_{self.orientation}_front_{self.current_file}")

        self.pimg = ImageTk.PhotoImage(self.img)
        self.back_pimg = ImageTk.PhotoImage(self.back_img)
        self.canvas.itemconfig(self.cimg, image=self.pimg)
        self.back_canvas.itemconfig(self.back_cimg, image=self.back_pimg)

    def save(self):
        if len(self.image_meta) <= 0:
            return

        self.image_meta[self.current_file] = {
            'Image': self.current_file,
            'Jersey Number': self.jnum,
            'X Offset': self.offset_x,
            'Y Offset': self.offset_y,
            'Scale': self.scale,
            'Orientation': self.orientation,
        }
        with open('input/images.csv', 'w') as csvfile:
            first_key = list(self.image_meta.keys())[0]
            fieldnames = self.image_meta[first_key].keys()
            writer = DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for v in self.image_meta.values():
                writer.writerow(v)

    def keypress_handler(self, event):
        #print(f"keypress {event.char=} {event.keysym=} {event.keycode=}")
        if event.keysym.startswith('Shift_'):
            self.shift_flag = True

    def keyrelease_handler(self, event):
        #print(f"keyrelease {event.char=} {event.keysym=} {event.keycode=}")
        if event.keysym.startswith('Shift_'):
            self.shift_flag = False
        elif event.keysym == 'q':
            sys.exit(0)
        elif event.keysym == "minus":
            self.scale *= 1.1
        elif event.keysym == "plus":
            self.scale /= 1.1
        elif event.keysym == 'Left':
            if self.shift_flag:
                self.offset_x += 50
            else:
                self.offset_x += 10
        elif event.keysym == 'Right':
            if self.shift_flag:
                self.offset_x -= 50
            else:
                self.offset_x -= 10
        elif event.keysym == 'Up':
            if self.shift_flag:
                self.offset_y += 50
            else:
                self.offset_y += 10
        elif event.keysym == 'Down':
            if self.shift_flag:
                self.offset_y -= 50
            else:
                self.offset_y -= 10
        elif event.keysym == 'r':
            self.scale = 1
            self.offset_x = 0
            self.offset_y = 0
        elif event.keysym == 's':
            self.save()
        elif event.keysym == 'a':
            for (k,imeta) in self.image_meta.items():
                self.load_img(k, show_table=False)
                self.draw_img()
        elif event.keysym == 'Next':
            self.save()
            keys = list(self.image_meta.keys())
            keys = list(self.image_meta.keys())
            cidx = keys.index(self.current_file)
            cidx += 1
            cidx %= len(keys)
            self.load_img(keys[cidx])
        elif event.keysym == 'Prior':
            self.save()
            keys = list(self.image_meta.keys())
            cidx = keys.index(self.current_file)
            cidx -= 1
            cidx %= len(keys)
            self.load_img(keys[cidx])
        elif event.keysym >= '0' and event.keysym <= '9':
            if self.jnum is None:
                self.jnum = event.keysym
            else:
                self.jnum += event.keysym
        elif event.keysym == 'BackSpace':
            if self.jnum is not None:
                self.jnum = self.jnum[0:-1]
            if self.jnum == '':
                self.jnum = None
        elif event.keysym == 'f':
            if self.orientation == 'v':
               self.orientation = 'h'
            else:
               self.orientation = 'v'
        elif event.keysym == 'slash':
            print("rotate")
            self.oimg = self.oimg.rotate(90)
            print(f"writing to {self.current_file}")
            self.oimg.save('input/' + self.current_file)
            self.load_img(self.current_file)
        self.draw_img()

mainwindow = MainWindow()
mainwindow.root.mainloop()
