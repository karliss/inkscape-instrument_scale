#!/usr/bin/env python
# coding=utf-8
'''
Copyright (C)
2009 Sascha Poczihoski, sascha@junktech.de
Original author.

2013 Roger Jeurissen, roger@acfd-consultancy.nl
Added dangling labels and inside/outside scale features.

2015 Paul Rogalinski, pulsar@codewut.de
Adapted Inkscape 0.91 API changes.

2015 Bit Barrel Media, bitbarrelmedia -at- gmail dot com
-Changed UI and added the following features:
	Label offset. This will move the labels side to side and up/down.
	Option to use the center of a bounding box as the drawing reference.
	Ability to set line stroke width.
	Option to add a perpendicular line.
	Mathematical expression for the number format. For example, to divide the label number by 2, use "n/2".
	"Draw all labels" checkbox.
	Option to flip the label orientation.
	Support for "Draw every x lines" = 0 in order to remove lines.

2020 Neon22 github
- migrated to inkscape 1.0
- fixed font adjustments for flipping, inverting, etc
- fixed 360 degree circulars
- fixed centering on selected items
- added internal docs
- clarified UI, words, values
- improved groupings
- cleaned up params affected by units
- fixed perplines for invert
- help tab

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#for debugging:
message = "Debug: " + str(i) + "\n"
inkex.debug(message)
'''


import sys, math

import inkex
from simplestyle import *
from lxml import etree

