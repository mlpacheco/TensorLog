# (C) William W. Cohen and Carnegie Mellon University, 2016

import sys
import logging
import getopt

import declare
import funs
import ops
import parser
import matrixdb
import bpcompiler
import learn
import mutil


#TODO make parameters of a program
MAXDEPTH=10
NORMALIZE=True

TRACE=True

##############################################################################
## a program
##############################################################################

class Program(object):

    def __init__(self, db=None, rules=parser.RuleCollection()):
        self.db = db
        self.function = {}
        self.rules = rules

    def findPredDef(self,mode):
        """Find the set of rules with a lhs that match the given mode."""
        return self.rules.rulesFor(mode)

    def compile(self,mode,depth=0):
        """ Produce an ops.Function object which implements the predicate definition
        """
        #find the rules which define this predicate/function
        
        if (mode,depth) in self.function:
            return

        if depth>MAXDEPTH:
            self.function[(mode,depth)] = funs.NullFunction(mode)
        else:
            predDef = self.findPredDef(mode)
            if len(predDef)==0:
                assert False,'no rules match mode %s' % mode
            elif len(predDef)==1:
                #instead of a sum of one function, just find the function
                #for this single predicate
                c = bpcompiler.BPCompiler(mode,self,depth,predDef[0])
                self.function[(mode,depth)] = c.getFunction()
            else:
                #compute a function that will sum up the values of the
                #clauses
                ruleFuns = map(lambda r:bpcompiler.BPCompiler(mode,self,depth,r).getFunction(), predDef)
                self.function[(mode,depth)] = funs.SumFunction(ruleFuns)
            if depth==0 and NORMALIZE:
                self.function[(mode,0)] = funs.SoftmaxFunction(self.function[(mode,0)])
        return self.function[(mode,depth)]

    def getPredictFunction(self,mode):
        if (mode,0) not in self.function: self.compile(mode)
        fun = self.function[(mode,0)]
        return fun

    def evalSymbols(self,mode,symbols):
        """ After compilation, evaluate a function.  Input is a list of
        symbols that will be converted to onehot vectors, and bound to
        the corresponding input arguments.
        """
        if TRACE: logging.debug('evalSymbols %s inputs %r' % (str(mode),symbols))
        return self.eval(mode, [self.db.onehot(s) for s in symbols])

    def eval(self,mode,inputs):
        """ After compilation, evaluate a function.  Input is a list of onehot
        vectors, which will be bound to the corresponding input
        arguments.
        """
        if (mode,0) not in self.function: self.compile(mode)
        fun = self.function[(mode,0)]
        if TRACE: logging.debug('eval function %s' % str(fun))
        if TRACE: logging.debug('\n'.join(fun.pprint()))
        if TRACE: logging.debug(str(inputs))
        return fun.eval(self.db, inputs)

    def evalGradSymbols(self,mode,symbols):
        """ After compilation, evaluate a function.  Input is a list of
        symbols that will be converted to onehot vectors, and bound to
        the corresponding input arguments.
        """
        return self.evalGrad(mode, [self.db.onehot(s) for s in symbols])

    def evalGrad(self,mode,inputs):
        """ After compilation, evaluate a function.  Input is a list of onehot
        vectors, which will be bound to the corresponding input
        arguments.
        """
        if (mode,0) not in self.function: self.compile(mode)
        fun = self.function[(mode,0)]
        return fun.evalGrad(self.db, inputs)

    @staticmethod 
    def _load(fileNames):
        ruleFiles = [f for f in fileNames if f.endswith(".ppr") or f.endswith(".tlog")]
        dbFiles = [f for f in fileNames if f.endswith(".db")]
        factFiles = [f for f in fileNames if f.endswith(".cfacts")]
        assert (not dbFiles) or (not factFiles), 'cannot combine a serialized database and .cfacts files'
        assert (not dbFiles) or (len(dbFiles)==1), 'cannot combine multiple serialized databases'
        assert dbFiles or factFiles,'no db specified'
        assert ruleFiles,'no rules specified'
        rules = parser.Parser.parseFile(ruleFiles[0])
        for f in ruleFiles[1:]:
            rules = parser.Parser.parseFile(f,rules)
        if dbFiles:
            db = matrixdb.MatrixDB.deserialize(dbFiles[0])
        if factFiles:
            db = matrixdb.MatrixDB()
            for f in factFiles:
                logging.debug("starting %s" % f)
                db.addFile(f)
                logging.debug("finished %s" % f)
        return (db,rules)

    @staticmethod
    def load(fileNames):
        (db,rules) = Program._load(fileNames)
        return Program(db,rules)

