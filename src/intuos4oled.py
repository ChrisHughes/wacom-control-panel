#!/usr/bin/python
# Wacom Intuos 4 OLED driver
# deps: python-usb python-imaging python-cairo
# to continue using tablet after writing screens, you need to restart the driver with modprobe -r wacom && modprobe wacom
# By Chris Hughes (89dragon@gmail.com) 2011

import usb, array, Image, cairo

ICON_WIDTH = 64
ICON_HEIGHT = 32

class Intuos4OLEDChanger:
	def __init__(self, vendor_id, product_id):
		busses = usb.busses()
		self.handle = None
		count = 0
		for bus in busses:
		  devices = bus.devices
		  for dev in devices:
			if dev.idVendor==vendor_id and dev.idProduct==product_id:          
				self.dev = dev
				self.conf = self.dev.configurations[0]
				self.intf = self.conf.interfaces[0][0]
				self.endpoints = []
				for endpoint in self.intf.endpoints:
				  self.endpoints.append(endpoint)
				return

	def open(self):
		if self.handle:
		  self.handle = None
		self.handle = self.dev.open()
		try:self.handle.detachKernelDriver(0)
		except:pass
		self.handle.setConfiguration(self.conf)
		self.handle.claimInterface(self.intf)
		self.handle.setAltInterface(self.intf)
	
	def close(self):
		self.handle.releaseInterface()

	def set_transfer_mode(self, mode):
		buf = array.array('B', [0x21, mode])

		return self.handle.controlMsg(0x21, 0x09, buf, 0x0321);

	def downsample_icon_to_4_bit(self, data):
		buffer = []
		for y in range(ICON_HEIGHT / 2):
			for x in range(ICON_WIDTH):
				b1 = data[y*ICON_WIDTH*2 + ICON_WIDTH + (ICON_WIDTH-x-1)]
				b2 = data[y*ICON_WIDTH*2 + (ICON_WIDTH-x-1)]
				buffer += [(int((b1 / 255.0) * 15.0) << 4) + int((b2 / 255.0) * 15.0)]
		return array.array('B', buffer)

				
	def set_image(self, button, icon):
		data = self.downsample_icon_to_4_bit(icon)
		buf = array.array('B', ([0] * 259))
		if not self.set_transfer_mode(True): return False
		buf[0] = 0x23
		buf[1] = button
		for i in range(4):
			buf[2] = i
			for j in range(256):
				buf[3 + j] = data[256 * i + j];
			self.handle.controlMsg(0x21, 0x09, buf, 0x0323, 0);
		if not self.set_transfer_mode(False): return False

	def set_image_from_file(self, button, file):
		image=Image.open(file)
		greyscale_image = image.convert('L')
		greyscale_8bit = array.array('B', greyscale_image.tostring())
		self.set_image(button, greyscale_8bit)
	
	def set_image_from_text(self, button, text, font_family="Georgia", font_size=12, font_slant=cairo.FONT_SLANT_NORMAL, font_weight=cairo.FONT_WEIGHT_NORMAL, border=False, line_padding=3, antialiasing=cairo.ANTIALIAS_DEFAULT):
		data = array.array('B', [0] * 2048)
		stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_A8, ICON_WIDTH)
		image = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_A8, ICON_WIDTH, ICON_HEIGHT, stride)
		cr = cairo.Context(image)
		cr.set_source_rgba(1.0, 1.0, 1.0, 255.0)
		cr.select_font_face(font_family, font_slant, font_weight)
		cr.set_font_size(font_size)
		fo = cairo.FontOptions()
		fo.set_antialias(antialiasing)
		cr.set_font_options(fo)

		lines = text.split('\n')
		for y, line in enumerate(lines):
			x_bearing, y_bearing, width, height = cr.text_extents(line)[:4]
			#cr.move_to(0.5 - ICON_WIDTH / 2 - x_bearing, 0.5 - ICON_HEIGHT / 2 - y_bearing)
			cr.move_to(ICON_WIDTH / 2 - width / 2, ICON_HEIGHT / 2 + height / 2 + y*(height+line_padding) - (height/1.5)*(len(lines)-1))
			cr.show_text(line)
		if border:
			cr.move_to(0,0)
			cr.line_to(64,0)
			cr.line_to(64,32)
			cr.line_to(0,32)
			cr.line_to(0,0)
			cr.stroke()
		self.set_image(button, data)
        
if __name__=="__main__":
	USB_VENDOR = 0x056a
	USB_PRODUCT = 0x00b9
	d = Intuos4OLEDChanger(USB_VENDOR, USB_PRODUCT)
	d.open()
	#for i in range(8):
		#d.set_image_from_file(i, '/home/qb89dragon/Desktop/Untitled.png')
	d.set_image_from_text(0, 'Hi Nathan', font_slant=cairo.FONT_SLANT_ITALIC)
	d.set_image_from_text(1, 'I')
	d.set_image_from_text(2, 'Am', 'Rai', 20)
	d.set_image_from_text(3, 'Display\nToggle', 'Verdana', 11, antialiasing=cairo.ANTIALIAS_NONE, line_padding=0, border=True)
	d.set_image_from_text(4, 'Wacom', 'Trajan Pro', font_weight=cairo.FONT_WEIGHT_BOLD)
	d.set_image_from_text(5, 'Tablet', '911 Porscha', 10, antialiasing=cairo.ANTIALIAS_NONE)
	d.set_image_from_text(6, 'On')
	d.set_image_from_text(7, 'Ubuntu', 'Ubuntu', 15, font_weight=cairo.FONT_WEIGHT_BOLD, border=True)
