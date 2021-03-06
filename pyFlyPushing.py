#import itertools
#import logging
import sys
from django.utils import simplejson as json

#logging.getLogger().setLevel(logging.DEBUG)

def product(*args, **kwds):
	# product('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
	# product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111
	pools = map(tuple, args) * kwds.get('repeat', 1)
	result = [[]]
	for pool in pools:
		result = [x+[y] for x in result for y in pool]
	for prod in result:
		yield list(prod)

def genoHash(genotype):
	genoHash=[]
	for chrA,chrB in genotype:
		genoHash.append(sorted([chrA.cHash,chrB.cHash]))
	return genoHash

def listToDict(lst):
	dct={}
	for item in lst:
		if item in dct: dct[item]+=1
		else: dct[item]=1
	return dct

def dictSubset(d1,d2):#to check if d1 is subset of d2
	for d1key in d1:
		if d1key in d2:
			if d1[d1key]>d2[d1key]: return False
		else: return False
	return True

def findRescuerPairs(causerList,rawRescuerList):# find a list of rescuers for each lethal set
	rescuerList=[]
	for causer in causerList:
		rescuers=[]
		for r in rawRescuerList:
			if dictSubset(causer,r):rescuers.append(r)
		rescuerList.append(rescuers)
	return rescuerList

def makeFlyFromGametes(gamete1,gamete2,environment):
	flyG=[]
	warnings=[]
	for i in range(len(gamete1)):
		if (gamete1[i].cHash != gamete2[i].cHash) and not(gamete1[i].balancer or gamete2[i].balancer) and not(gamete1[i].Y or gamete2[i].Y):
			warnings.append( "Warning! Recombination will occur betweeen "+str(gamete1[i])+" and "+str(gamete2[i]))
		flyG.append([gamete1[i].geneList,gamete2[i].geneList])
	return warnings,Fly(flyG,environment)

def _deSpace(lst):#so taht accidental spaces entered by user doesnt mess up stuff
	ret=[]
	for item in lst:
		#print item
		ret.append(item.replace(" ",""))
	return ret

class Environment():
	def __init__(self,constraints,balancers,markers):
		self.balancers=_deSpace(balancers)
		self.markers=_deSpace(markers)
		self.constraints=[]
		for constraint,tag in constraints:
			self.constraints.append([_deSpace(constraint),tag])
		
		self.lList=[]#lethal: list of dicts
		self.rlList=[]#rescues lethality: list of list of dicts
		self.sList=[]#sterile: list of dicts
		self.rsList=[]#rescues sterility: list of list of dicts
		self.iList=[]#marker interference (cant be rescued)
		self.riList=[]#kept for uniformity with the other lists
		rlTemp=[]
		rsTemp=[]
		for constraint,tag in constraints:
			if tag=='l':self.lList.append(listToDict(constraint))
			elif tag=='rl':rlTemp.append(listToDict(constraint))
			elif tag=='s':self.sList.append(listToDict(constraint))
			elif tag=='rs':rsTemp.append(listToDict(constraint))
			elif tag=='i':self.iList.append(listToDict(constraint))
		self.rlList=findRescuerPairs(self.lList,rlTemp)	
		self.rsList=findRescuerPairs(self.sList,rsTemp)
		self.riList=findRescuerPairs(self.iList,[])

class Chromosome():
	def __init__(self,geneList,environment):
		self.geneList=geneList
		self.cHash=sorted(_deSpace(geneList))
		self.Y=False
		self.domMarkers=[]
		self.recMarkers=[]
		self.balancer=False
		#deSpacedGeneList=[]
		for gene in geneList:
			#deSpacedGeneList.append(gene.replace(" ",""))#So that accidental spaces entered by user doesnt mess up stuff
			if gene in environment.markers:
				if gene[0].isupper():
					self.domMarkers.append(gene)
				elif gene[0].islower():self.recMarkers.append(gene)
			if gene=='Y':self.Y=True
			if gene in environment.balancers:self.balancer=True
		#self.cHash=sorted(deSpacedGeneList)

	def __str__(self):
		return ','.join(self.geneList)

