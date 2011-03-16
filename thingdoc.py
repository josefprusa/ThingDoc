# ThingDOC 
# things comment parser
# http://thingdoc.org/
# by Josef Prusa (josefprusa.cz)
# GNU GPL v2 or up
 
# Imports
import os, fileinput, string, sys


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
		self.assembly = ""
		# If thing is soo common
		self.common = False
		# Other things which this thing uses
		self.usedParts = []

# List of all things
things = []

# Link to root thing
rootThing = "";

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
				
				if '/**' in line:
					#Hooray we found comment
					inComment = True
					foundThing = Thing()
					foundThing.category = "Uncategorized"
					foundThing.link = link
					foundThing.assembly = []
				if '@name' in line:
					#Thing name (-1 = remove nl character)
					name = line[9:len(line)-1]
					#print name
					foundThing.name = name.strip()
					thisLine = "name"
				if ('@using' in line) and (inComment is True):
					#Slice the line
					using = divide(line, " ")
					#Dig part name
					partName = using[4][0:len(using[4])-1]
					#Append it to things
					foundThing.usedParts.append([str(partName).strip(), int(using[3])])
					thisLine = "using"
				if ('@link' in line) and (inComment is True):
					# Thing link parsing
					foundLink = line[9:len(line)-1]
					#Append it to things
					foundThing.link = foundLink.strip()
					thisLine = "link"
				if ('@assembly' in line) and (inComment is True):
					# Thing link parsing
					assembly = line[12:len(line)-1]
					#Append it to things
					foundThing.assembly.append(assembly)
					thisLine = "assembly"
				if ('@category' in line) and (inComment is True):
					# Thing category
					category = line[13:len(line)-1]
					#Append it to things
					foundThing.category = category
					thisLine = "category"
				# Common thing
				if ('@common' in line) and (inComment is True):
					#Append it to things
					foundThing.common = True
					thisLine = "common"
				# Root thing
				if ('@root' in line) and (inComment is True):
					#Append it to things
					foundThing.root = True
					rootThing = link
					thisLine = "root"
					#debug msg
					if debug: print "Found root thing: " + link + "(" + foundThing.name + ")"
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

# List of instructions
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
			if not(thing.assembly in assemblyInstructions):
				for assembly in thing.assembly:
					assemblyInstructions.append(assembly)

# Parse things from root thing
parseTree(rootThing)

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
for assembly in assemblyInstructions:
	if(assembly != ""):
		output += "- "+assembly+"\n"

#print output
filename = os.getcwd()+"/docs/bom.txt"
 
print "Writing TXT BOM to file: %s" % filename
  
file = open(filename, 'w')
 
file.write(output)
 
file.close()

					

		



