#!/usr/bin/env python
#
# ThingDoc - things comment parser - http://thingdoc.org/
# Copyright (C) 2011 Josef Prusa <iam@josefprusa.cz>
# Copyright (C) 2011 Pavol Rusnak <stick@gk2.sk>
# See the file AUTHORS for all contributions
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

VERSION = '1.0'

import os
import re
import shutil
import sys
import time
from jinja2 import Environment, FileSystemLoader
from optparse import OptionParser


class Thing:

	def __init__(self):
		self.id = None          # unique id, root has id = 0 (numeric) which cannot be overriden
		self.name = None        # name of the thing
		self.common = False     # is this thing common?
		self.assembled = False  # is this thing assembled?
		self.category = ''      # category of the thing
		self.type = ''          # type of the thing (more detailed than category, e.g. RP, fastener, etc)
		self.step = []          # assembly instructions (aka steps)
		self.since = ''         # since when does the thing exist (can be YYYY-MM-DD or some tag, e.g. "Mendel")
		self.comment = []       # comments
		self.image = None       # thing image (filename with extension)
		self.using = {}         # dict of dependencies (id: cnt)
		self.price = None       # price of the thing (in $) - experimental
		self.weight = None      # weight of the thing (in grams) - experimental
		self.time = None        # how long does it take to assemble the part (in minutes) - experimental
		self.desc = []          # description of the thing


def escape_latex(value):
	if isinstance(value, str):
		value = value.replace('\\ ', '@textbackslash@ ').replace('\\', '\\textbackslash ').replace('@textbackslash@', '\\textbackslash\\')
		value = value.replace('^ ', '\\textasciicircum\\ ').replace('^', '\\textasciicircum ')
		value = value.replace('~ ', '\\textasciitilde\\ ').replace('~', '\\textasciitilde ')
		value = value.replace('| ', '\\textbar\\ ').replace('|', '\\textbar ')
		for i in ('$', '%', '_', '#', '{', '}', '&'):
			value = value.replace(i, '\\' + i)
		return value
	else:
		return value