class ScaleGen(inkex.Effect):

	def __init__(self):

		# Call the base class constructor.
		inkex.Effect.__init__(self)

		# Page 1 (Shape)
		self.arg_parser.add_argument('-u', '--unit',
			type = str, dest = 'unit', default = 'mm',
			help = 'Unit:')
		self.arg_parser.add_argument('-p', '--stype',
			type = str, dest = 'stype', default = 'circular',
			help = 'Type of Scale to draw')
		self.arg_parser.add_argument('--useref',
			type = inkex.Boolean, dest = 'useref', default = 'False',
			help = 'Reference is bounding box center')
		self.arg_parser.add_argument('--insidetf',
			type = inkex.Boolean, dest = 'insidetf', default = 'False',
			help = 'Draw lines above or below line')
		#
		self.arg_parser.add_argument('-b', '--external_length',
			type = float, dest = 'external_length', default = '100',
			help = 'Lengh of straight graph.')
		self.arg_parser.add_argument('--orientation',
			type = str, dest = 'orientation', default = '0',
			help = 'Major axis')
		self.arg_parser.add_argument('--radius',
			type = float, dest = 'radius', default = '100',
			help = 'Circular Scale Radius')
		self.arg_parser.add_argument('--originmark',
			type = inkex.Boolean, dest = 'originmark', default = 'True',
			help = 'Mark origin')
		self.arg_parser.add_argument('--scaleradbegin',
			type = float, dest = 'scaleradbegin', default = '0',
			help = 'Radial Start angle')
		self.arg_parser.add_argument('--scaleradcount',
			type = float, dest = 'scaleradcount', default = '90',
			help = 'Radial end angle')

		## Page 2 (Labels)
		self.arg_parser.add_argument('--drawalllabels',
			type = inkex.Boolean, dest = 'drawalllabels', default = 'True',
			help = 'Draw labels')
		self.arg_parser.add_argument('-f', '--scalefrom',
			type = int, dest = 'scalefrom', default = '0',
			help = 'Number from...')
		self.arg_parser.add_argument('-t', '--scaleto',
			type = int, dest = 'scaleto', default = '20',
			help = 'Number to...')
		self.arg_parser.add_argument('--mathexpression',
			type = str, dest = 'mathexpression', default = ' ',
			help = 'Math expression')
		self.arg_parser.add_argument('-c', '--reverse',
			type = inkex.Boolean, dest = 'reverse', default = 'False',
			help = 'Reverse order')
		#
		self.arg_parser.add_argument('-s', '--fontsize',
			type = float, dest = 'fontsize', default = '3',
			help = 'Font Height')
		self.arg_parser.add_argument('-i', '--suffix',
			type = str, dest = 'suffix', default = ' ',
			help = 'Appended to label')
		self.arg_parser.add_argument('--ishorizontal',
			type = inkex.Boolean, dest = 'ishorizontal', default = 'False',
			help = 'Horizontal labels')
		self.arg_parser.add_argument('--fliplabel',
			type = inkex.Boolean, dest = 'fliplabel', default = 'False',
			help = 'Flip orientation')
		# label offset
		self.arg_parser.add_argument('-x', '--labeloffseth',
			type = float, dest = 'labeloffseth', default = '0.0',
			help = 'Label offset in X')
		self.arg_parser.add_argument('-y', '--labeloffsetv',
			type = float, dest = 'labeloffsetv', default = '0.0',
			help = 'Label offset in Y')
		self.arg_parser.add_argument('--labeloffsetr',
			type = float, dest = 'labeloffsetr', default = '0.0',
			help = 'Radial Label offset')
			
		## Page 3 (Lines)
		self.arg_parser.add_argument("--perpline",
			type = inkex.Boolean, dest = "perpline", default=True,
			help = "Perpendicular line")
		self.arg_parser.add_argument('--perplinestrokewidth',
			type = float, dest = 'perplinestrokewidth', default = '0.2',
			help = 'Perpendicular line - Stroke width')
		self.arg_parser.add_argument('--perplineoffset',
			type = float, dest = 'perplineoffset', default = '0',
			help = 'Offset')
		#
		self.arg_parser.add_argument('-g', '--labellinelength',
			type = float, dest = 'labellinelength', default = '100',
			help = 'Length of main Label line')
		self.arg_parser.add_argument('--labellinestrokewidth',
			type = float, dest = 'labellinestrokewidth', default = '0.4',
			help = 'Stroke width of main Label line')
		self.arg_parser.add_argument('-m', '--mark0',
			type = int, dest = 'mark0', default = '10',
			help = 'Draw every Nth label line')
		#
		self.arg_parser.add_argument('-w', '--mark1wid',
			type = int, dest = 'mark1wid', default = '75',
			help = 'Length of Long lines')
		self.arg_parser.add_argument('--longlinestrokewidth',
			type = float, dest = 'longlinestrokewidth', default = '0.2',
			help = 'Long lines - Stroke width')
		self.arg_parser.add_argument('-n', '--mark1',
			type = int, dest = 'mark1', default = '5',
			help = 'Draw every Nth  Long line')
		#
		self.arg_parser.add_argument('-v', '--mark2wid',
			type = int, dest = 'mark2wid', default = '50',
			help = 'Short line: - Length (units): (\%):')
		self.arg_parser.add_argument('--shortlinestrokewidth',
			type = float, dest = 'shortlinestrokewidth', default = '0.2',
			help = 'Short line - Stroke width')
		self.arg_parser.add_argument('-o', '--mark2',
			type = int, dest = 'mark2', default = '1',
			help = 'Short line - Draw every x lines')

		#dummy for the doc tab - which is named
		self.arg_parser.add_argument("--tab",
			dest = "tab", default="use",
			help = "The selected UI-tab when OK was pressed")


	def add_numeric_label(self, n, x, y, group, fontsize, phi = 0.0):
		""" draw text at x,y location
			Phi is used to rotate text to line up in circular chart
		"""

		# swapped and horizontal
		if self.scaletype == 'straight' and self.insidetf and self.orientation=='V':
			self.labeloffsetv *= -1

		# swapped and vertical
		if self.scaletype == 'straight' and self.insidetf and self.orientation=='H':
			self.labeloffseth *= -1

		if self.drawalllabels:
			font_height_offset = 0
			if self.fliplabel:
				phi += 180
				font_height_offset = self.svg.unittouu(str(self.fontsize)+"mm")*0.9

			if not self.insidetf:
				font_height_offset -= self.svg.unittouu(str(self.fontsize)+"mm")

			if self.scaletype == 'straight':
				x = float(x) + self.labeloffseth
				y = float(y) - self.labeloffsetv - font_height_offset

			suffix = self.suffix  #.decode('utf-8') # fix ° (degree char)
			text = etree.SubElement(group, inkex.addNS('text','svg'))

			number = n;
			try:
				number = eval(self.mathexpression)
			except (ValueError, SyntaxError, NameError):
				pass

			text.text = str(number)+self.suffix
			cosphi=math.cos(math.radians(phi))
			sinphi=math.sin(math.radians(phi))
			a1 = str(cosphi)
			a2 = str(-sinphi)
			a3 = str(sinphi)
			a4 = str(cosphi)
			a5 = str((1-cosphi)*x-sinphi*y)
			a6 = str(sinphi*x+(1-cosphi)*y)
			#
			style = {'text-align' : 'center', 'text-anchor': 'middle', 'font-size': str(fontsize)}
			text.set('style', str(inkex.Style(style)))
			text.set('transform', 'matrix({0},{1},{2},{3},{4},{5})'.format(a1,a2,a3,a4,a5,a6))
			text.set('x', str(float(x)))
			text.set('y', str(float(y)))
			group.append(text)


	def add_straight_line(self, i, scalefrom, scaleto, group, grpLabel, type=2):
		""" Used for straight line graphs.
			add_numeric_label() is called from inside
		"""
		res = self.res

		direction = 1
		if self.insidetf:
			direction = -1

		# vertical
		if self.orientation == 'V':
			res *= -1

		label = False
		if self.reverse:
			# Count absolute i for labeling
			counter = 0
			for n in range(scalefrom, i):
				counter += 1
			n = scaleto-counter-1
		else:
			n = i

		#label line
		if type == 0:
			name = 'label_line'
			stroke = self.labellinestrokewidth
			line_style = { 'stroke': 'black',	'stroke-width': stroke }
			x1 = 0
			y1 = i*res
			x2 = self.labellinelength * direction
			y2 = i*res

			label = True

		#long line
		if type == 1:
			name = 'long_line'
			stroke = self.longlinestrokewidth
			line_style = { 'stroke': 'black', 'stroke-width': stroke }
			x1 = 0
			y1 = i*res
			x2 = self.labellinelength * self.mark1wid * direction
			y2 = i*res

		# short line
		name = 'short_line'
		if type == 2:
			stroke = self.shortlinestrokewidth
			line_style = { 'stroke': 'black', 'stroke-width': stroke }
			x1 = 0
			y1 = i*res
			x2 = self.labellinelength * self.mark2wid * direction
			y2 = i*res

		# perpendicular line
		if type == 3:
			name = 'perpendicular_line'
			stroke = self.perplinestrokewidth
			line_style = { 'stroke': 'black', 'stroke-width': stroke }

			#if stroke is in units, use this logic:
			strokeoffset = (self.labellinestrokewidth / 2)

			x1 = self.perplineoffset * direction
			x2 = self.perplineoffset * direction

			# vertical
			if self.orientation == 'V':
				y2 = ((scaleto-1)*res) - strokeoffset*2 # Top of vertical line
				y1 = ((scalefrom)*res) + strokeoffset   # bottom of Vertical line

			# horizontal
			else:
				y2 = ((scaleto-1)*res) + strokeoffset*2 # RHS of horiz line
				y1 = ((scalefrom)*res) - strokeoffset   # LHS of horiz line

		x1 = str(x1)
		y1 = str(y1)
		x2 = str(x2)
		y2 = str(y2)

		# horizontal
		if self.orientation == 'H':
			x1,y1 = y1,x1
			x2,y2 = y2,x2

		if label:
			self.add_numeric_label(n , x2, y2, grpLabel, self.fontsize)

		line_attribs = {'style' : str(inkex.Style(line_style)), inkex.addNS('label','inkscape') : name, 'd' : 'M '+x1+','+y1+' L '+x2+','+y2}
		line = etree.SubElement(group, inkex.addNS('path','svg'), line_attribs )


	def add_radial_line(self, i, scalefrom, scaleto, group, grpLabel, type=2, ishorizontal=True):
		""" Used to draw circular chart.
			add_numeric_label() called from inside
		"""
		height = self.labellinelength

		draw_label = False
		self.labeloffsetv *= -1 # text has upside down origin

		# Count absolute count for evaluation of increment
		count = 0
		for n in range(scalefrom, scaleto):
			count += 1
		countstatus = 0
		for n in range(scalefrom, i):
			countstatus += 1

		if self.reverse:
			counter = 0
			for n in range(scalefrom, i):
				counter += 1
			n = scaleto - counter -1
		else:
			n = i
		#
		inc = self.radcount / (count-1)
		irad = countstatus*inc
		irad = -1 * (self.radbegin+irad+180)
		
		#
		angled_text = 0
		if not ishorizontal:
			angled_text = 1
		inside = -1
		if not self.insidetf:
			inside = 1
		flipped = 0
		if not self.fliplabel:
			flipped = 1

		# label line
		if type==0:
			name = 'label line'
			stroke = self.labellinestrokewidth
			line_style = { 'stroke': 'black',	'stroke-width': stroke }
			x1 = math.sin(math.radians(irad))*self.radius
			y1 = math.cos(math.radians(irad))*self.radius
			x2 = math.sin(math.radians(irad))*(self.radius - inside*height)
			y2 = math.cos(math.radians(irad))*(self.radius - inside*height)

			draw_label = True

		# long line
		if type==1:
			name = 'long line'
			stroke = self.longlinestrokewidth
			line_style = { 'stroke': 'black', 'stroke-width': stroke }
			x1 = math.sin(math.radians(irad))*self.radius
			y1 = math.cos(math.radians(irad))*self.radius
			x2 = math.sin(math.radians(irad))*(self.radius - inside*height*self.mark1wid)
			y2 = math.cos(math.radians(irad))*(self.radius - inside*height*self.mark1wid)

		# short line
		if type==2:
			name = 'short line'
			stroke = self.shortlinestrokewidth
			line_style = { 'stroke': 'black', 'stroke-width': stroke }
			x1 = math.sin(math.radians(irad))*self.radius
			y1 = math.cos(math.radians(irad))*self.radius
			x2 = math.sin(math.radians(irad))*(self.radius - inside*height*self.mark2wid)
			y2 = math.cos(math.radians(irad))*(self.radius - inside*height*self.mark2wid)

		# perpendicular line
		if type==3:
			name = 'perpendicular line'
			stroke = self.perplinestrokewidth
			line_style = {'stroke': 'black', 'stroke-width' : stroke, 'fill': 'none'}

			rx = self.radius - inside*self.perplineoffset
			ry = rx

			#
			strokeoffset = math.atan((self.labellinestrokewidth / 2) / self.radius)

			start = math.radians(self.radbegin + 270) - strokeoffset
			end   = math.radians(self.radbegin + self.radcount + 270) + strokeoffset

			if self.radcount != 360:
				line_attribs = {'style':str(inkex.Style(line_style)),
					inkex.addNS('label','inkscape')        :name,
					inkex.addNS('cx','sodipodi')           :str(0),
					inkex.addNS('cy','sodipodi')           :str(0),
					inkex.addNS('rx','sodipodi')           :str(rx),
					inkex.addNS('ry','sodipodi')           :str(ry),
					inkex.addNS('start','sodipodi')        :str(start),
					inkex.addNS('end','sodipodi')          :str(end),
					inkex.addNS('open','sodipodi')         :'true',    #all ellipse sectors we will draw are open
					inkex.addNS('type','sodipodi')         :'arc',}
			else:
				line_attribs = {'style':str(inkex.Style(line_style)),
					inkex.addNS('label','inkscape')        :name,
					inkex.addNS('cx','sodipodi')           :str(0),
					inkex.addNS('cy','sodipodi')           :str(0),
					inkex.addNS('rx','sodipodi')           :str(rx),
					inkex.addNS('ry','sodipodi')           :str(ry),
					inkex.addNS('open','sodipodi')         :'true',    #all ellipse sectors we will draw are open
					inkex.addNS('type','sodipodi')         :'arc',}

		if type!=3: # everything excpet the perp line

			if draw_label:
				# if self.radcount==360: inkex.debug(str(n)+" "+str(self.scaleto))
				#if the circle count is 360 degrees, do not draw the last label because it will overwrite the first.
				if not (self.radcount==360 and n==self.scaleto-1):

					# complex adj to get text in right pos depending on flipped, angled, and insidetf
					font_height_offset = self.svg.unittouu(str(self.fontsize)+"mm")*1.0
					radial_offset = 0
					rotated_offset = self.labeloffsetr - font_height_offset
					vert_offset = self.labeloffsetv
					if self.fliplabel:
						radial_offset += font_height_offset
					else:
						rotated_offset += font_height_offset*2
					if not self.insidetf:
						radial_offset -= font_height_offset
					x2label = math.sin(math.radians(irad + self.labeloffseth)) * (self.radius - inside*height + radial_offset + angled_text*rotated_offset)
					y2label = math.cos(math.radians(irad + self.labeloffsetv)) * (self.radius - inside*height + radial_offset + angled_text*rotated_offset)
					self.add_numeric_label(n , x2label, y2label, grpLabel, self.fontsize, angled_text*(irad))

			# draw (excpet perp)
			x1 = str(x1)
			y1 = str(y1)
			x2 = str(x2)
			y2 = str(y2)
			line_attribs = {'style': str(inkex.Style(line_style)),	inkex.addNS('label','inkscape'): name, 'd' : 'M '+str(x1)+','+str(y1)+' L '+str(x2)+','+str(y2)}

		line = etree.SubElement(group, inkex.addNS('path','svg'), line_attribs )


	def skipfunc(self, i, markArray, groups):
		""" When to draw each tick mark.
			(Label, long, short)
		"""
		skip = True
		group = groups[0]
		linetype = 0

		if markArray[0] != 0:
			if (i % markArray[0])==0:
				linetype = 0	# the labeled line
				group = groups[0]
				skip = False

		if markArray[1] != 0 and skip:
			if (i % markArray[1])==0:
				linetype = 1 	# the long line
				group = groups[1]
				skip = False

		if markArray[2] != 0 and skip:
			if (i % markArray[2])==0:
				linetype = 2 	# the short line
				group = groups[2]
				skip = False

		return (skip, group, linetype)


