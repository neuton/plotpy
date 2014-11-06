#!/usr/bin/python

import matplotlib.pyplot as plt
import sys
import shlex


class Plot:
	
	def __init__(self, iy, ix=None, iex=None, iey=None, color=None, mrkr=None, lnwd=None, lnstyle=None, label=None):
		self.kwargs = {'linewidth':lnwd or 1, 'linestyle':lnstyle or '-', 'marker':mrkr, 'label':label}
		if color is not None:
			self.kwargs['color'] = color
		self.ix, self.iy, self.iex, self.iey = ix, iy, iex, iey
	
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
_opened_files = set()

def parseFile(filename):
	
	def isNumber(a):
		try:
			float(a)
		except ValueError:
			return False
		else:
			return True
	
	global _default_axis
	default_style = {'color':None, 'mrkr':None, 'lnstyle':None, 'lnwd':None}
	included_files, data, inc_data, plots, inc_plots = [], [], [], [], []
	
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
				l = shlex.split(val)
				if isNumber(l[1]):
					ix, iy = int(l[0]), int(l[1])
					l = l[2:]
				else:
					ix, iy = None, int(l[0])
					l = l[1:]
				color = default_style['color']
				mrkr = default_style['mrkr']
				lnwd = default_style['lnwd']
				lnstyle = default_style['lnstyle']
				iex = iey = label = source = None
				for s in l:
					a = s.split('=')
					pn = a[0].strip()
					if 'xerr' in pn:
						iex = int(a[1])
					elif 'yerr' in pn:
						iey = int(a[1])
					elif pn == 'color':
						color = a[1].strip()
					elif pn == 'marker':
						mrkr = a[1].strip()
					elif pn == 'linewidth':
						lnwd = float(a[1])
					elif pn == 'linestyle':
						lnstyle = a[1]
					elif pn == 'label':
						label = a[1]
					elif pn == 'source':
						source = a[1]
				shift = 0
				label = label or source
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
				plots.append(Plot(iy,ix,iex,iey,color,mrkr,lnwd,lnstyle,label))
				plots[-1].shift(shift)
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


def initFig():
	plt.gcf().patch.set_facecolor('white')
	#plt.grid(True, which="both", ls="-", color='gray')
	plt.minorticks_on()
	#plt.gca().tick_params(which='minor', bottom='on', labelbottom='on')
	#plt.setp(plt.gca().get_xticklabels(minor=True), visible=True)

def saveFig(filename):
	fig = plt.gcf()
	fig.set_size_inches(18,10)
	fig.savefig(filename)

def showFig():
	plt.show()


if __name__ == '__main__':
	
	initFig()
	
	args = sys.argv[1:]
	if '-o' in args:
		i = args.index('-o')
		output_filename = args[i+1]
		filenames = set(args[:i]+args[i+2:])
	else:
		output_filename = None
		filenames = set(args)
	if filenames == set():
		filenames = ['plot.txt']
	
	data, plots = [], []
	for f in filenames:
		ndata, nplots = parseFile(f)
		for plot in nplots:
			plot.shift(len(data))
		data += ndata
		plots += nplots
	
	if plots == []:
		plots = [Plot(i+1) for i in range(len(data))]
	
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
		plot.plot(data)
	
	if output_filename is None:
		showFig()
	else:
		saveFig(output_filename)
