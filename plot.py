#!/usr/bin/python

import matplotlib.pyplot as plt
import sys
import shlex


default_style = {'color':'black', 'mrkr':None, 'lnwd':1, 'lnstyle':'-'}
default_axis = [None]*4


class Plot:
	
	def __init__(self, iy, ix=None, ie=None, color=None, mrkr=None, lnwd=None, lnstyle=None, label=None):
		self.iy = iy
		self.ix = ix
		self.ie = ie
		self.color = color
		self.mrkr = mrkr
		self.lnwd = lnwd
		self.lnstyle = lnstyle
		self.label = label
	
	def shift(self, shift):
		self.ix, self.iy, self.ie = map(lambda i: i if i is None else i+shift, (self.ix, self.iy, self.ie))
	
	def plot(self):
		global data, default_style
		y0 = data[self.iy-1]
		if self.ix is None:
			x0 = range(len(data[0]))
		else:
			x0 = data[self.ix-1]
		if self.ie is None:
			x, y = zip(*[[dx, dy] for dx, dy in zip(x0,y0) if dx is not None and dy is not None])
		else:
			e0 = map(lambda d: 0. if d is None else d, data[self.ie-1])
			x, y, e = zip(*[[dx, dy, de] for dx, dy, de in zip(x0,y0,e0) if dx is not None and dy is not None])
		color = self.color or default_style['color']
		mrkr = self.mrkr or default_style['mrkr']
		lnwd = self.lnwd or default_style['lnwd']
		lnstyle = self.lnstyle or default_style['lnstyle']
		self.p, = plt.plot(x, y, linewidth=lnwd, linestyle=lnstyle, marker=mrkr, color=color, label=self.label)
		if self.ie is not None:
			plt.errorbar(x, y, yerr=e, linewidth=lnwd, marker=None, color=color)
		if self.label is not None:
			plt.legend()


_opened_files = set()

def parseFile(filename):
	
	def isNumber(a):
		try:
			float(a)
		except ValueError:
			return False
		else:
			return True
	
	global default_style, default_axis
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
				default_axis[0] = float(val)
			elif a == 'maxx':
				default_axis[1] = float(val)
			elif a == 'miny':
				default_axis[2] = float(val)
			elif a == 'maxy':
				default_axis[3] = float(val)
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
				ie = color = mrkr = lnwd = lnstyle = label = source = None
				for s in l:
					a = s.split('=')
					pn = a[0].strip()
					if pn == 'yerror':
						ie = int(a[1])
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
				plots.append(Plot(iy,ix,ie,color,mrkr,lnwd,lnstyle,label))
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

def saveFig(filename='fig.eps'):
	fig = plt.gcf()
	fig.set_size_inches(18,10)
	fig.savefig(filename, format=filename.split('.')[-1])

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
	
	x1, x2, y1, y2 = default_axis
	all_x = sum([[d for d in data[plot.ix-1] if d is not None] for plot in plots],[])
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
	
	if output_filename is None:
		showFig()
	else:
		saveFig(output_filename)