class Fly():
	def __init__(self,genotype,environment,withChromObj=False):
		self.genotype=[]
		self.allGenes=[]
		self.gender=None
		self.phenotype=[]
		self.phenoHash=[]
		self.flyHash=[]
		self.gametes=[]
		self.lethal=None
		self.sterile=None
		self.markerInterference=None
		#self.environment=environment

		# # add genes to allGenes, and fill genotype with chromosome objects
		if withChromObj:
			self.genotype=genotype
			for chrA,chrB in genotype:
				self.allGenes+=chrA.geneList+chrB.geneList
			self.allGenes=filter(lambda x: x!='+',self.allGenes)#remove all instances of +
		else:
			for chrAList,chrBList in genotype:
				self.allGenes+=chrAList+chrBList
				self.genotype.append([Chromosome(chrAList,environment),Chromosome(chrBList,environment)])
			self.allGenes=filter(lambda x: x!='+',self.allGenes)#remove all instances of +

		# # Find Gender
		for allosome in self.genotype[0]:
			if allosome.Y:self.gender='Male'
		if not self.gender:
			self.gender='Female'

		# # function to find lethality, sterility and markerInterference
		def checkConstraint(causerList,rescuerList):
			flyGeneDict=listToDict(self.allGenes)
			for i in range(len(causerList)):
				if dictSubset(causerList[i],flyGeneDict):
					rescued=False
					#print ("rescuerList",rescuerList,"causerList",causerList)
					for rescuer in rescuerList[i]:
						if dictSubset(rescuer,flyGeneDict):
							rescued=True
							break
					if not rescued: return True
			return False
						

		# # look at constraints for lethality(l),sterility(s) and markerInterference(i)
		self.lethal=checkConstraint(environment.lList,environment.rlList)
		self.sterile=checkConstraint(environment.sList,environment.rsList)
		self.markerInterference=checkConstraint(environment.iList,environment.riList)

		# # Find Phenotype
		if self.lethal: self.phenotype=['lethal']
		else:
			self.phenotype=[self.gender]
			for chrA,chrB in self.genotype:
				self.phenotype+=filter(lambda x:x in chrA.recMarkers,chrB.recMarkers)#intersection of recMarkers
				self.phenotype+=chrA.domMarkers+filter(lambda x:x not in chrA.domMarkers,chrB.domMarkers)#union of domMarkers

		# # Find genoHash and phenoHash
		self.flyHash=genoHash(self.genotype)
		self.phenoHash=sorted(self.phenotype)

		# # Find gametes
		chrList=[]
		for chrA,chrB in self.genotype:
			if chrA.cHash==chrB.cHash:chrList.append([chrA])
			else:chrList.append([chrA,chrB])
		self.gametes=list(product(*chrList))


	def __str__(self):
		return " ; ".join([str(chromosomeA)+' / '+str(chromosomeB) for chromosomeA,chromosomeB in self.genotype])

class PunnettSquare():
	def __init__(self):
		self.fly1Axis=[]
		self.fly2Axis=[]

class Cross():
	def __init__(self,fly1,fly2,environment):
		self.fly1=fly1
		self.fly2=fly2
		self.environment=environment
		self.punnettSquare=self.punnett(fly1,fly2)
		self.identifiables=[]#stuff without phenotype clashes
		self.unidentifiables=[]#stuff with phenotype clashes

	
	def punnett(self,fly1,fly2):
		punnettSquare=[]
		for gamete1 in fly1.gametes:
			flyRow=[]
			for gamete2 in fly2.gametes:
				warnings,fly=makeFlyFromGametes(gamete1,gamete2,self.environment)
				flyRow.append({'warnings':warnings,
									'Fly':fly})
			punnettSquare.append(flyRow)
		return (fly1.gametes,
				  fly2.gametes,
				  punnettSquare)

class Bottle:
	def __init__(self,fly,environment):
		self.flies=[]
		self.deadFlies=[]
		chromosomes=[]
		for i in range(len(fly.genotype)):
			chrA=fly.genotype[i][0]
			chrB=fly.genotype[i][1]
			Y=Chromosome(['Y'],environment)
			combinations=[]
			if chrA.cHash == chrB.cHash:
				combinations=[[chrA,chrA]]
				if i==0:
					combinations+=[[chrA,Y]]
			else:
				if i==0:
					if chrA.Y:
						combinations=[[chrA,chrB],[chrB,chrB]]
					elif chrB.Y:
						combinations=[[chrA,chrB],[chrA,chrA]]
					else:
						combinations=[[chrA,Y],[chrB,Y],[chrA,chrB],[chrA,chrA],[chrB,chrB]]
				else:
					combinations=[[chrA,chrB],[chrA,chrA],[chrB,chrB]]
			#print combinations
			chromosomes.append(combinations)
		genotypes=product(*chromosomes)
		# print list(genotypes)
		for genotype in genotypes:
			fly=Fly(genotype,environment,withChromObj=True)
			if fly.lethal:
				self.deadFlies.append(fly)
			else:
				self.flies.append(fly)
			

def punnettDict(fly1,fly2,child):
	fly1AxisChr,fly2AxisChr,punnettSqr=punnett(fly1,fly2)

	# Convert the chromosome object filled gametes to strings
	fly1Axis=[';'.join([str(chromosome) for chromosome in gamete]) for gamete in fly1AxisChr]
	fly2Axis=[';'.join([str(chromosome) for chromosome in gamete]) for gamete in fly2AxisChr]
	
	genotypeMappings={}
	phenotypeMappings={}
	if child:
		reformattedChildGenotype=genotypeMappings[str(child.flyHash)]=str(child)
	else:
		reformattedChildGenotype=""
	p=[]
	for row in range(len(punnettSqr)):
		pRow=[]
		for col in range(len(punnettSqr[row])):
			fly=punnettSqr[row][col]['Fly']
			warnings=punnettSqr[row][col]['warnings']

			# Make mappings of genoHashes to human readable genotypes
			if str(fly.flyHash) in genotypeMappings:
				genotype=genotypeMappings[str(fly.flyHash)]
			else:
				genotype=genotypeMappings[str(fly.flyHash)]=str(fly)

			# Make mappings of phenoHashes to human readable phenotypes
			if str(fly.phenoHash) in phenotypeMappings:
				phenotype=phenotypeMappings[str(fly.phenoHash)]
			else:
				phenotype=phenotypeMappings[str(fly.phenoHash)]=fly.phenotype

			flyDict={'genotype':genotype,
						'phenotype':phenotype,
						'sterile':fly.sterile,
						'lethal':fly.lethal,
						'warnings':warnings,
						'markerInterference':fly.markerInterference}
			pRow.append(flyDict)
		p.append(pRow)
	return {'fly1Axis':fly1Axis,
			  'fly2Axis':fly2Axis,
			  'reformattedChild':reformattedChildGenotype,
			  'punnettSquare':p}

