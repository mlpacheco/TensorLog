import os

PATH = "/scratch2/pachecog/psl-drail/drail-4forums"
ISSUES = ["abortion", "evolution", "gay_marriage", "gun_control"]
SPLITS = ["learn", "eval"]
IN_THREAD = "in_thread.txt"

in_thread_dict = {}
with open(IN_THREAD) as fp:
    for line in fp:
        thread, post = line.strip().split('\t')
        in_thread_dict[post] = thread

# (respond_to, post_i, post_j)
# (is_author, post_i, author)  -- take it only from one split
# (agree, post_i, post_j, score)
# (stance, post_i, stance, score)

# inferred agree
# inferred stance

for issue in ISSUES:
    print(issue)
    for fid in range(0, 5):
        fold = "f{}".format(fid)
        print("\t{}".format(fold))
        curpath = os.path.join(PATH, issue, fold)
        is_author_cfacts = os.path.join(issue, fold, "is_author.cfacts")
        is_author_cfacts_w = open(is_author_cfacts, "w")
        in_thread_cfacts = os.path.join(issue, fold, "in_thread.cfacts")
        in_thread_cfacts_w = open(in_thread_cfacts, "w")
        respond_to_cfacts = os.path.join(issue, fold, "respond_to.cfacts")
        respond_to_cfacts_w = open(respond_to_cfacts, "w")
        agree_cfacts = os.path.join(issue, fold, "agree.cfacts")
        agree_cfacts_w = open(agree_cfacts, "w")
        stance_cfacts = os.path.join(issue, fold, "stance.cfacts")
        stance_cfacts_w = open(stance_cfacts, "w")

        inferred_stance_learn = os.path.join(issue, fold, "inferred_stance_learn.exam")
        inferred_stance_learn = open(inferred_stance_learn, "w")
        inferred_stance_eval = os.path.join(issue, fold, "inferred_stance_eval.exam")
        inferred_stance_eval = open(inferred_stance_eval, "w")
        inferred_agree_learn = os.path.join(issue, fold, "inferred_agree_learn.exam")
        inferred_agree_learn = open(inferred_agree_learn, "w")
        inferred_agree_eval = os.path.join(issue, fold, "inferred_agree_eval.exam")
        inferred_agree_eval = open(inferred_agree_eval, "w")

        same_thread_author = os.path.join(issue, fold, "same_thread_author.cfacts")
        same_thread_author_w = open(same_thread_author, "w")

        for split in SPLITS:
            # is_author
            if split == 'learn':
                is_author = os.path.join(curpath, split, "is_author.txt")
                threads = {}
                post_to_author = {}
                with open(is_author) as fp:
                    for line in fp:
                        post_i, author = line.strip().split('\t')
                        thread = in_thread_dict[post_i]
                        if thread not in threads:
                            threads[thread] = []
                        threads[thread].append(post_i)
                        post_to_author[post_i] = author

                        is_author_cfacts_w.write("{0}\tp{1}\t{2}\t{3}\n".format("is_author", post_i, author, 1.0))
                        in_thread_cfacts_w.write("{0}\tp{1}\tt{2}\t{3}\n".format("in_thread", post_i, thread, 1.0))

                # same author same thread
                for thread in threads:
                    for post_a in threads[thread]:
                        for post_b in threads[thread]:
                            if post_a != post_b and post_to_author[post_a] == post_to_author[post_b]:
                                same_thread_author_w.write("{0}\tp{1}\tp{2}\t{3}\n".format("same_thread_author", post_a, post_b, 1.0))

            # respond_to
            respond_to = os.path.join(curpath, split, "respond_to.txt")
            with open(respond_to) as fp:
                for line in fp:
                    post_i, post_j = line.strip().split('\t')
                    respond_to_cfacts_w.write("{0}\tp{1}\tp{2}\t{3}\n".format("respond_to", post_i, post_j, 1.0))

            # disagree -> agree
            disagree = os.path.join(curpath, split, "disagree_local.txt")
            with open(disagree) as fp:
                for line in fp:
                    post_i, post_j, score = line.strip().split('\t')
                    inv_score = str(1.0 - float(score))
                    agree_cfacts_w.write("{0}\tp{1}\tp{2}\t{3}\n".format("agree", post_i, post_j, inv_score))
                    #agree_cfacts_w.write("{0}\tp{1}\tp{2}\t{3}\n".format("agree", post_i, "none", score))
            # disagree truth -> agree truth
            disagree = os.path.join(curpath, split, "disagree_truth.txt")
            with open(disagree) as fp:
                for line in fp:
                    post_i, post_j, label = line.strip().split('\t')
                    if label == "0.0" and split == "learn":
                        inferred_agree_learn.write("{0}\tp{1}\tp{2}\n".format("agree", post_i, post_j))
                    elif label == "1.0" and split == "learn":
                        inferred_agree_learn.write("{0}\tp{1}\tp{2}\n".format("disagree", post_i, post_j))
                    elif label == "0.0" and split == "eval":
                        inferred_agree_eval.write("{0}\tp{1}\tp{2}\n".format("agree", post_i, post_j))
                    elif label == "1.0" and split == "eval":
                        inferred_agree_eval.write("{0}\tp{1}\tp{2}\n".format("disagree", post_i, post_j))

            # is_pro -> stance
            is_pro = os.path.join(curpath, split, "is_pro_local.txt")
            with open(is_pro) as fp:
                for line in fp:
                    post_i, _, score = line.strip().split('\t')
                    inv_score = str(1.0 - float(score))
                    stance_cfacts_w.write("{0}\tp{1}\t{2}\t{3}\n".format("stance", post_i, "pro", score))
                    stance_cfacts_w.write("{0}\tp{1}\t{2}\t{3}\n".format("stance", post_i, "con", inv_score))
            # is pro truth -> stance truth
            is_pro = os.path.join(curpath, split, "is_pro_truth.txt")
            with open(is_pro) as fp:
                for line in fp:
                    post_i, _, label = line.strip().split('\t')
                    if label == "0.0" and split == "learn":
                        inferred_stance_learn.write("{0}\tp{1}\t{2}\n".format("inferred_stance", post_i, "con"))
                    elif label == "1.0" and split == "learn":
                        inferred_stance_learn.write("{0}\tp{1}\t{2}\n".format("inferred_stance", post_i, "pro"))
                    elif label == "0.0" and split == "eval":
                        inferred_stance_eval.write("{0}\tp{1}\t{2}\n".format("inferred_stance", post_i, "con"))
                    elif label == "1.0" and split == "eval":
                        inferred_stance_eval.write("{0}\tp{1}\t{2}\n".format("inferred_stance", post_i, "pro"))
                    else:
                        print(line)
                        exit()

        inferred_stance_learn.close()
        inferred_stance_eval.close()
        inferred_agree_learn.close()
        inferred_agree_eval.close()

        is_author_cfacts_w.close()
        respond_to_cfacts_w.close()
        agree_cfacts_w.close()
        stance_cfacts_w.close()
        in_thread_cfacts_w.close()
        same_thread_author_w.close()

        all_cfacts = os.path.join(issue, fold, "all.cfacts")
        os.system("cat {0} {1} {2} {3} {4} {5} > {6}".format(agree_cfacts, in_thread_cfacts, is_author_cfacts, respond_to_cfacts, same_thread_author, stance_cfacts, all_cfacts))

