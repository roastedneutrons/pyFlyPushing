from pyFlyPushing import *

def isValidChar(s):
	return True

def parseErr(msg,frag):
	return {"error":msg,"frag":frag}

def sex(fly):
	for chromosome in fly[0]:
		for gene in chromosome:
			if gene == "Y":
				return "M"
	return "F"

def checkStructure(fly):
	if len(fly) != 3:
		return parseErr("3 pairs of chromosomes are needed: ",str(fly))
	for pair in fly:
		if len(pair) > 2:
		   return parseErr("More than 2 chromosomes in the pair: ",str(pair))
		if len(pair) == 0:
		   return parseErr("Missing chromosomes: ",str(fly))
		for chromosome in pair:
			if len(chromosome) == 0:
				return parseErr("No genes on chromosomes: ",str(pair))
			for gene in chromosome:
				if gene == "":
					return parseErr("No genes on chromosomes: ",str(fly))    
			if len(pair) == 1:
				pair.append(pair[0])
	return fly


def parseFly(f,gender=None):
	ret = []
	gene = ""
	chromosome = []
	pair = []
	f = f.replace(" ","")
	state = 0
	openBrackets = 0
	frag = ""
	if len(f)==0:
		return parseErr("No Fly!",frag)
	for ch in f:
		frag += ch
		if state == 0:
			if ch in ['(','[','{']:
				gene += ch
				openBrackets+=1
				state = 1
			elif ch in [')',']','}']:
				return parseErr("Closed bracket before opening",frag)                   
			elif ch in [',']:
				chromosome.append(gene)  
				gene = ""
			elif ch in ['/']:
				chromosome.append(gene)
				pair.append(chromosome)
				gene = ""
				chromosome = []
			elif ch in [";"]:
				chromosome.append(gene)
				pair.append(chromosome) ;
				ret.append(pair)
				gene = ""
				chromosome = []
				pair = []               
			else:
				if isValidChar(ch):
					#print "isValidChar"
					gene += ch
				else:
					return parseErr("Unexpected Character",frag)
		elif state == 1:
			gene += ch
			if ch in ["(",'[','{']:
				openBrackets+=1
			elif ch in [")",']','}']:
				openBrackets-=1
			if openBrackets == 0:
				state = 0
	if openBrackets:
		return parseErr("Brackets do not match",frag)
	chromosome.append(gene)
	pair.append(chromosome)
	ret.append(pair)
	ret = checkStructure(ret)
	if "error" in ret:
		return(ret)       
	if gender and sex(ret)!=gender:
		return parseErr("Wrong Gender, Check Y",f)
	return {"fly":ret} 

markers=["Tft","e","CyO"]
balancers=["CyO"]
constraints=[[["CyO","CyO"],"l"]]
updateLists(constraints,balancers,markers)
fly1=Fly(parseFly("+;Tft,e/CyO;tub Gal80ts")["fly"])
fly2=Fly(parseFly("+/Y;UAS TntG/CyO;+")["fly"])
cross1=Cross(fly1,fly2,markers,balancers,constraints)
print cross1.punnettSquare
