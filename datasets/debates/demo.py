import sys
import tensorflow as tf
from sklearn.metrics import f1_score, accuracy_score
from tensorlog import simple
from collections import Counter

def runMain(argv):

  # option parsing - options should be passed in as something like sys.argv[1:], eg
  # runMain(["--epochs","20","--dataset","rand","--fold", "f0"])
  opts = simple.Options()
  opts.regularizer_scale = 0.1
  opts.link_scale = 0.9
  opts.epochs = 20 # 0 for no learning
  opts.max_depth = 100
  opts.dataset = "rand"
  opts.fold = "f0"
  opts.learning_rate = 0.01

  opts.infer_stance = True
  opts.infer_agree = False

  # override the option defaults, set above
  opts.set_from_command_line(argv)
  # define the input file names from the stems
  factFile = '{0}/{1}/all.cfacts'.format(opts.dataset, opts.fold)
  trainFile = '{0}/{1}/inferred_post_learn.exam'.format(opts.dataset, opts.fold)
  testFile = '{0}/{1}/inferred_post_eval.exam'.format(opts.dataset, opts.fold)
  mode = 'inferred_post/io'

  #testFile_agree = '{0}/{1}/inferred_agree_eval.exam'.format(opts.dataset, opts.fold)

  print(factFile, trainFile, testFile)

  # construct a Compiler object
  tlog = simple.Compiler(db=factFile,prog='debates.tlog')

  # tweak the program and database
  tlog.prog.maxDepth = opts.max_depth
  # scale down the friend links, according to the option link_scale.
  # smaller weights are like a higher reset in RWR/PPR
  #tlog.db.matEncoding[('agree',2)] = opts.link_scale * tlog.db.matEncoding[('agree',2)]
  # specify which relations will be treated as parameters
  tlog.mark_db_predicate_trainable('post_stance/2')
  tlog.mark_db_predicate_trainable('user_stance/2')
  #tlog.mark_db_predicate_trainable('voter_stance/2')
  #tlog.mark_db_predicate_trainable('vote_for/2')
  #tlog.mark_db_predicate_trainable('vote_same/2')

  # compile the rules, plus a query mode, into the inference function,
  # which we will use for testing
  predicted_y = tlog.inference(mode)
  actual_y = tlog.target_output_placeholder(mode)
  correct_predictions = tf.equal(tf.argmax(actual_y,1), tf.argmax(predicted_y,1))
  accuracy = tf.reduce_mean(tf.cast(correct_predictions, tf.float32))
  y_true = tf.argmax(actual_y, 1)
  y_pred = tf.argmax(predicted_y, 1)

  # also get the corresponding loss function from tensorlog
  unregularized_loss = tlog.loss(mode)
  # L1 regularize the basic loss function
  weight_vectors = tlog.trainable_db_variables(mode,for_optimization=True)
  regularized_loss = unregularized_loss
  for v in weight_vectors:
    regularized_loss = regularized_loss + opts.regularizer_scale*tf.reduce_sum(tf.abs(v))

  # how to optimize
  optimizer = tf.train.AdagradOptimizer(opts.learning_rate)
  train_step = optimizer.minimize(regularized_loss)

  # set up the session
  session = tf.Session()
  session.run(tf.global_variables_initializer())

  # load the training and test data
  trainData = tlog.load_small_dataset(trainFile)
  testData = tlog.load_small_dataset(testFile)

  # compute initial test-set performance
  (ux,uy) = testData[mode]
  test_fd = {tlog.input_placeholder_name(mode):ux, tlog.target_output_placeholder_name(mode):uy}
  initial_accuracy = session.run(accuracy, feed_dict=test_fd)
  #yt = session.run(y_true, feed_dict=test_fd)
  #yp = session.run(y_pred, feed_dict=test_fd)
  #print(yt)
  #print(yp)

  #cnt = Counter(yt)
  #label_list = [x for (x,y) in cnt.most_common(2)]

  #initial_macro_f1 = f1_score(yt, yp, average='macro', labels=label_list)
  print('initial test acc',initial_accuracy)
  #print('initial test macro f1',initial_macro_f1)

  # run the optimizer for fixed number of epochs
  (tx,ty) = trainData[mode]
  train_fd = {tlog.input_placeholder_name(mode):tx, tlog.target_output_placeholder_name(mode):ty}
  for i in range(opts.epochs):
    session.run(train_step, feed_dict=train_fd)
    #yt = session.run(y_true, feed_dict=train_fd)
    #yp = session.run(y_pred, feed_dict=train_fd)
    #macro_f1 = f1_score(yt, yp, average='macro', labels=label_list)

    #yt_test = session.run(y_true, feed_dict=test_fd)
    #yp_test = session.run(y_pred, feed_dict=test_fd)
    #macro_f1_test = f1_score(yt_test, yp_test, average='macro', labels=label_list)

    print('epoch',i+1,'train loss, accuracy and macro f1',session.run([unregularized_loss,accuracy], feed_dict=train_fd))
    #print('test macro f1',macro_f1)

  # save the learned model
  tlog.set_all_db_params_to_learned_values(session)
  #direc = '/tmp/%s-learned-model.prog' % opts.stem
  direc = '/tmp/learned-model.prog'
  tlog.serialize_program(direc)
  print('learned parameters serialized in',direc)

  # compute final test performance
  final_accuracy = session.run(accuracy, feed_dict=test_fd)
  #yt = session.run(y_true, feed_dict=test_fd)
  #yp = session.run(y_pred, feed_dict=test_fd)
  #final_macro_f1 = f1_score(yt, yp, average='macro', labels=label_list)
  print('initial test acc',initial_accuracy)
  #print('initial test macro f1',initial_macro_f1)
  print('STANCE= final test acc',final_accuracy)
  #print('STANCE= final test macro f1',final_macro_f1)

  '''
  post2stance = {}
  with open(testFile) as fp:
      for i, line in enumerate(fp):
          _, post, stance = line.strip().split('\t')
          #print(stance, yt[i])
          if yt[i] != yp[i] and stance == 'pro':
              pred = 'con'
          elif yt[i] != yp[i] and stance == 'con':
              pred = 'pro'
          else:
              pred = stance
          post2stance[post] = {'true': stance, 'pred': pred}

  yt_agree = []; yp_agree = []
  with open(testFile_agree) as fp:
      for i, line in enumerate(fp):
          reln, post_i, post_j = line.strip().split('\t')
          if reln == "agree":
              yt_agree.append(1)
          else:
              yt_agree.append(0)

          if post2stance[post_i]['pred'] == post2stance[post_j]['pred']:
              yp_agree.append(1)
          else:
              yp_agree.append(0)

  agree_final_f1 = f1_score(yt_agree, yp_agree, average='macro')
  agree_final_acc = accuracy_score(yt_agree, yp_agree)
  print('AGREE= final test acc',agree_final_acc)
  print('AGREE= final test macro f1',agree_final_f1)
  '''

  # save what was learned
  #schema_fp = open("schema_fp_{0}_{1}".format(opts.dataset, opts.fold), "w")
  #data_stream = open("data_stream_{0}_{1}".format(opts.dataset, opts.fold), "wb")

  #tlog.db.serializeDataTo(data_stream, filter="params")
  #tlog.db.schema.serializeTo(schema_fp)

  # return summary of statistics
  return initial_accuracy,final_accuracy

if __name__=="__main__":
  runMain(sys.argv[1:])
