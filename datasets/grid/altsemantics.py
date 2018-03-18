import sys
import time
import tensorflow as tf
import numpy as np
import random
import getopt

# alternative semantics -- multiple outputs and distributional learning
# 
# --n N: grid size is N*N default 10
# --epochs N: default 100
# --repeat K: default 1


from tensorlog import simple,program,declare,dbschema,masterconfig
import expt


def setup_tlog(maxD,factFile,trainFile,testFile,multiclass):
  tlog = simple.Compiler(db=factFile,prog='grid.ppr')
  tlog.prog.db.markAsParameter('edge',2)
  tlog.prog.maxDepth = maxD
  print 'loading trainData,testData from',trainFile,testFile
  if multiclass:
    masterconfig.masterConfig().dataset.normalize_outputs = False
  trainData = tlog.load_small_dataset(trainFile)
  testData = tlog.load_small_dataset(testFile)
  return (tlog,trainData,testData)

def trainAndTest(tlog,trainData,testData,epochs,n,multiclass):
  mode = 'path/io'
  if multiclass:
    A = tf.Variable(1.0, "A")
    B = tf.Variable(0.0, "B")
    logits = A*tlog.proof_count(mode) + B
    predicted_y = tf.sigmoid(logits)
  else:
    predicted_y = tlog.inference(mode)
  actual_y = tlog.target_output_placeholder(mode)

  if multiclass:
    loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(labels=actual_y,logits=logits))
  else:
    loss = tlog.loss(mode)

  optimizer = tf.train.AdamOptimizer(0.1)
  train_step = optimizer.minimize(loss)

  session = tf.Session()
  session.run(tf.global_variables_initializer())

  def computed_accuracy(fd):
    if multiclass:
      actual = session.run(actual_y, feed_dict=fd)
      predicted = session.run(predicted_y, feed_dict=fd)
      #print '*** actual',actual
      #print '*** predicted',predicted
      total_preds = np.array(predicted>=0.0, dtype=np.float32).sum()
      total_correct = np.array((actual>0.5)==(predicted>0.5),dtype=np.float32).sum()
      #print '*** preds',total_correct,'correct',total_correct,'acc',total_correct/total_preds
      return total_correct/total_preds
    else:
      correct_predictions = tf.equal(tf.argmax(actual_y,1), tf.argmax(predicted_y,1))
      accuracy = tf.reduce_mean(tf.cast(correct_predictions, tf.float32))
      return session.run(accuracy, feed_dict=fd)


  (ux,uy) = testData[mode]
  test_fd = {tlog.input_placeholder_name(mode):ux, tlog.target_output_placeholder_name(mode):uy}
  #acc = session.run(accuracy, feed_dict=test_fd)
  acc = computed_accuracy(test_fd)
  print 'training: initial test acc',acc

  (tx,ty) = trainData[mode]
  train_fd = {tlog.input_placeholder_name(mode):tx, tlog.target_output_placeholder_name(mode):ty}

  def show_test_results():
    if False:
      test_preds = session.run(tf.argmax(predicted_y,1), feed_dict=test_fd)    
      print 'test best symbols are',map(lambda i:tlog.db.schema.getSymbol('__THING__',i),test_preds)
      if False:
        test_scores = session.run(predicted_y, feed_dict=test_fd)    
        print 'test scores are',test_scores
        weighted_predictions = session.run(tf.multiply(predicted_y, (x1+x2-2)), feed_dict=test_fd)    
        print 'test weighted_predictions',weighted_predictions
        test_loss = session.run(loss,feed_dict=test_fd)    
        print 'test loss',test_loss

  show_test_results()

  t0 = time.time()
  print 'epoch',
  for i in range(epochs):
    print i+1,
    session.run(train_step, feed_dict=train_fd)
    if (i+1)%3==0:
      test_fd = {tlog.input_placeholder_name(mode):ux, tlog.target_output_placeholder_name(mode):uy}
      train_loss = session.run(loss, feed_dict=train_fd)
      #train_acc = session.run(accuracy, feed_dict=train_fd)
      train_acc = computed_accuracy(train_fd)
      test_loss = session.run(loss, feed_dict=test_fd)
      #test_acc = session.run(accuracy, feed_dict=test_fd)
      test_acc = computed_accuracy(test_fd)
      print 'train loss',train_loss,
      print 'acc',train_acc,
      print 'test loss',test_loss,'acc',test_acc
      print 'epoch',
  print 'done'
  print 'learning takes',time.time()-t0,'sec'

  #acc = session.run(accuracy, feed_dict=test_fd)
  acc = computed_accuracy(test_fd)
  print 'test acc',acc

  show_test_results()

  tlog.set_all_db_params_to_learned_values(session)
  tlog.serialize_db('learned.db')

  return acc

def nodeName(i,j):
    return '%d,%d' % (i,j)

def genInputs(n,multiclass):
    #generate grid

    stem = 'inputs/g%d' % n

    factFile = stem+'_logic.cfacts'
    trainFile = stem+'_logic-train.exam'
    testFile = stem+'_logic-test.exam'
    rnd = random.Random()
    #rnd.seed(0)
    # generate the facts
    expt.generateGrid(n,factFile)
    # data
    with open(trainFile,'w') as fpTrain,open(testFile,'w') as fpTest:
      r = random.Random()
      for i in range(1,n+1):
        for j in range(1,n+1):
          if multiclass:
            tis = (1,2) if i<=n/2 else (n-1,n)
            tjs = (1,2) if j<=n/2 else (n-1,n)
          else:
            tis = (1,) if i<=n/2 else (n,)
            tjs = (1,) if j<=n/2 else (n,)
          x = nodeName(i,j)
          ys = [nodeName(ti,tj) for ti in tis for tj in tjs]
          fp = fpTrain if r.random()<0.67 else fpTest
          fp.write('\t'.join(['path',x] + ys) + '\n')
    return (factFile,trainFile,testFile)

def runMain(n='10',epochs='100',repeat='1',multiclass='False'):
  n = int(n)
  epochs = int(epochs)
  repeat = int(repeat)
  multiclass = True if (multiclass!='False' and multiclass!='0') else False
  print 'run',epochs,'epochs','training on',n,'x',n,'grid','maxdepth',n,'repeating',repeat,'times','multiclass',multiclass
  accs = []
  for r in range(repeat):
    print 'trial',r+1
    if len(accs)>0: print 'running avg',sum(accs)/len(accs)
    (factFile,trainFile,testFile) = genInputs(n,multiclass)
    (tlog,trainData,testData) = setup_tlog(n,factFile,trainFile,testFile,multiclass)
    acc = trainAndTest(tlog,trainData,testData,epochs,n,multiclass)
    accs.append(acc)
  print 'accs',accs,'average',sum(accs)/len(accs)

if __name__=="__main__":
  optlist,args = getopt.getopt(sys.argv[1:],"x:",['n=','epochs=','repeat=','multiclass='])
  optdict = dict(map(lambda(op,val):(op[2:],val),optlist))
  print 'optdict',optdict
  runMain(**optdict)
