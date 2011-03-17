# ThingDOC 
# things comment parser
# http://thingdoc.org/
# by Josef Prusa (josefprusa.cz)
# GNU GPL v2 or up
 
# Imports
import os, fileinput, string, sys, re


# Devides strings by chosen character
def divide(string, divs):
    for d in divs[1:]:
        string = string.replace(d, divs[0])
    return string.split(divs[0])

# Makes output safe fo LaTeX
def latexSafe(string):
	return string.replace("&", "\\&")

# Turns on debug mode	
debug = True

class Thing:
	def __init__(self): 
		# Name of the thing
		self.name = "" 
		# Unique link to thing
		self.link = "" 
		# Root thing for generating tree
		self.root = False
		# Category of the thing
		self.category = ""
		# Description of thing
		self.description = ""
		# Assembly info
		self.assembly = []
		# If thing is soo common
		self.common = False
		# Other things which this thing uses
		self.usedParts = []

# List of all things
things = []

# Link to root thing
rootThing = "";

# Command parser (insulated against whitespace)
def parseLine(line):
	m = re.search("\*\s*\@(\w+)\s(.*)", line)
	if(m != None):
		return { 'Command': m.group(1), 'Arg': m.group(2) }
	else:
		return { 'Command': None, 'Arg': None }

# Going thru directory
for root, dirs, files in os.walk(os.getcwd()):
	for name in files:
		filename = os.path.join(root, name)
		
		# We take only two kinds of files
		if (name.endswith(".scad") or name.endswith(".tdoc")):
			# Active file
			f = file(filename)
			
			# Debug msg
			if debug: print "Analyzing file: " + filename
			
			# Thing link
			link = divide(filename, ".")[0]
			link = divide(link, "/")
			link = link[len(link)-1]
			
			# Debug msg
			if debug: print "Automagically found thing link: " + link
			
			# Variable which tells us if we are in comment
			inComment = False
			# Set some extra variables
			lastLine = "regular"
			for line in f:
				thisLine = "regular"
				parsedLine = None
				
				if inComment is True:
					parsedLine = parseLine(line)
					if parsedLine['Command'] == 'name':
						#Thing name (-1 = remove nl character)
						name = parsedLine['Arg']
						#print name
						foundThing.name = name.strip()
						thisLine = "name"
					if parsedLine['Command'] == 'using':
						#Slice the line
						using = re.search('(\d)+\s+(.*)', parsedLine['Arg'])

						if(using != None):
							#Dig part name
							partName = using.group(2)
							#Append it to things
							foundThing.usedParts.append([str(partName).strip(), int(using.group(1))])
							thisLine = "using"
					if parsedLine['Command'] == 'link':
						# Thing link parsing
						foundLink = parsedLine['Arg']
						#Append it to things
						foundThing.link = foundLink.strip()
						thisLine = "link"
					if parsedLine['Command'] == 'assembly':
						# Thing link parsing
						assembly = parsedLine['Arg']
						#Append it to things
						foundThing.assembly.append(assembly)
						thisLine = "assembly"
					if parsedLine['Command'] == 'category':
						# Thing category
						category = parsedLine['Arg']
						#Append it to things
						foundThing.category = category
						thisLine = "category"
					# Common thing
					if parsedLine['Command'] == 'common':
						#Append it to things
						foundThing.common = True
						thisLine = "common"
					# Root thing
					if parsedLine['Command'] == 'root':
						#Append it to things
						foundThing.root = True
						rootThing = link
						thisLine = "root"
						#debug msg
						if debug: print "Found root thing: " + link + "(" + foundThing.name + ")"
				else:
					if '/**' in line:
						#Hooray we found comment
						inComment = True
						foundThing = Thing()
						foundThing.category = "Uncategorized"
						foundThing.link = link
				# Thing description
				if (thisLine == "regular") and (lastLine == "regular") and (inComment is True):
					#Find the string of description
					description  = line[3:len(line)-1]
					foundThing.description = foundThing.description+description
				if ('*/' in line) and (lastLine != "regular"):
					things.append(foundThing)
					inComment = False
				lastLine = thisLine
				
	
print "Starting to analyze parts from " + rootThing

# Dictionary where are stored parts counts (thing link is key)
partsCount = {}

# List of categories
categories = [""]

# List of items that have instructions, in an order that is assemblable.
# - Any part that requires another part should only appear after the required
#   parts have been output.
assemblyInstructions = []

# Looking for a thing by link if found returns it
def findThing(thingLink):
	for thing in things:
		if thing.link == thingLink:
			return thing