#
# subclass of Program that corresponds more or less to Proppr....
# 

class ProPPRProgram(Program):

    def __init__(self, db=None, rules=parser.RuleCollection(),weights=None):
        super(ProPPRProgram,self).__init__(db=db, rules=rules)
        #expand the syntactic sugar used by ProPPR
        self.rules.mapRules(ProPPRProgram._moveFeaturesToRHS)
        if weights!=None: self.setWeights(weights)

    def setWeights(self,weights):
        self.db.markAsParam("weighted",1)
        self.db.setParameter("weighted",1,weights)

    def getWeights(self):  
        return self.db.matEncoding[('weighted',1)]

    def getParams(self):
        return self.db.params

    @staticmethod
    def _moveFeaturesToRHS(rule0):
        rule = parser.Rule(rule0.lhs, rule0.rhs)
        if not rule0.findall:
            #parsed format is {f1,f2,...} but we only support {f1}
            assert len(rule0.features)==1,'multiple constant features not supported'
            constFeature = rule0.features[0].functor
            constAsVar = constFeature.upper()
            rule.rhs.append( matrixdb.assignGoal(constAsVar,constFeature) )
            rule.rhs.append( parser.Goal('weighted',[constAsVar]) )
        else:
            #format is {all(F):-...}
            assert len(rule0.features)==1,'feature generators of the form {a,b: ... } not supported'
            featureLHS = rule0.features[0]
            assert featureLHS.arity==1 and featureLHS.functor=='all', 'non-constant features must be of the form {all(X):-...}'
            outputVar = featureLHS.args[0] 
            for goal in rule0.findall:
                rule.rhs.append(goal)
            rule.rhs.append( parser.Goal('weighted',[outputVar]) )
        return rule

    @staticmethod
    def load(fileNames):
        (db,rules) = Program._load(fileNames)
        return ProPPRProgram(db,rules)

