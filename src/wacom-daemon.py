#! /usr/bin/python
# deps: python-gobject
# Daemon to switch tablet states when window focus changes
# By Chris Hughes (89dragon@gmail.com) 2011

import gobject
import os
import pickle
import time
from intuos4oled import Intuos4OLEDChanger
from x11windowevents import X11InputFocusChangeDetector
from filesystem import FileMonitor

class TabletConfigDaemon(gobject.GObject):
	def __init__(self):
		# Identify tablet
		self.USB_VENDOR = 0x056a
		self.USB_PRODUCT = 0x00b9
		
		# Settings
		self.settingsfile = os.path.expanduser('~') + '/.wacom-settings'
		
		gobject.GObject.__init__(self)
		
		# Load X11 input focus
		self.xfcd = X11InputFocusChangeDetector()
		self.xfcd.connect('focus-changed', self.on_focus_changed)
		
		# Load OLED interface
		self.iOLED = Intuos4OLEDChanger(self.USB_VENDOR, self.USB_PRODUCT)
		
		# Detect device
		self.detect_device()
		
		# Load and apply settings
		self.reload_settings()

		# Connect filesystem watcher to check for settings file changes
		self.fileevent = FileMonitor(self.settingsfile)
		self.fileevent.connect("event", self.reload_settings)
		self.fileevent.open()
		
	def reload_settings(self, a=None, b=None, c=None):
		self.save_defaults()
		try:
			self.settings = pickle.load(open(self.settingsfile, 'r'))
		except:
			print 'Creating default application profile'
			self.save_defaults()
			self.settings = pickle.load(open(self.settingsfile, 'r'))
		self.profile = self.settings[self.USB_VENDOR]['profile']
		self.application_profiles = self.settings[self.profile]['application_profiles']
	
	def reload_driver(self):
		os.system('modprobe -r wacom')
		os.system('modprobe wacom')
		
	def save_settings(self, settings=None):
		if not settings: settings = self.settings
		pickle.dump(settings,open(self.settingsfile,'w'))
	
	def save_defaults(self):
		defaults = {}
		defaults[self.USB_VENDOR] = {}
		defaults[self.USB_VENDOR]['profile'] = 'Default'
		defaults['Default'] = {'application_profiles':{}}
		defaults['Default']['application_profiles'] = {
			'default':{'buttons':{	0:{'type':'text', 'text':'Unity', 'action':'keystroke', 'data':'meta'},
									1:{'type':'text', 'text':'Applications', 'action':'keystroke', 'data':'meta+a'},
									2:{'type':'text', 'text':'Files', 'action':'keystroke', 'data':'meta+f'},
									}},
			'nautilus':{'buttons':{	0:{'type':'text', 'text':'Cut', 'action':'keystroke', 'data':'lctrl+x'},
									1:{'type':'text', 'text':'Copy', 'action':'keystroke', 'data':'lctrl+c'},
									2:{'type':'text', 'text':'Paste', 'action':'keystroke', 'data':'lctrl+v'},
									3:{'type':'text', 'text':'Delete', 'action':'keystroke', 'data':'del'},
									4:{'type':'text', 'text':'Select\nAll', 'action':'keystroke', 'data':'lctrl+a'},
									5:{'type':'text', 'text':''},
									6:{'type':'text', 'text':''},
									7:{'type':'text', 'text':'Unity', 'action':'keystroke', 'data':'meta'},
									}},
			'gimp-2.6':{'buttons':{0:{'type':'text', 'text':'Back', 'action':'keystroke', 'data':'meta'}}},
			'inkscape':{'buttons':{0:{'type':'text', 'text':'Back', 'action':'keystroke', 'data':'meta'}}}
		}
		self.settings = defaults
		self.save_settings()
	
	def detect_device(self):
		print os.popen('xsetwacom --list devices').readlines()
		
	def on_focus_changed(self, obj, wmclass, wmname, wmgeom):
		print wmclass[0]
		if wmclass[0] in self.application_profiles: profile = wmclass[0]
		else: profile = 'default'
		self.set_profile(profile)
	
	def set_profile(self, profile_name):
		self.iOLED.open()
		profile = self.application_profiles[profile_name]
		for button in profile['buttons']:
			self.iOLED.set_image_from_text(button, profile['buttons'][button]['text'])
		self.iOLED.close()
		self.reload_driver()
		
if __name__ == "__main__":
	tcd = TabletConfigDaemon()
	loop = gobject.MainLoop()
	loop.run()