class ThingDoc:
	
	parse_only_files = False;

	def parse(self, indir, outdir, imagedir):

		self.indir = indir
		self.outdir = outdir
		self.imagedir = imagedir

		self.start = time.strftime('%Y/%m/%d %H:%M:%S')
		self.datadir = os.path.dirname(os.path.abspath(__file__)) + '/data/'
		self.jinja = Environment(loader = FileSystemLoader(self.datadir))
		# register latex escaper
		self.jinja.filters['el'] = escape_latex

		self.tree = self.generate_tree()

		try:
			os.makedirs(self.outdir)
		except:
			pass
		try:
			os.chdir(self.outdir)
		except:
			self.fatal('Cannot switch to OUTDIR: %s' % self.outdir)

		self.check_tree()
		self.bom = self.extract_bom()
		self.instr = self.extract_instructions(1)


	def warning(self, string):
		print >> sys.stderr, 'Warning:', string


	def error(self, string):
		print >> sys.stderr, 'Error:', string


	def fatal(self, string):
		print >> sys.stderr, 'Fatal:', string
		sys.exit(1)


	def process_file(self, absname, things):

		try:
			f = open(absname, 'r')
		except IOError:
			self.fatal('Cannot open file %s' % absname)

		success = True
		thing = None
		linenum = 0
		for line in f:
			linenum += 1
			if line.startswith('/**'):
				if thing:
					self.error('Start of the comment (/**) found but the previous one is still open (%s:%d)' % (absname, linenum))
					success = False
				thing = Thing()
				continue
			if line.startswith(' */'):
				if not thing:
					self.error('End of the comment ( */) found but there is no previous open one (%s:%d)' % (absname, linenum))
					success = False
					continue
				if not thing.id:
					self.error('Missing mandatory attribute @id (%s:%d)' % (absname, linenum))
					success = False
				if not thing.name:
					self.error('Missing mandatory attribute @name (%s:%d)' % (absname, linenum))
					success = False
				if thing.id and thing.name:
					if thing.id in things:
						if thing.id == 1:
							self.fatal('More than one @root detected!')
						else:
							self.error("Duplicate thing id: '%s' (%s:%d)" % (thing.id, absname, linenum))
							success = False
					else:
						things[ thing.id ] = thing
				thing = None
				continue
			if not thing:
				continue  # not in a comment
			if not line.startswith(' * '):
				if line.rstrip() != ' *': # ignore lines ' *'
					self.error('Comment line does not start with a " * " (%s:%d)' % (absname, linenum))
					success = False
				continue
			(key, _, value) = line[3:].strip().partition(' ')
			if   key == '@id':
				thing.id = value
			elif key == '@name':
				thing.name = value
			elif key == '@root':
				thing.id = 1
			elif key == '@common':
				thing.common = True
			elif key == '@assembled':
				thing.assembled = True
			elif key == '@since':
				thing.since = value
			elif key == '@category':
				thing.category = value
			elif key == '@type':
				thing.type = value
			elif key == '@step':
				m = re.match('(.*)\[\[(.*)\]\]', value)
				if m:
					thing.step.append( {'text': m.group(1).strip(), 'img': m.group(2).strip()} )
				else:
					thing.step.append( {'text': value} )
			elif key == '@comment':
				thing.comment.append(value)
			elif key == '@image':
				thing.image = value
			elif key == '@using':
				(cnt, _, id) = value.partition(' ')
				try:
					cnt = int(cnt)
				except:
					id = cnt
					cnt = 1
				if id in thing.using:
					thing.using[id] += cnt
				else:
					thing.using[id] = cnt
			elif key == '@price':
				thing.price = float(value)
			elif key == '@weight':
				thing.weight = float(value)
			elif key == '@time':
				thing.weight = float(time)
			elif key.startswith('@'):
				self.error('Unknown tag %s (%s:%d)' % (key, absname, linenum))
				success = False
			else:
				if key:
					thing.desc.append((key + ' ' + value).strip())
		f.close()
		return success


	def generate_tree(self):
		things = {}
		for root, dirs, files in os.walk(os.path.abspath(self.indir)):
			dirs[:] = [d for d in dirs if not d.startswith('.')]
			for name in files:
				# skip if the file is not supported document
				
				if not os.path.splitext(name)[1] in ['.scad', '.tdoc']:
					continue
				if self.parse_only_files is not False:			
					if not name in self.parse_only_files:
						continue
				print name
				absname = os.path.join(root, name)
				self.process_file(absname, things)
		return things


	def check_tree(self):

		if not 1 in self.tree:
			self.fatal('Nothing was declared as @root')

		# do iterative BFS on dependency graph
		used = []
		missing = []
		queue = [1]
		while queue:
			thing = queue.pop()
			if not thing in self.tree.iterkeys():
				if not thing in missing:
					missing.append(thing)
				continue
			if not thing in used:
				used.append(thing)
				queue += self.tree[thing].using.keys()
			# do various alterations of items
			if os.path.exists('%s/%s.jpg' % (self.imagedir, thing)):
				self.tree[thing].image = '%s.jpg' % thing
			elif os.path.exists('%s/%s.png' % (self.imagedir, thing)):
				self.tree[thing].image = '%s.png' % thing

		# handle unused things
		for thing in self.tree.iterkeys():
			if not thing in used:
				self.warning("Thing '%s' is defined but unused" % thing)

		valid = True

		# handle undefined things
		for thing in missing:
			parents = []
			for k, v in self.tree.iteritems():
				if thing in v.using:
					parents.append(k == 1 and '@root' or ("'" + k + "'"))
			parents.sort()
			self.error("Thing '%s' is not defined and required by: %s" % (thing, ', '.join(parents)))
			valid = False

		# detect oriented cycles
		todo = self.tree.keys()
		while todo:
			node = todo.pop()
			stack = [node]
			while stack:
				top = stack[-1]
				for node in self.tree[top].using:
					if node in stack:
						self.error("Oriented cycle detected: '%s'" % ("' -> '".join(stack[stack.index(node):] + [node])))
						valid = False
						todo = []
						stack = []
						break
					if node in todo:
						stack.append(node)
						todo.remove(node)
						break
				else:
					node = stack.pop()

		if not valid:
			self.fatal('Tree validation failed, see errors above')


	def print_tree(self):

		# perform iterative DFS on tree
		queue = [(1, 0, -1)]
		while queue:
			(id, cnt, level) = queue.pop(0)
			if id == 1:
				print '@root', '(' + self.tree[id].name + ')'
			else:
				print level * '  ', '-', str(cnt) + 'x', self.tree[id].id, '(' + self.tree[id].name + ')'
			queue = map(lambda (id, cnt): (id, cnt, level + 1), self.tree[id].using.iteritems()) + queue


	def graphviz_tree(self):

		print 'digraph thingdoc {'
		print '\tnode [style=filled, colorscheme=pastel19];'
		print '\tedge [dir=back];'
		# perform iterative DFS on tree
		queue = [(1, 0, ['root'])]
		while queue:
			(id, cnt, path) = queue.pop(0)
			if id == 1:
				print '\t"root"[label="%s", fillcolor=9];' % self.tree[id].name
			else:
				name = self.tree[id].name
				if cnt > 1:
					name = '%dx %s' % (cnt, name)
				if self.tree[id].common:
					color = 1
				elif not self.tree[id].category:
					color = 8
				else:
					i = self.bom.keys().index(self.tree[id].category)
					color = (i % 6) + 2 # 2-7
				print '\t"%s"[label="%s", fillcolor=%d];' % ('/'.join(path), name, color)
				print '\t"%s" -> "%s";' % ('/'.join(path[:-1]), '/'.join(path))
			queue = map(lambda (id, cnt): (id, cnt, path + [id]), self.tree[id].using.iteritems()) + queue
		print '}'


	def extract_bom(self):

		# perform iterative BFS on tree
		queue = [ self.tree[1].using.items() ]
		bom = {}
		while queue:
			using = queue.pop(0)
			for (id, cnt) in using:
				thing = self.tree[id]
				if thing.category in bom:
					if id in bom[thing.category]:
						bom[thing.category][id] += cnt
					else:
						bom[thing.category][id] = cnt
				else:
					if thing.category:
						bom[thing.category] = {id: cnt}
				queue += [ map(lambda (a, b): (a, b*cnt), thing.using.items()) ]
		return bom


	def extract_instructions(self, id):

		# perform recursive DFS on tree
		instr = []
		for cid in self.tree[id].using:
			instr += self.extract_instructions(cid)
		if self.tree[id].step:
			instr.append( [id] + self.tree[id].step )
		return instr


	def generate_bom(self):

		try:
			f = open('bill-of-materials.txt', 'w')
		except:
			self.error('Cannot create bom.txt')
			return

		template = self.jinja.get_template('template.bom')
		f.write(template.render(title = self.tree[1].name, start = self.start, tree = self.tree, bom = self.bom))
		f.close()


	def generate_html(self):

		try:
			f = open('documentation.html', 'w')
		except:
			self.error('Cannot create documentation.html')
			return
		try:		
			os.mkdir('html_data')	
		except: 	
			pass

		# copy static files
		for i in ('facebox.css', 'facebox.js', 'iphone.css', 'jquery.js', 'jquery.cookie.js', 'logo.png', 'logo120.png', 'thingdoc.css', 'thingdoc.js'):
			shutil.copy(self.datadir + i, 'html_data/' + i)

		template = self.jinja.get_template('template.html')
		f.write(template.render(title = self.tree[1].name, unique="153431534841", titleimg = self.tree[1].image, titledesc = self.tree[1].desc, start = self.start, tree = self.tree, bom = self.bom, instr = self.instr, imagedir = self.imagedir))
		f.close()


	def generate_wiki(self):

		try:
			f = open('documentation.wiki', 'w')
		except:
			self.error('Cannot create documentation.wiki')
			return

		template = self.jinja.get_template('template.wiki')
		f.write(template.render(tree = self.tree, bom = self.bom))
		f.close()


	def generate_tex(self):

		try:
			f = open('documentation.tex', 'w')
		except:
			self.error('Cannot create documentation.tex')
			return

		# copy static files
		for i in ('logo.png', ):
			shutil.copy(self.datadir + i, i)

		template = self.jinja.get_template('template.tex')
		f.write(template.render(title = self.tree[1].name, titleimg = self.tree[1].image, titledesc = self.tree[1].desc, start = self.start, tree = self.tree, bom = self.bom, instr = self.instr, imagedir = self.imagedir))
		f.close()

