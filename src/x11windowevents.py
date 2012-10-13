#! /usr/bin/python
# Class which runs on gobject/glib mainloop and returns signal if Xlib window input focus changes
# deps: python-xlib, python-gobject
# By Chris Hughes (89dragon@gmail.com) 2011

import Xlib.display
import gobject

class X11InputFocusChangeDetector(gobject.GObject):
	__gsignals__ = {"focus-changed" : (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT])}
	def __init__(self):
		gobject.GObject.__init__(self)
		self.cw_class = None
		self.display = Xlib.display.Display()
		gobject.timeout_add(300, self.poll)
	
	def poll(self):
		try:
			window = self.display.get_input_focus().focus
			wmname = window.get_wm_name()
			wmclass = window.get_wm_class()
			wmgeom = window.get_geometry()

			if wmclass is None and wmname is None:
				window = window.query_tree().parent
				wmname = window.get_wm_name()
				wmgeom = window.get_geometry()
				wmclass = window.get_wm_class()
			
			if self.cw_class != wmclass:
				self.cw_class = wmclass
				self.emit('focus-changed', wmclass, wmname, wmgeom)
		except:
			print 'Error encountered'
		
		return True
			
if __name__ == "__main__":
	def cl(obj, wmclass, wmname, wmgeom):
		print wmclass, wmname, wmgeom
		
	xfcd = X11InputFocusChangeDetector()
	xfcd.connect('focus-changed', cl)

	loop = gobject.MainLoop()
	loop.run()