class Interp(object):
    """High-level interface to tensor log."""

    def __init__(self,initFiles=[],proppr=True,weights=None):
        if proppr: 
            self.prog = ProPPRProgram.load(initFiles)
            if weights==None:
                weights = self.prog.db.ones()
            self.prog.setWeights(weights)
        else: 
            self.prog = Program.load(initFiles)
        self.db = self.prog.db
        self.learner = None

    def list(self,str):
        assert str.find("/")>=0, 'supported formats are functor/arity, function/io, function/oi, function/o, function/i'
        functor,rest = str.split("/")
        try:
            arity = int(rest)
            self.listRules(functor,arity) or self.listFacts(functor,arity)
        except ValueError:
            self.listFunction(str)

    def listRules(self,functor,arity):
        mode = declare.ModeDeclaration(parser.Goal(functor,['x']*arity),strict=False)
        rules = self.prog.rules.rulesFor(mode)
        if rules:
            for r in rules: print r
            return True
        return False

    def listAllRules(self):
        self.prog.rules.listing()

    def listFacts(self,functor,arity):
        if self.db.inDB(functor,arity):
            print self.db.summary(functor,arity)
            return True
        return False

    def listAllFacts(self):
        self.db.listing()

    @staticmethod
    def _asMode(spec):
        if type(spec)==type("") and spec.find("/")>=0:
            functor,rest = spec.split("/")            
            return declare.ModeDeclaration(parser.Goal(functor,list(rest)))
        elif type(spec)==type(""):
            return declare.ModeDeclaration(spec)
        else:
            return spec

    def listFunction(self,modeSpec):
        mode = self._asMode(modeSpec)
        key = (mode,0)
        if key not in self.prog.function:
            self.prog.compile(mode)
        fun = self.prog.function[key]
        print "\n".join(fun.pprint())

    def eval(self,modeSpec,x):
        mode = self._asMode(modeSpec)
        result = self.prog.evalSymbols(mode,[x])
        return self.prog.db.rowAsSymbolDict(result)
    
    def train(self,trainingDataFile,modeSpec=False,allModes=False,trainSpec=False,epochs=5):
        trainingData = self.db.createPartner()
        trainingData.addFile(trainingDataFile)
        multiPredicate = False
        if modeSpec and not allModes:
            # then train just one mode
            mode = self._asMode(modeSpec)
            if not trainSpec:
                trainSpec = (mode.functor,mode.arity)
            X,Y = trainingData.matrixAsTrainingData(*trainSpec)
        else:
            # then train all available modes
            multiPredicate = True
            if not modeSpec: modeSpec="i,o"
            X,Y=([],[])
            mode = []
            for (functor,arity) in trainingData.matEncoding.keys():
                if arity != 2: assert "Nonbinary query predicate '%s' not supported" % functor
                thisMode = self._asMode("%s(%s)" % (functor,modeSpec))
                thisX,thisY=trainingData.matrixAsTrainingData(thisMode.functor,thisMode.arity)
                mode.append(thisMode)
                X.append(thisX)
                Y.append(thisY)
            Y = mutil.stack(Y)
        self.learner = learn.FixedRateGDLearner(self.prog,X,Y,epochs=epochs,multiPredicate=multiPredicate)
        P0 = self.learner.predict(mode,X)
        acc0 = self.learner.accuracy(Y,P0)
        xent0 = self.learner.crossEntropy(Y,P0)
        print 'untrained: xent0',xent0,'acc0',acc0

        self.learner.train(mode)
        P1 = self.learner.predict(mode)
        acc1 = self.learner.accuracy(Y,P1)
        xent1 = self.learner.crossEntropy(Y,P1)
        
        print "xent0>xent1? ",xent0>xent1
        print "acc0<acc1?   ",acc0<acc1
        print 'trained: xent1',xent1,'acc1',acc1
    def predict(self,queryFile,modeSpec=False):
        """ currently only supports queries with 1 input """
        X = []
        M = []
        multi = True
        if type(modeSpec) == type(""): 
            M = self._asMode(modeSpec)
            multi = False
        with open(queryFile,"r") as f:
            k=0
            for line in f:
                k+=1
                parts = line.strip().split("\t",2)
                if len(parts) < 2: assert "on line %d of %s: Need at least 2 fields; got %d. Syntax is <modeSpec> TAB <input> TAB <ignored>..." % (k,queryFile,len(parts))
                q,i = parts[0],parts[1]
                if not multi:
                    if q == M:
                        X.append(i)
                else:
                    if len(M) == 0 or q != M[-1]: 
                        M.append(self._asMode(q))
                        X.append([])
                    X[-1].append(i)
        def impl(m,x,n):
            result = self.prog.evalSymbols(m,[x])
            return self.prog.db.matrixAsSymbolDict(result,start=n)
        if not multi:
            return [M],[X],impl(M,X)
        else:
            init = False
            result = {}
            for i in range(len(M)):
                r = impl(M[i],X[i],len(result))
                result.update(r)
                logging.debug("r: %s" % str(r))
                logging.debug("Result: %s" % str(result))
            return M,X,result
    def solutions(self,queryFile,solutionsFile):
        M,I,S = self.predict(queryFile)
        def queries():
            k=-1
            for m,X in zip(M,I):
                for x in X:
                    k+=1
                    yield k,m,x,S[k]
        for qid,mode,instance,solutions in queries():
            print "# proved %d\t%s\t-1 msec" % (qid,queryString(mode,instance))
            ranked = solutions.items()
            ranked.sort(key=lambda x: x[1])
            k=0
            for v,s in ranked:
                print "%d\t%g\t%s" % (k,s,queryString(mode,instance,[v]))
            

def queryString(mode,instance,values=None):
    result = mode.functor
    delim = "("
    k=0
    for a in range(mode.arity):
        if mode.isInput(a): result += delim + instance
        else: 
            s = "X%d" % k
            if values: s = values[k]
            result += delim + s
            k+=1
        delim = ","
    return result + ")"

#
# sample main: python tensorlog.py test/fam.cfacts 'rel(i,o)' 'rel(X,Y):-spouse(X,Y).' william
#

if __name__ == "__main__":
    
    argspec = ["programFiles=","debug", "proppr","help"]
    try:
        optlist,args = getopt.getopt(sys.argv[1:], 'x', argspec)
    except getopt.GetoptError:
        logging.fatal('bad option: use "--help" to get help')
        sys.exit(-1)
    optdict = dict(optlist)
    if "--help" in optdict:
        print "python tensorlog.py --programFiles a.ppr:b.cfacts:... [p(i,o) x1 x2 ....]"
    if "--debug" in optdict:
        logging.basicConfig(level=logging.DEBUG)        
    

    assert '--programFiles' in optdict, '--programFiles f1:f2:... is a required option'
    ti = Interp(initFiles=optdict['--programFiles'].split(":"), proppr=('--proppr' in optdict))

    if args:
        modeSpec = args[0]
        for a in args[1:]:
            print ("f_%s[%s] =" % (modeSpec,a)),ti.eval(modeSpec,a)