### Main function
	def effect(self):
		# Values from UI corrected for units etc.
		self.unit      = self.options.unit
		self.scaletype = self.options.stype		# straight,circular
		self.useref    = self.options.useref	# bool
		self.insidetf  = self.options.insidetf	# bool
		#
		self.external_length = self.svg.unittouu(str(self.options.external_length)+self.unit)
		self.orientation     = self.options.orientation		# bool
		self.radius          = self.svg.unittouu(str(self.options.radius)+self.unit)
		self.originmark      = self.options.originmark		# bool
		self.radbegin        = self.options.scaleradbegin
		self.radcount        = self.options.scaleradcount
		#
		self.drawalllabels  = self.options.drawalllabels	# bool
		self.scalefrom      = self.options.scalefrom		# numeric start of scale
		self.scaleto        = self.options.scaleto			# numeric end of scale
		self.mathexpression = self.options.mathexpression
		self.reverse        =  self.options.reverse			# bool
		#
		self.fontsize     = self.svg.unittouu(str(self.options.fontsize)+"pt")	# all font calcs in pts
		self.suffix       = self.options.suffix
		self.ishorizontal = self.options.ishorizontal		# bool - are labels horizontal or curved in 'circular'
		self.fliplabel    = self.options.fliplabel			# bool - flip label upside down
		self.labeloffseth = self.svg.unittouu(str(self.options.labeloffseth)+self.unit)
		self.labeloffsetv = self.svg.unittouu(str(self.options.labeloffsetv)+self.unit)
		self.labeloffsetr = self.svg.unittouu(str(self.options.labeloffsetr)+self.unit)
		#
		self.perpline            = self.options.perpline	# bool
		self.perplinestrokewidth = self.svg.unittouu(str(self.options.perplinestrokewidth)+self.unit)
		self.perplineoffset      = self.svg.unittouu(str(self.options.perplineoffset)+self.unit)
		#
		self.labellinelength      = self.svg.unittouu(str(self.options.labellinelength)+self.unit)
		self.labellinestrokewidth = self.svg.unittouu(str(self.options.labellinestrokewidth)+self.unit)
		self.mark0                = self.options.mark0	# when labels appear
		#
		self.mark1wid            = self.options.mark1wid / 100
		self.longlinestrokewidth = self.svg.unittouu(str(self.options.longlinestrokewidth)+self.unit)
		self.mark1               = self.options.mark1	# when major tick marks appear
		#
		self.mark2wid             = self.options.mark2wid / 100
		self.shortlinestrokewidth = self.svg.unittouu(str(self.options.shortlinestrokewidth)+self.unit)
		self.mark2                = self.options.mark2	# when minor tick marks appear

		groups = ['0', '0', '0', '0']	# holds the svg groups for organising the tick marks, labels and perp line
		markArray = [self.mark0, self.mark1, self.mark2]	# to aid iterating when each tick line is drawn

		# Get access to main SVG document element and get its dimensions.
		doc = self.document.getroot()

		# Again, there are two ways to get the attributes:
		# width  = self.svg.unittouu(doc.get('width'))
		# height = self.svg.unittouu(doc.get('height'))

		# Put in in the centre of the current view
		centre = self.svg.namedview.center
		cx, cy = centre[0], centre[1]
		# OR use the selected elements to define the center
		if self.useref: # use center of selected element instead of doc.
			# get the bbox centers for each selected node
			bboxes = [node.bounding_box().center for node in self.svg.selected.values()]
			centers = [ (c.x,c.y) for c in bboxes] # turn vectors into lists
			# find average of all centers.
			if len(centers) > 0:
				cx = sum([c[0] for c in centers]) / len(centers)
				cy = sum([c[1] for c in centers]) / len(centers)

		# adjust for external length or radius
		if self.orientation == 'V' and self.scaletype == 'straight':
			cy += self.external_length/2
		if self.orientation == 'H' and self.scaletype == 'straight':
			cx -= self.external_length/2
		if self.scaletype == 'circular':
			cx -= self.radius/2
			cy += self.radius/2

		centre = (cx,cy)
		grp_transform = 'translate' + str( centre )
		
		# top level group
		grp_name = 'Instrument_scale'
		grp_attribs = {inkex.addNS('label','inkscape'):grp_name, 'transform':grp_transform }
		toplevel_group = etree.SubElement(self.svg.get_current_layer(), 'g', grp_attribs)

		# other line, label groups
		grp_name = 'Label_line'
		grp_attribs = {inkex.addNS('label','inkscape'):grp_name}
		groups[0] = etree.SubElement(toplevel_group, 'g', grp_attribs)

		if self.mark1 > 0:
			grp_name = 'Long line'
			grp_attribs = {inkex.addNS('label','inkscape'):grp_name}
			groups[1] = etree.SubElement(toplevel_group, 'g', grp_attribs)

		if self.mark2 > 0:
			grp_name = 'Short line'
			grp_attribs = {inkex.addNS('label','inkscape'):grp_name}
			groups[2] = etree.SubElement(toplevel_group, 'g', grp_attribs)

		if self.drawalllabels:
			grp_name = 'Labels'
			grp_attribs = {inkex.addNS('label','inkscape'):grp_name}
			groups[3] = etree.SubElement(toplevel_group, 'g', grp_attribs)

		# allow positive to negative counts
		if self.scalefrom < self.scaleto:
			self.scaleto += 1
		else:
			self.scaleto, self.scalefrom = self.scalefrom+1, self.scaleto
			
		# calc resolution scale factor from external length and the scale distance
		self.res = self.external_length / (self.scaleto - self.scalefrom - 1)

		if self.scaletype == 'straight':
			for i in range(self.scalefrom, self.scaleto):
				skip, group, type = self.skipfunc(i, markArray, groups)
				if not skip:
					# add_numeric_label is called from inside
					self.add_straight_line(i, self.scalefrom, self.scaleto, group, groups[3], type)
			# Perpendicular line
			if self.perpline:
				self.add_straight_line(0, self.scalefrom, self.scaleto, toplevel_group, groups[3], 3)

		elif self.scaletype == 'circular':
			for i in range(self.scalefrom, self.scaleto):
				skip, group, type = self.skipfunc(i, markArray, groups)
				if not skip:
					# add_numeric_label is called from inside
					self.add_radial_line(i, self.scalefrom, self.scaleto, group, groups[3], type, self.ishorizontal)

			# Perpendicular (circular) line
			if self.perpline:
				self.add_radial_line(0, self.scalefrom, self.scaleto, toplevel_group, groups[3], 3, self.ishorizontal)
			# Draw origin marker only for circular
			if self.originmark:

				grp_name = 'Radial center'
				grp_attribs = {inkex.addNS('label','inkscape'):grp_name}
				grp_originmark = etree.SubElement(toplevel_group, 'g', grp_attribs)

				stroke = self.shortlinestrokewidth
				origin_length = self.labellinelength * self.mark2wid/2
				line_style   = { 'stroke': 'black',	'stroke-width': stroke }
				line_attribs = {'style' : str(inkex.Style(line_style)),	inkex.addNS('label','inkscape') : 'name', 'd' : 'M '+str(origin_length)+','+str(origin_length)+' L '+str(-origin_length)+','+str(-origin_length)}
				line = etree.SubElement(grp_originmark, inkex.addNS('path','svg'), line_attribs )

				line_attribs = {'style' : str(inkex.Style(line_style)), inkex.addNS('label','inkscape') : 'name', 'd' : 'M '+str(-origin_length)+','+str(origin_length)+' L '+str(origin_length)+','+str(-origin_length)}
				line = etree.SubElement(grp_originmark, inkex.addNS('path','svg'), line_attribs )

###
if __name__ == '__main__':
	effect = ScaleGen()
	effect.run()
