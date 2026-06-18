#!/usr/bin/env python3

from configparser import ConfigParser
from tkinter import *
from PIL import Image, ImageTk, ImageFont, ImageDraw
from csv import DictReader, DictWriter
import os
import sys
import textwrap
import subprocess
import shutil

HEIGHT_IDX = 1
WIDTH_IDX = 0


def is_image(filename):
    return os.path.isfile(filename) and filename.lower().endswith(".jpg")

class MainWindow:
    def __init__(self):
        self.load_config()
        self.last_cmd = None

        self.key_actions = [
        ]

        self.root = Tk()
        self.root.attributes('-zoomed', True)

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
        self.template_overlay = self.vertical_template.resize((int(self.bleed_width * self.print_dpi), int(self.bleed_height * self.print_dpi)))

        self.info_frame = Frame(self.root, width=15)
        self.info_frame.pack(side=LEFT)

        self.filename_label = Label(self.info_frame, text="")
        self.filename_label.pack(side=TOP)

        self.index_label = Label(self.info_frame, text="")
        self.index_label.pack(side=TOP)

        self.not_in_output_label = Label(self.info_frame, text="")
        self.not_in_output_label.pack(side=TOP)

        self.img_frame = Frame(self.root)
        self.img_frame.pack(side=RIGHT)

        self.cmd_box = Text(self.img_frame, height=1)
        self.cmd_box.bind('<Return>', self.process_cmd)
        self.cmd_box.pack(side=BOTTOM)

        self.canvas = Canvas(
            self.img_frame,
            width=self.cwidth,
            height=self.cheight,
        )
        self.canvas.pack(side=LEFT)

        self.back_canvas = Canvas(
            self.img_frame,
            width=self.cwidth,
            height=self.cheight,
        )
        self.back_canvas.pack(side=RIGHT)

        self.back_img = self.template_back.resize((int(self.back_cut_width * self.print_dpi), int(self.back_cut_height * self.print_dpi)))

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

        first_key = list(self.image_meta.keys())[0]
        self.load_img(first_key)
        self.draw_img()

        self.root.bind("<KeyPress>", self.keypress_handler)
        self.root.bind("<KeyRelease>", self.keyrelease_handler)


    def load_config(self):
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
            if 'Not in Output' not in self.image_meta[first_key]:
                for k in self.image_meta:
                    self.image_meta[k]['Not in Output'] = 'f'
            if 'Blurb' not in self.image_meta[first_key]:
                for k in self.image_meta:
                    self.image_meta[k]['Blurb'] = None
        for filename in self.images:
            if filename not in self.image_meta:
                self.image_meta[filename] = {
                    'Image': filename,
                    'Jersey Number': None,
                    'X Offset': None,
                    'Y Offset': None,
                    'Scale': 1,
                    'Orientation': 'v',
                    'Not in Output': 'f',
                    'Blurb': None,
                }
        for k in self.image_meta:
            print(self.image_meta[k])
            if self.image_meta[k]['Jersey Number'] == '':
                self.image_meta[k]['Jersey Number'] = None
            if self.image_meta[k]['X Offset'] == '':
                self.image_meta[k]['X Offset'] = None
            if self.image_meta[k]['Y Offset'] == '':
                self.image_meta[k]['Y Offset'] = None
            if self.image_meta[k]['Not in Output'] == '':
                self.image_meta[k]['Not in Output'] = 'f' 
            if self.image_meta[k]['Blurb'] == '':
                self.image_meta[k]['Blurb'] = None 

    def get_blurb(self):
        if self.jnum not in self.roster:
            return None
        r = self.roster[self.jnum]
        blurb = r['Blurb']
        if self.image_meta[self.current_file]['Blurb'] is not None:
            blurb = self.image_meta[self.current_file]['Blurb']
        return blurb

    def count_table(self):
        counts = {}
        count = 0

        for (jnum, r) in self.roster.items():
            counts[jnum]={'v': 0,
                          'h': 0,
                          't': 0,
                          }
            for (k,v) in self.image_meta.items():
                if v['Not in Output'] != 'f':
                    continue
                if v['Jersey Number'] == jnum:
                    counts[jnum][v['Orientation']] += 1
                    counts[jnum]['t'] += 1
                    count += 1

        return (counts, count)

    def print_count_table(self):
        (counts, count) = self.count_table()

        longest_fname = 0
        longest_lname = 0
        for (jnum, r) in self.roster.items():
            if len(r['First Name']) > longest_fname:
                longest_fname = len(r['First Name'])
            if len(r['Last Name']) > longest_lname:
                longest_lname = len(r['Last Name'])
        for (jnum, v) in self.roster.items():
            fname = v['First Name'].ljust(longest_fname)
            lname = v['Last Name'].ljust(longest_lname)
            print(f"{jnum:2} | {fname} | {lname} | {counts[jnum]['v']} | {counts[jnum]['h']} | {counts[jnum]['t']}")
        print(f"{count=}")

    def load_img(self, filename, show_table=True):
        if show_table:
            self.print_count_table()

        self.current_file = filename
        self.filename_label.config(text=self.current_file)
        self.index_label.config(text=f"?/{len(self.image_meta)-1}")

        if self.current_file not in self.image_meta:
            print(f"{self.current_file} not in input/images.cv")
            return
        imeta = self.image_meta[self.current_file]

        i = list(self.image_meta.keys()).index(self.current_file)
        self.index_label.config(text=f"{i}/{len(self.image_meta)-1}")
        print(f"loading {self.current_file} {i}/{len(self.image_meta)-1}")

        #print(f"{imeta=}")
        if imeta['Jersey Number'] is not None and imeta['Jersey Number'] not in self.roster:
            print(f"image {self.current_file} has jersey number {imeta['Jersey Number']}, but that is not in input/roster.csv")
            return
        nio = ""
        if self.image_meta[self.current_file]['Not in Output'] != 'f':
            nio = "Not in Output"
        self.not_in_output_label.config(text=nio)

        self.oimg = Image.open('input/' + self.current_file)
        self.orientation = imeta['Orientation']
        self.scale = float(imeta['Scale'])
        if self.scale < 0.1:
            self.scale = 1

        self.set_orientation()

        aspr = self.oimg.size[WIDTH_IDX] / self.oimg.size[HEIGHT_IDX]
        self.height = self.oimg.size[HEIGHT_IDX]
        self.width = self.oimg.size[WIDTH_IDX]

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
                self.template_overlay = self.vertical_template.resize((int(self.bleed_width * self.print_dpi), int(self.bleed_height*self.print_dpi)))
        else:
            if self.cwidth < self.cheight:
                self.aspect_ratio = 1/self.aspect_ratio
                (self.cut_height, self.cut_width) = self.cut_width, self.cut_height
                (self.bleed_height, self.bleed_width) = self.bleed_width, self.bleed_height
                (self.safe_height, self.safe_width) = self.safe_width, self.safe_height
                (self.height, self.width) = self.width, self.height
                (self.cheight, self.cwidth) = self.cwidth, self.cheight
                self.canvas.config(width=self.cwidth, height=self.cheight)
                self.template_overlay = self.horizontal_template.resize((int(self.bleed_width * self.print_dpi), int(self.bleed_height * self.print_dpi)))

    def draw_img(self):
        self.set_orientation()

        sw = self.safe_width * self.print_dpi
        sh = self.safe_height * self.print_dpi
        swo_x = int((self.bleed_width * self.print_dpi - sw) / 2)
        swo_y = int((self.bleed_height * self.print_dpi - sh) / 2)

        cw = self.cut_width * self.print_dpi
        ch = self.cut_height * self.print_dpi
        cwo_x = int((self.bleed_width * self.print_dpi - cw) / 2)
        cwo_y = int((self.bleed_height * self.print_dpi - ch) / 2)

        back_sw = self.back_safe_width * self.print_dpi
        back_sh = self.back_safe_height * self.print_dpi
        back_swo_x = int((self.back_bleed_width * self.print_dpi - back_sw) / 2)
        back_swo_y = int((self.back_bleed_height * self.print_dpi - back_sh) / 2)

        back_cw = self.back_cut_width * self.print_dpi
        back_ch = self.back_cut_height * self.print_dpi
        back_cwo_x = int((self.back_bleed_width * self.print_dpi - back_cw) / 2)
        back_cwo_y = int((self.back_bleed_height * self.print_dpi - back_ch) / 2)


        cropto = (
                int(float(self.offset_x)), 
                int(float(self.offset_y)),
                int(float(self.offset_x + (self.scale * self.width))),
                int(float(self.offset_y + (self.scale * self.height))),
        )
        self.img = self.oimg.crop(cropto)
        self.img = self.img.resize((int(self.bleed_width * self.print_dpi), int(self.bleed_height * self.print_dpi)))
        self.img.paste(self.template_overlay, (0,0), self.template_overlay)

        self.back_img = Image.new('RGB', (int(self.back_bleed_width * self.print_dpi), int(self.back_bleed_height * self.print_dpi)), color='white')
        self.template_back = self.template_back.resize(
                (int(self.back_bleed_width * self.print_dpi), int(self.back_bleed_height * self.print_dpi)))
        self.back_img.paste(self.template_back, (0, 0), self.template_back)

        self.dimg = ImageDraw.Draw(self.img)
        self.back_dimg = ImageDraw.Draw(self.back_img)
        if self.jnum is not None:
            text_color = (0xcc,0xb0,0x1e)

            font = self.font_jnum
            ysize = self.jnum_pt
            lines = [self.jnum]
            if self.jnum in ['T', 'T2']:
                lines = []

            if self.jnum not in self.roster:
                print(f"{self.jnum} not in roster")
            else:
                if self.roster[self.jnum]['Position'] != '':
                    lines = self.roster[self.jnum]['Position'].split(' ')
                    font = self.font_fname
                    ysize = self.fname_pt
                for (i,jnum) in enumerate(lines):
                    jnum_x = self.jnum_pos[self.orientation][0]
                    jnum_width = self.dimg.textlength(jnum, font=font)
                    jnum_x -= jnum_width
                    self.dimg.text((jnum_x, self.jnum_pos[self.orientation][1] + ((i)*ysize)), jnum, fill=text_color, font=font)
                fname = self.roster[self.jnum]['First Name']
                lname = self.roster[self.jnum]['Last Name'].upper()
                self.dimg.text(self.fname_pos[self.orientation], fname, fill=text_color, font=self.font_fname)
                self.dimg.text(self.lname_pos[self.orientation], lname, fill=text_color, font=self.font_lname)

                if self.jnum.isdigit():
                    jnum_x=196
                    jnum_width = self.dimg.textlength(self.jnum, font=self.font_jnum)
                    jnum_x -= jnum_width/2
                    self.back_dimg.text((jnum_x, 152), self.jnum, fill=(0,0,0), font=self.font_jnum)

                self.back_dimg.text((330,60), fname, fill=(0,0,0), font=self.font_fname)
                self.back_dimg.text((330,95), lname, fill=(0,0,0), font=self.font_lname)
                
                r = self.roster[self.jnum]
                if r['Position'] is not None and r['Position'] != '':
                    self.back_dimg.text((335,173), f"{r['Position']}", fill=(0,0,0), font=self.font_stats)
                elif r['School'] is not None and r['School'] != '':
                    self.back_dimg.text((335,173), f"School: {r['School']}", fill=(0,0,0), font=self.font_stats)
                if r['Throws'] is not None and r['Throws'] != '':
                    self.back_dimg.text((335,205), f"Throws: {r['Throws']}", fill=(0,0,0), font=self.font_stats)
                if r['Walk Up Song'] is not None and r['Walk Up Song'] != '':
                    #self.back_dimg.text((190,170), "Walk-Up Song:", fill=(0,0,0), font=self.font_stats)
                    self.back_dimg.text((330,252), "♫ ", fill=(0,0,0), font=self.font_2stats)
                    self.back_dimg.text((375,252), r['Walk Up Song'], fill=(0,0,0), font=self.font_stats)
                    self.back_dimg.text((375,284), r['Walk Up Artist'], fill=(0,0,0), font=self.font_stats)

                if r['Height'] is not None and r['Height'] != '':
                    self.back_dimg.text((582,173), f"Ht: {r['Height']}", fill=(0,0,0), font=self.font_stats)
                if r['Bats'] is not None and r['Bats'] != '':
                    self.back_dimg.text((582,205), f"Bats: {r['Bats']}", fill=(0,0,0), font=self.font_stats)


                blurb = r['Blurb']
                if self.image_meta[self.current_file]['Blurb'] is not None:
                    blurb = self.image_meta[self.current_file]['Blurb']
                blurb_font_path = self.config.get('default', 'blurb_font')
                blurb_w_ratio = 1.75
                if self.jnum == 'T' and self.image_meta[self.current_file]['Blurb'] is None:
                    if blurb == '' or blurb is None:
                        blurb = []
                        longest_name_len = 0
                        longest_p_len = 0
                        for jn in self.roster:
                            if jn not in ['T', 'A']:
                                n = len(f"{self.roster[jn]['First Name']} {self.roster[jn]['Last Name']}")
                                if n > longest_name_len:
                                    longest_name_len = n

                                p = self.roster[jn]['Position']
                                pn = len(jn)
                                if p != "" and p is not None:
                                    pn = len(p)
                                if pn > longest_p_len:
                                    longest_p_len = pn
                        longest_np_len = 0
                        for jn in self.roster:
                            if jn not in ['T', 'A']:
                                n = f"{self.roster[jn]['First Name']} {self.roster[jn]['Last Name']}".strip()
                                n = n.ljust(longest_name_len)

                                p = self.roster[jn]['Position']
                                if p != "" and p is not None:
                                    jn = p
                                jn = jn.rjust(longest_p_len)
                                np = f"{n} {jn}"
                                blurb.append(np)
                                if len(np) > longest_np_len:
                                    longest_np_len = len(np)
                        blurb2 = []
                        for i in range(0,len(blurb),2):
                            t = ""
                            if i + 1 != len(blurb):
                                t = f" | {blurb[i + 1]}"
                            t = t.rjust(longest_np_len)
                            o = blurb[i].ljust(longest_np_len)
                            blurb2.append(f"{o}{t}")
                        blurb = "\n".join(blurb2)
                        blurb_font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
                        blurb_w_ratio = 0.9

                if blurb != '' and blurb is not None:
                    for blurb_pt in range(self.blurb_pt, 8, -1):
                        font_blurb = ImageFont.truetype(blurb_font_path, blurb_pt)
                        W_width = self.dimg.textlength("W", font=font_blurb)
                        max_line_len = self.back_safe_width * self.print_dpi // W_width * blurb_w_ratio

                        blurb_lines = blurb.split("\n")
                        line_idx = 0
                        wrapped_lines = []
                        for line in blurb_lines:
                            newlines = textwrap.wrap(line, width=max_line_len)
                            if len(newlines) == 0:
                                newlines = [""]
                            wrapped_lines.extend(newlines)

                        if (len(wrapped_lines)*blurb_pt) >= 14*18:
                            continue

                        for (i, line) in enumerate(wrapped_lines):
                            line_width = self.dimg.textlength(line, font=font_blurb)
                            x = (self.back_bleed_width * self.print_dpi - line_width) // 2
                            self.back_dimg.text((x,350 + (i*self.blurb_pt)), line, fill=(0,0,0), font=font_blurb)
                        break

                joke_idx = 0
                for (imk,imv) in self.image_meta.items():
                    if imk == self.current_file:
                        break
                    if imv['Not in Output'] == 'f':
                        joke_idx += 1
                if joke_idx >= len(self.jokes):
                    print(f"Uh oh! For img={self.current_file=} {joke_idx=} and {len(self.jokes)=}. Reusing joke {joke_idx % len(self.jokes)}")
                joke_idx %= len(self.jokes)
                joke = self.jokes[joke_idx]

                W_width = self.dimg.textlength("W", font=self.font_stats)
                max_line_len = self.back_bleed_width * self.print_dpi // W_width

                joke_lines = [f"Q: {joke['Q']}", " ", f"A: {joke['A']}"]
                wrapped_joke_lines = []
                for line in joke_lines:
                    newlines = textwrap.wrap(line, width=max_line_len)
                    if len(newlines) == 0:
                        newlines = [""]
                    wrapped_joke_lines.extend(newlines)

                min_x = self.back_bleed_width * self.print_dpi
                text_color = (0xcc,0xb0,0x1e)
                for (i, line) in enumerate(wrapped_joke_lines):
                    line_width = self.dimg.textlength(line, font=self.font_stats)
                    x = (self.back_bleed_width * self.print_dpi - line_width) // 2
                    if x < min_x:
                        min_x = x

                circle_r = (len(wrapped_joke_lines)+1)*self.stats_pt/2
                circle_x_l = min_x 
                circle_y = (900 - circle_r) 
                self.back_dimg.circle((circle_x_l, circle_y), circle_r, fill=(0,0, 0x80), outline=None)

                circle_x_r = self.back_bleed_width * self.print_dpi - min_x 
                self.back_dimg.circle((circle_x_r, circle_y), circle_r, fill=(0,0, 0x80), outline=None)

                self.back_dimg.rectangle((circle_x_l, 900 - 2*circle_r, circle_x_r, 900), fill=(0,0,0x80), outline=None)

                self.back_dimg.polygon([
                    (650, 950), 
                    (circle_x_r, 900-circle_r), 
                    ((circle_x_l + circle_x_r) // 2, 900 - circle_r)
                ], fill=(0,0,0x80), outline=None)

                for (i, line) in enumerate(wrapped_joke_lines):
                    line_width = self.dimg.textlength(line, font=self.font_stats)
                    x = (self.back_bleed_width * self.print_dpi - line_width) // 2
                    if x < min_x:
                        min_x = x
                    self.back_dimg.text((x,900 - ((len(wrapped_joke_lines)-i+0.5)*self.stats_pt)), line, fill=text_color, font=self.font_stats)

        self.dimg.text((0, 0), "Bleed area", font=self.font_stats)

        self.dimg.rectangle((cwo_x, cwo_y, self.bleed_width * self.print_dpi - cwo_x, self.bleed_height * self.print_dpi - cwo_y), outline=(0,0,0), fill=None)
        self.dimg.text((cwo_x, cwo_y), "Cut line", font=self.font_stats)

        self.dimg.rectangle((swo_x, swo_y, self.bleed_width * self.print_dpi - swo_x, self.bleed_height * self.print_dpi - swo_y), outline=(0,0,0), fill=None)
        self.dimg.text((swo_x, swo_y), "Safe line", font=self.font_stats)
        self.dimg.text((swo_x, swo_y+30), "Draft", font=self.font_2stats)

        self.back_dimg.text((0, 0), "Bleed area", font=self.font_stats, fill='black')

        self.back_dimg.rectangle((back_swo_x, back_swo_y, self.back_bleed_width * self.print_dpi - swo_x, self.back_bleed_height * self.print_dpi - swo_y), outline=(0,0,0), fill=None)
        self.back_dimg.text((back_cwo_x, back_cwo_y), "Cut line", font=self.font_stats, fill='black')

        self.back_dimg.text((back_swo_x, back_swo_y), "Safe line", font=self.font_stats, fill='black')
        self.back_dimg.rectangle((cwo_x, cwo_y, self.back_bleed_width * self.print_dpi - cwo_x, self.back_bleed_height * self.print_dpi - cwo_y), outline=(0,0,0), fill=None)
        self.back_dimg.text((back_swo_x, back_swo_y+30), "Draft", font=self.font_2stats, fill='black')


        idx = list(self.image_meta.keys()).index(self.current_file)
        if self.jnum is not None:
            meta = self.image_meta[self.current_file]
            if meta['Not in Output'] == 'f':
                (fw,fh) = self.img.size
                (bw,bh) = self.back_img.size
                maxh = max(fh,bh)
                
                fbimg = Image.new('RGB', (fw+bw+5, max(fh,bh)))
                fbimg.paste(self.img, (0, (maxh - fh) // 2 ))
                fbimg.paste(self.back_img, (fw+5, (maxh - bh) // 2 ))

                fbimg.convert('RGB').save('output/' + f"{self.jnum}_{idx:02}_front_back.png")
                self.back_img.convert('RGB').save('output/' + f"{self.jnum}_{idx:02}_back.png")
                self.img.save('output/' + f"{self.jnum}_{idx:02}_front.png")

        self.img = self.img.resize((self.cwidth, self.cheight))
        self.back_img = self.back_img.resize((self.back_cwidth, self.back_cheight))

        self.pimg = ImageTk.PhotoImage(self.img)
        self.back_pimg = ImageTk.PhotoImage(self.back_img)
        self.canvas.itemconfig(self.cimg, image=self.pimg)
        self.back_canvas.itemconfig(self.back_cimg, image=self.back_pimg)

    def write_index(self):
        index_filename = "output/index.html"
        tmp_index_filename = f"{index_filename}~"
        with open(tmp_index_filename, "w+") as f:
            f.write("<html>\n")
            f.write("<head>\n")
            f.write("<style>\n")
            f.write("img {width: 100%;}\n")
            f.write("</style>\n")
            f.write("</head>\n")
            f.write("<body>\n\n")

            f.write("<table>\n")
            f.write("  <thead>\n")
            f.write("  <tr>\n")
            f.write("    <th>Jersey Number</th>\n")
            f.write("    <th>First Name</th>\n")
            f.write("    <th>Last Name</th>\n")
            f.write("    <th>Vertical</th>\n")
            f.write("    <th>Horizontal</th>\n")
            f.write("    <th>Total</th>\n")
            f.write("  </tr>\n")
            f.write("  </thead>\n")
            f.write("  <tbody>\n")

            (counts, count) = self.count_table()
            for (jnum, v) in self.roster.items():
                fname = v['First Name']
                lname = v['Last Name']
                f.write("    <tr>\n")
                f.write(f"      <td><a href=\"#jnum_{jnum}\">{jnum}</a></td>\n")
                f.write(f"      <td><a href=\"#jnum_{jnum}\">{fname}</a></td>\n")
                f.write(f"      <td><a href=\"#jnum_{jnum}\">{lname}</a></td>\n")
                f.write(f"      <td>{counts[jnum]['v']}</td>\n")
                f.write(f"      <td>{counts[jnum]['h']}</td>\n")
                f.write(f"      <td>{counts[jnum]['t']}</td>\n")
                f.write("    </tr>\n")

            f.write("    <tr>\n")
            f.write(f"      <td>Total</td>")
            f.write(f"      <td></td>")
            f.write(f"      <td></td>")
            f.write(f"      <td>{count}</td>")
            f.write(f"      <td></td>")
            f.write(f"      <td></td>")
            f.write("    </tr>\n")

            f.write("</table>\n")

            files = [x for x in enumerate(self.image_meta.items())]
            def sortfileskey(x):
                jnum = x[1][1]['Jersey Number']
                if jnum is not None:
                    if len(jnum) == 1:
                        if jnum.isdigit():
                            jnum = f"0{jnum}"
                        else:
                            jnum = f"{jnum}A"
                    return jnum
                return ""

            files=sorted(files, key=sortfileskey)
            byjersey = {}
            for (i, (iname, meta)) in files:
                jnum = meta['Jersey Number']
                if jnum not in byjersey:
                    byjersey[jnum] = []
                byjersey[jnum].append((i, iname))

            for jnum in byjersey:
                f.write(f"<div id=\"jnum_{jnum}\">\n")
                if jnum in self.roster:
                    f.write(f"<h2>{jnum} {self.roster[jnum]['First Name']} {self.roster[jnum]['Last Name']}</h2>")
                for (i, biname) in byjersey[jnum]:
                    # print(f"{jnum=} {i=} {biname=}")
                    meta = self.image_meta[biname]
                    if meta['Not in Output'] == 'f':
                        iname = f"{meta['Jersey Number']}_{i:02}_front_back.png"
                        f.write(f"<small>{i} {biname} {meta['Jersey Number']}</small>")
                        f.write(f"<a href=\"{iname}\">")
                        f.write(f"<img src=\"{iname}\">")
                        f.write("</a>\n")
                f.write("</div><hr>\n\n")

            f.write("</body>\n")
            f.write("</html>")
        shutil.move(tmp_index_filename, index_filename)

    def quit(self):
        self.save()
        sys.exit(0)

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
            'Not in Output': self.image_meta[self.current_file]['Not in Output'],
            'Blurb': self.image_meta[self.current_file]['Blurb']
        }

        images_csv_filename = 'input/images.csv'
        tmp_images_csv_filename = f"{images_csv_filename}~"
        with open(tmp_images_csv_filename, 'w') as csvfile:
            first_key = list(self.image_meta.keys())[0]
            fieldnames = self.image_meta[first_key].keys()
            writer = DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for v in self.image_meta.values():
                writer.writerow(v)
        shutil.move(tmp_images_csv_filename, images_csv_filename)
        self.write_index()

    def keypress_handler(self, event):
        #print(f"keypress {event.char=} {event.keysym=} {event.keycode=}")
        if event.keysym.startswith('Shift_'):
            self.shift_flag = True

    def keyrelease_handler(self, event):
        # print(f"keyrelease {self.shift_flag=} {event.char=} {event.keysym=} {event.keycode=}")
        # print(f"{event.widget=}")
        # print(f"{self.root.focus_get()=}")

        if self.root.focus_get() != self.root:
            return
        if event.keysym.startswith('Shift_'):
            self.shift_flag = False
        elif event.keysym == 'q':
            self.quit()
        elif event.keysym == "minus":
            self.scale *= 1.01
        elif event.keysym == "equal":
            self.scale /= 1.01
        elif event.keysym == "underscore":
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
        elif event.keysym == 'R':
            print("reload")
            print(f"{len(self.roster)=}")
            print(f"{len(self.image_meta)=}")
            self.load_config()
            print(f"{len(self.roster)=}")
            print(f"{len(self.image_meta)=}")
        elif event.keysym == 'r':
            self.scale = 1
            self.offset_x = 0
            self.offset_y = 0
        elif event.keysym == 's':
            self.save()
        elif event.keysym == 'N':
            self.cmd_box.delete("1.0", END)
            self.cmd_box.insert(END, self.last_cmd)
            self.process_cmd(event)
        elif event.keysym == 'n':
            if self.image_meta[self.current_file]['Not in Output'] != 't':
                self.image_meta[self.current_file]['Not in Output'] = 't'
            else:
                self.image_meta[self.current_file]['Not in Output'] = 'f'
            self.load_img(self.current_file)
        elif event.keysym == 'a':
            for (k,imeta) in self.image_meta.items():
                if imeta['Not in Output'] != 't':
                    self.load_img(k, show_table=False)
                    self.draw_img()
            self.save()
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
        elif event.keysym == 'numbersign':
            self.cmd_box.delete("1.0", END)
            self.cmd_box.insert(END, "idx ")
            self.cmd_box.focus()
        elif event.keysym == 'J':
            self.cmd_box.delete("1.0", END)
            self.cmd_box.insert(END, "jnum ")
            self.cmd_box.focus()
        elif event.keysym == 'e':
            subprocess.run(['rawtherapee', f"input/{self.current_file}"])
        else:
            print(f"keyrelease {self.shift_flag=} {event.char=} {event.keysym=} {event.keycode=}")
        self.draw_img()

    def process_cmd(self, event):
        self.last_cmd = self.cmd_box.get("1.0",END).strip()
        parts = self.cmd_box.get("1.0",END).strip().split(" ")
        parts = list(filter(lambda x:len(x) != 0, parts))

        if len(parts) > 0:
            if parts[0] == 'idx':
                if len(parts) == 2:
                    f = list(self.image_meta.keys())[int(parts[1])]
                    self.load_img(f)
                else:
                    print(f"idx requires 1 param. {parts=}")
            elif parts[0] == 'jnum':
                if len(parts) == 2:
                    filelist = list(self.image_meta.keys())
                    fidx = filelist.index(self.current_file)
                    fidx = (fidx + 1) % len(filelist)
                    found_fn = None
                    for fn in filelist[fidx:]:
                        meta = self.image_meta[fn]
                        if meta['Jersey Number'] == parts[1]:
                            found_fn = fn
                            break
                    if found_fn is None:
                        for fn in filelist[0:fidx]:
                            meta = self.image_meta[fn]
                            if meta['Jersey Number'] == parts[1]:
                                found_fn = fn
                                break
                    if found_fn is None:
                        print(f"jersey number {parts[1]} not found")
                    else:
                        self.load_img(found_fn)
                else:
                    print(f"jnum requires 1 param. {parts=}")

        self.cmd_box.delete("1.0", END)
        self.root.focus()

mainwindow = MainWindow()
mainwindow.root.mainloop()