parse_only_temp = False;

def parse_only(option, opt, value, parser):
	global parse_only_temp
	parse_only_temp = [i.split("/")[-1] for i in value.split(',')]
		
	
			

def main():
	parser = OptionParser(
		version = 'ThingDoc ' + VERSION,
		epilog = 'If none of --bom, --html, --tex, --wiki are provided then all 4 types are generated.')
	parser.add_option('-i', '--indir', dest = 'indir', default = '.', help = 'start scanning in INDIR directory (current by default)', metavar = 'INDIR')
	parser.add_option('-o', '--outdir', dest = 'outdir', default = 'docs', help = 'use OUTDIR as output directory ("docs" by default)', metavar = 'OUTDIR')
	parser.add_option('--imagedir', dest = 'imagedir', default = 'images', help = 'use IMAGEDIR directory (relative to OUTDIR) to look for images used in HTML and TeX ("images" by default)', metavar = 'IMAGEDIR')
	parser.add_option('-l', '--lint', dest = 'lint', default = None, help = 'check syntax in FILE and exit', metavar = 'FILE')
	parser.add_option('-b', '--bom', action = 'store_true', dest = 'bom', default = False, help = 'generate Bill of Materials')
	parser.add_option('-m', '--html', action = 'store_true', dest = 'html', default = False, help = 'generate HTML (markup) documentation')
	parser.add_option('-t', '--tex', action = 'store_true', dest = 'tex', default = False, help = 'generate TeX documentation')
	parser.add_option('-w', '--wiki', action = 'store_true', dest = 'wiki', default = False, help = 'generate Wiki documentation')
	parser.add_option('-p', '--print', action = 'store_true', dest = 'tree', default = False, help = 'print tree of things and exit (text mode)')
	parser.add_option('-g', '--graph', action = 'store_true', dest = 'graphviz', default = False, help = 'generate graphviz document')
	parser.add_option('-x', '--parse-only', type='string', action='callback', callback=parse_only)

	(options, _) = parser.parse_args()

	if not options.bom and not options.html and not options.tex and not options.wiki:
		options.bom = options.html = options.tex = options.wiki = True

	thingdoc = ThingDoc()
	thingdoc.parse_only_files = parse_only_temp

	if options.lint:
		if thingdoc.process_file(options.lint, {}):
			print 'No syntax errors detected'
			sys.exit(0)
		else:
			sys.exit(1)

	thingdoc.parse(options.indir, options.outdir, options.imagedir)

	if options.tree:
		thingdoc.print_tree()
		return

	if options.graphviz:
		thingdoc.graphviz_tree()
		return

	if options.bom:
		thingdoc.generate_bom()
	if options.html:
		thingdoc.generate_html()
	if options.tex:
		thingdoc.generate_tex()
	if options.wiki:
		thingdoc.generate_wiki()

	print 'All Done!'


if __name__ == '__main__':
	main()