# Recursive parser of things
def parseTree(partLink):
	for thing in things:
		if thing.link == partLink:
			#print thing.name
			# Parse categories things etc
			if not(thing.category in categories):
				categories.append(thing.category)
			#Check if we have some parts
			partCount = len(thing.usedParts)
			if partCount > 0:
				for part in thing.usedParts:
					#Count of part
					count = part[1]
					#Check if we already has entry, if so, take it and add 1
					if partsCount.has_key(part[0]):
						count = partsCount[part[0]]+part[1]
					partsCount[part[0]] = count
					for i in range(0, part[1]):
						parseTree(part[0])
			instructionCount = len(thing.assembly)
			if(instructionCount > 0):
				if not(thing.link in assemblyInstructions):
					assemblyInstructions.append(thing.link)


# Parse things from root thing
parseTree(rootThing)

def replaceLinksWithNames(instruction):
	newInstruction = instruction
	for thing in things:
		newInstruction = string.replace(newInstruction, "[" + thing.link + "]", thing.name)
	return newInstruction
						
# Outputting TEX

output = ""
output += "\\documentclass[11pt]{article}\n\\usepackage[latin2]{inputenc}\n\\usepackage{a4wide}\n\\usepackage{graphicx}\n"
output += "\\title{"+findThing(rootThing).name+" documentation}\n"
output += "\\author{ThingDOC.py}\n"
output += "\\begin{document}\n"
output += "\\maketitle\n"
output += findThing(rootThing).description+"\n"
output += "\\newpage\n"
output += "\\tableofcontents\n"
output += "\\newpage\n"

#Printing BOM 
output += "\\section{Bill of materials}\n" 
output += "List of things you need to build the machine devided by categories\n" 
for category in [category for category in categories if category != "Uncategorized"]:
	categoryThingList = [thing for thing in things if (thing.category == category) and (thing.link in partsCount.keys()) ]
	#Write something only if category isnt empty
	if len(categoryThingList) > 0:
		output += "\\subsection{"+category+"}\n\\begin{itemize}\n" 
		#print "\n"+category +"\n==================="
		#Print category items
		for thing in categoryThingList:
			#print str(partsCount[thing.link]) +"x "+thing.name	
			output += "\\item "+str(partsCount[thing.link]) +"x "+thing.name+"\n"
		output += "\\end{itemize}\n" 
output += "\\newpage\n"

#Printing things info
#print "\n\nThings overview \n++++++++++++++++++++++++++\n"
output += "\\section{Things overview}\n" 
output += "List of things and their descriptions\n" 
for link, count in partsCount.iteritems():
	for thing in things:
		#if thing.category == category:
			if (thing.link == link) and (thing.common == False):
				output += "\\subsection{"+thing.name+"}\n" 
				output += thing.description+"\n\n"
				imgname = "images/"+thing.link+".jpg"
				if os.path.isfile("docs/"+imgname):
					output += "\\includegraphics[width=4cm]{"+imgname+"}\n"
				#print thing.name + "\n======================"\includegraphics{image.png}
				#print thing.description + "\n"
				found = True

output += "\\newpage\n"				

#Printing Instructions
output += "\\section{Assembly Instructions}\n" 
output += "Instructions to assemble the machine\n" 
for link in assemblyInstructions:
	thing = findThing(link)
	count = 1;
	if(thing.root != True):
		count = partsCount[thing.link];
	if(count > 1):
		output += "\\subsection{Assemble "+str(count) + "x "+thing.name+"}\n\\begin{itemize}\n"
	else:
		output += "\\subsection{Assemble "+thing.name+"}\n\\begin{itemize}\n"
	for instruction in thing.assembly:
		output += "\\item " + replaceLinksWithNames(instruction) + "\n"
	output += "\\end{itemize}\n" 

output += "\\end{document}\n" 			
#print output
filename = os.getcwd()+"/docs/doc.tex"
 
print "Writing TEX to file: %s" % filename
  
file = open(filename, 'w')
 
file.write(latexSafe(output))
 
file.close()


# Outputing TXT BOM

#Printing BOM 
output = findThing(rootThing).name+" bill of materials\n++++++++++++++++++++\n"
for category in [category for category in categories if category != "Uncategorized"]:
	categoryThingList = [thing for thing in things if (thing.category == category) and (thing.link in partsCount.keys()) ]
	#Write something only if category isnt empty
	if len(categoryThingList) > 0:
		output += "\n\n"+category+"\n====================\n"
		for thing in categoryThingList:
			#print str(partsCount[thing.link]) +"x "+thing.name	
			output += "- "+str(partsCount[thing.link]) +"x "+thing.name+"\n"

output += "\nAssembly\n++++++++++++++++++++\n"
for link in assemblyInstructions:
	thing = findThing(link)
	count = 1;
	if(thing.root != True):
		count = partsCount[thing.link];
	output += "Assemble " + str(count) + "x "+thing.name+"\n"
	for instruction in thing.assembly:
		output += "- " + replaceLinksWithNames(instruction) + "\n"

#print output
filename = os.getcwd()+"/docs/bom.txt"
 
print "Writing TXT BOM to file: %s" % filename
  
file = open(filename, 'w')
 
file.write(output)
 
file.close()

					

		



