#!/usr/bin/python

import matplotlib.pyplot as plt
import sys
import shlex
import getopt


class Data:
	pass

class Plot:
	
	def __init__(self, figure, iy, ix=None, iex=None, iey=None, source=None, kwargs={}):
		#label = label or source
		self.kwargs = {'linewidth':lnwd or 1, 'linestyle':lnstyle or '-', 'marker':mrkr, 'label':label}
		if color is not None:
			self.kwargs['color'] = color
		self.ix, self.iy, self.iex, self.iey = ix, iy, iex, iey
		shift = 0
		if source is not None:
			if source in _opened_files:
				raise Exception('Recursive inclusion!')
			if source in included_files:
				shift = sum(map(len, inc_data[:included_files.index(source)]))
			else:
				nd, np = parseFile(source)
				shift = sum(map(len, inc_data))
				for p in np:
					p.shift(shift)
				inc_data.append(nd)
				inc_plots += np
				included_files.append(source)
		self.shift(shift)
	
	def shift(self, shift):
		self.ix, self.iy, self.iex, self.iey = map(lambda i: i if i is None else i+shift, (self.ix, self.iy, self.iex, self.iey))
	
	def plot(self, data):
		y0 = data[self.iy-1]
		if self.ix is None:
			x0 = range(len(y0))
		else:
			x0 = data[self.ix-1]
		if self.iex is None:
			ex0 = [None]*len(x0)
		else:
			ex0 = map(lambda d: 0. if d is None else d, data[self.iex-1])
		if self.iey is None:
			ey0 = [None]*len(y0)
		else:
			ey0 = map(lambda d: 0. if d is None else d, data[self.iey-1])
		x, y, ex, ey = zip(*[[dx, dy, dex, dey] for dx, dy, dex, dey in zip(x0,y0,ex0,ey0) if dx is not None and dy is not None])
		if self.iex is not None:
			self.kwargs['xerr'] = ex
		if self.iey is not None:
			self.kwargs['yerr'] = ey
		self.p = plt.errorbar(x, y, **self.kwargs)
		if self.kwargs['label'] is not None:
			plt.legend(numpoints=1)


_default_axis = [None]*4
_included_files = []
_opened_files = set()

def isNumber(a):
	try:
		float(a)
	except ValueError:
		return False
	else:
		return True

def parsePlot(s):
	l = shlex.split(s)
	if isNumber(l[1]):
		ix, iy = int(l[0]), int(l[1])
		l = l[2:]
	else:
		ix, iy = None, int(l[0])
		l = l[1:]
	kwargs0 = {'marker':None, 'linewidth':1}
	kwargs = dict(a.split('=') for a in l)
	kwargs = {k: kwargs.get(k) or kwargs0.get(k) for k in set(kwargs0).union(kwargs)}
	return iy, ix, kwargs

def parseFile(filename):
	
	global _default_axis, _included_files
	data, inc_data, plots, inc_plots = [], [], [], []
	
	global _opened_files
	_opened_files.add(filename)
	
	with open(filename) as inputfile:
		for eachline in inputfile:
			splitted = eachline.split(':')
			a, val = splitted[0].strip().lower(), ':'.join(splitted[1:]).strip()
			if a == '' or a[0] == '#':
				pass
			elif a == 'title':
				plt.title(val)
			elif a == 'xlogscale':
				plt.xscale('log')
			elif a == 'ylogscale':
				plt.yscale('log')
			elif a == 'xlabel':
				plt.xlabel(shlex.split(val)[0])
			elif a == 'ylabel':
				plt.ylabel(shlex.split(val)[0])
			elif a == 'xylabel':
				xlabel, ylabel = shlex.split(val)
				plt.xlabel(xlabel)
				plt.ylabel(ylabel)
			elif a == 'minx':
				_default_axis[0] = float(val)
			elif a == 'maxx':
				_default_axis[1] = float(val)
			elif a == 'miny':
				_default_axis[2] = float(val)
			elif a == 'maxy':
				_default_axis[3] = float(val)
			elif a == 'color':
				default_style['color'] = val
			elif a == 'marker':
				default_style['mrkr'] = val
			elif a == 'linewidth':
				default_style['lnwd'] = val
			elif a == 'linestyle':
				default_style['lnstyle'] = val
			elif a == 'plot':
				plots.append(Plot(parsePlot(val)))
			elif a == 'include':
				for f in shlex.split(val):
					if f in _opened_files:
						raise Exception('Recursive inclusion!')
					if f not in included_files:
						nd, np = parseFile(f)
						shift = sum(map(len, inc_data))
						for p in np:
							p.shift(shift)
						inc_data.append(nd)
						inc_plots += np
						included_files.append(f)
			else:
				data.append(a.split())
	
	_opened_files.remove(filename)
	
	if data != []:
		dlen = max(map(len, data))
		data = zip(*map(lambda s: map(lambda a: float(a) if isNumber(a) else None, s) + [None]*(dlen-len(s)), data))
	
	shift = len(data)
	for p in inc_plots:
		p.shift(shift)
	
	return data + sum(inc_data,[]), plots + inc_plots


class Figure:
	
	def __init__(self, *filenames):
		plt.gcf().patch.set_facecolor('white')
		#plt.grid(True, which="both", ls="-", color='gray')
		plt.minorticks_on()
		#plt.gca().tick_params(which='minor', bottom='on', labelbottom='on')
		#plt.setp(plt.gca().get_xticklabels(minor=True), visible=True)
		self.data = []
		self.plots = []
		self.load(*filenames)
	
	def load(self, *filenames):
		for f in filenames:
			data, plots = parse_file(f)
			for plot in plots:
				plot.shift(len(self.data))
			self.data += data
			self.plots += plots
	
	def add_plots(self, *plots):
		self.plots += plots
	
	def draw(self):
		if self.plots == []:
			self.plots = [Plot(self, i+1) for i in range(len(self.data))]
		x1, x2, y1, y2 = _default_axis
		all_x = sum([[d for d in data[plot.ix-1] if d is not None] if plot.ix is not None else range(len(data[plot.iy-1])) for plot in plots],[])
		all_y = sum([[d for d in data[plot.iy-1] if d is not None] for plot in plots],[])
		x2 = x2 or max(all_x)
		x1 = x1 or min(all_x)
		y2 = y2 or max(all_y)
		y1 = y1 or min(all_y)
		xs = x2 - x1
		ys = y2 - y1
		plt.axis([x1-xs/20., x2+xs/20., y1-ys/20., y2+ys/20.])
		for plot in plots:
			plot.plot()
	
	def show(self):
		plt.show()
	
	def save(self, filename):
		fig = plt.gcf()
		fig.set_size_inches(18,10)
		fig.savefig(filename)


if __name__ == '__main__':
	
	args, filenames = getopt.getopt(sys.argv[1:], 'p:o:')
	if filenames == []:
		filenames = ['plot.txt']
	
	figure = Figure(*filenames)
	figure.add_plots(*[Plot(figure, parse_plot(s)) for o, s in args if o == '-p'])
	figure.draw()
	
	if '-o' not in zip(*args)[0]:
		figure.show()
	else:
		for o, f in args:
			if o == '-o':
				figure.save(f)
