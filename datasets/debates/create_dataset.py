import os
import pathlib

PATH = "/scratch2/pachecog/psl-drail/drail-debates"
DATASETS = ["rand", "hard"]
SPLITS = ["learn", "eval"]

for dataset in DATASETS:
    for fid in range(0, 10):
        fold = "f{}".format(fid)
        curpath = os.path.join(PATH, dataset, fold)
        print("\t{}".format(curpath))

        is_author_cfacts = os.path.join(dataset, fold, "is_author.cfacts")
        path = pathlib.Path(is_author_cfacts)
        path.parent.mkdir(parents=True, exist_ok=True)
        is_author_cfacts_w = open(is_author_cfacts, "w")

        same_author_cfacts = os.path.join(dataset, fold, "same_author.cfacts")
        same_author_cfacts_w = open(same_author_cfacts, "w")

        opposing_author_cfacts = os.path.join(dataset, fold, "opposing_author.cfacts")
        opposing_author_cfacts_w = open(opposing_author_cfacts, "w")

        opposing_users_cfacts = os.path.join(dataset, fold, "opposing_user.cfacts")
        opposing_users_cfacts_w = open(opposing_users_cfacts, "w")

        opposing_stances_cfacts = os.path.join(dataset, fold, "opposing_stances.cfacts")
        opposing_stances_cfacts_w = open(opposing_stances_cfacts, "w")

        post_stance_cfacts = os.path.join(dataset, fold, "post_stance.cfacts")
        post_stance_cfacts_w = open(post_stance_cfacts, "w")

        user_stance_cfacts = os.path.join(dataset, fold, "user_stance.cfacts")
        user_stance_cfacts_w = open(user_stance_cfacts, "w")

        voter_stance_cfacts = os.path.join(dataset, fold, "voter_stance.cfacts")
        voter_stance_cfacts_w = open(voter_stance_cfacts, "w")

        vote_for_cfacts = os.path.join(dataset, fold, "vote_for.cfacts")
        vote_for_cfacts_w = open(vote_for_cfacts, "w")

        vote_same_cfacts = os.path.join(dataset, fold, "vote_same.cfacts")
        vote_same_cfacts_w = open(vote_same_cfacts, "w")

        inferred_post_learn = os.path.join(dataset, fold, "inferred_post_learn.exam")
        inferred_post_learn = open(inferred_post_learn, "w")

        inferred_post_eval = os.path.join(dataset, fold, "inferred_post_eval.exam")
        inferred_post_eval = open(inferred_post_eval, "w")

        inferred_user_learn = os.path.join(dataset, fold, "inferred_user_learn.exam")
        inferred_user_learn = open(inferred_user_learn, "w")

        inferred_user_eval = os.path.join(dataset, fold, "inferred_user_eval.exam")
        inferred_user_eval = open(inferred_user_eval, "w")

        inferred_voter_learn = os.path.join(dataset, fold, "inferred_voter_learn.exam")
        inferred_voter_learn = open(inferred_voter_learn, "w")

        inferred_voter_eval = os.path.join(dataset, fold, "inferred_voter_eval.exam")
        inferred_voter_eval = open(inferred_voter_eval, "w")

        for split in SPLITS:
            # participates_in : just to be able to find not author
            debate_participants = {}
            participates_in = os.path.join(curpath, split, "participates_in.txt")
            with open(participates_in) as fp:
                for line in fp:
                    debate_id, user_id = line.strip().split('\t')
                    if debate_id not in debate_participants:
                        debate_participants[debate_id] = []
                    debate_participants[debate_id].append(user_id)

            #for debate in debate_participants:
            #    print(len(debate_participants[debate]))
            #exit()

            # is author
            is_author = os.path.join(curpath, split, "is_author.txt")
            post_author = {}
            with open(is_author) as fp:
                for line in fp:
                    # post is of the form: fold_debate_issue_post
                    # author is of the form: fold_debate_issue_user

                    post_id, author_id = line.strip().split('\t')
                    post_author[post_id] = author_id
                    is_author_cfacts_w.write("{0}\t{1}\t{2}\t{3}\n".format("is_author", post_id, author_id, 1.0))

            # has_post : just to be able to find all posts by the same author
            debate_posts = {}
            has_post = os.path.join(curpath, split, "has_post.txt")
            with open(has_post) as fp:
                for line in fp:
                    debate_id, post_id = line.strip().split('\t')
                    if debate_id not in debate_posts:
                        debate_posts[debate_id] = []
                    debate_posts[debate_id].append(post_id)

            # create same author predicate
            for debate_id in debate_posts:
                for post_id_1 in debate_posts[debate_id]:
                    for post_id_2 in debate_posts[debate_id]:
                        if post_id_1 != post_id_2 and post_author[post_id_1] == post_author[post_id_2]:
                            same_author_cfacts_w.write("{0}\t{1}\t{2}\t{3}\n".format("same_author", post_id_1, post_id_2, 1.0))
                        elif post_id_1 != post_id_2:
                            opposing_author_cfacts_w.write("{0}\t{1}\t{2}\t{3}\n".format("opposing_author", post_id_1, post_id_2, 1.0))

            # post stance
            post_stance = os.path.join(curpath, split, "is_pro_local.txt")
            with open(post_stance) as fp:
                for line in fp:
                    _, post_id, score = line.strip().split('\t')
                    inv_score = str(1.0 - float(score))
                    post_stance_cfacts_w.write("{0}\t{1}\t{2}\t{3}\n".format("post_stance", post_id, "pro", score))
                    post_stance_cfacts_w.write("{0}\t{1}\t{2}\t{3}\n".format("post_stance", post_id, "con", inv_score))

            # user stance
            user_stance = os.path.join(curpath, split, "is_pro_user_local.txt")
            with open(user_stance) as fp:
                for line in fp:
                    debate_id, user_id, score = line.strip().split('\t')
                    inv_score = str(1.0 - float(score))
                    user_stance_cfacts_w.write("{0}\t{1}\t{2}\t{3}\n".format("user_stance", user_id, "pro", score))
                    user_stance_cfacts_w.write("{0}\t{1}\t{2}\t{3}\n".format("user_stance", user_id, "con", inv_score))

                    if user_id != debate_participants[debate_id][0]:
                        other_user_id = debate_participants[debate_id][1]
                    else:
                        other_user_id = debate_participants[debate_id][0]

                    opposing_users_cfacts_w.write("{0}\t{1}\t{2}\t{3}\n".format("opposing_user", user_id, other_user_id, 1.0))

            # voter stance
            voter_stance = os.path.join(curpath, split, "is_pro_voter_local.txt")
            with open(voter_stance) as fp:
                for line in fp:
                    _, user_id, score = line.strip().split('\t')
                    inv_score = str(1.0 - float(score))
                    voter_stance_cfacts_w.write("{0}\t{1}\t{2}\t{3}\n".format("voter_stance", user_id, "pro", score))
                    voter_stance_cfacts_w.write("{0}\t{1}\t{2}\t{3}\n".format("voter_stance", user_id, "con", inv_score))

            # vote_for
            vote_for = os.path.join(curpath, split, "votes_for_local.txt")
            with open(vote_for) as fp:
                for line in fp:
                    _, voter_id, user_id, score = line.strip().split('\t')
                    vote_for_cfacts_w.write("{0}\t{1}\t{2}\t{3}\n".format("vote_for", voter_id, user_id, score))

            # vote_same
            vote_same = os.path.join(curpath, split, "vote_same_local.txt")
            with open(vote_same) as fp:
                for line in fp:
                    _, voter_id, user_id, score = line.strip().split('\t')
                    vote_same_cfacts_w.write("{0}\t{1}\t{2}\t{3}\n".format("vote_same", voter_id, user_id, score))

            # post truth
            post_stance = os.path.join(curpath, split, "is_pro_truth.txt")
            with open(post_stance) as fp:
                for line in fp:
                    _, post_id, label = line.strip().split('\t')
                    if label == "0.0" and split == "learn":
                        inferred_post_learn.write("{0}\t{1}\t{2}\n".format("inferred_post", post_id, "con"))
                    elif label == "1.0" and split == "learn":
                        inferred_post_learn.write("{0}\t{1}\t{2}\n".format("inferred_post", post_id, "pro"))
                    elif label == "0.0" and split == "eval":
                        inferred_post_eval.write("{0}\t{1}\t{2}\n".format("inferred_post", post_id, "con"))
                    elif label == "1.0" and split == "eval":
                        inferred_post_eval.write("{0}\t{1}\t{2}\n".format("inferred_post", post_id, "pro"))
                    else:
                        print(line)
                        exit()

            # user truth
            user_stance = os.path.join(curpath, split, "is_pro_user_truth.txt")
            with open(user_stance) as fp:
                for line in fp:
                    _, user_id, label = line.strip().split('\t')
                    if label == "0.0" and split == "learn":
                        inferred_user_learn.write("{0}\t{1}\t{2}\n".format("inferred_user", user_id, "con"))
                    elif label == "1.0" and split == "learn":
                        inferred_user_learn.write("{0}\t{1}\t{2}\n".format("inferred_user", user_id, "pro"))
                    elif label == "0.0" and split == "eval":
                        inferred_user_eval.write("{0}\t{1}\t{2}\n".format("inferred_user", user_id, "con"))
                    elif label == "1.0" and split == "eval":
                        inferred_user_eval.write("{0}\t{1}\t{2}\n".format("inferred_user", user_id, "pro"))
                    else:
                        print(line)
                        exit()

            # voter truth
            voter_stance = os.path.join(curpath, split, "is_pro_voter_truth.txt")
            with open(voter_stance) as fp:
                for line in fp:
                    _, user_id, label = line.strip().split('\t')
                    if label == "0.0" and split == "learn":
                        inferred_voter_learn.write("{0}\t{1}\t{2}\n".format("inferred_voter", user_id, "con"))
                    elif label == "1.0" and split == "learn":
                        inferred_voter_learn.write("{0}\t{1}\t{2}\n".format("inferred_voter", user_id, "pro"))
                    elif label == "0.0" and split == "eval":
                        inferred_voter_eval.write("{0}\t{1}\t{2}\n".format("inferred_voter", user_id, "con"))
                    elif label == "1.0" and split == "eval":
                        inferred_voter_eval.write("{0}\t{1}\t{2}\n".format("inferred_voter", user_id, "pro"))
                    else:
                        print(line)
                        exit()

        opposing_stances_cfacts_w.write("opposing_stances\tpro\tcon\t1.0\n")
        opposing_stances_cfacts_w.write("opposing_stances\tcon\tcon\t1.0\n")

        is_author_cfacts_w.close()
        same_author_cfacts_w.close()
        opposing_author_cfacts_w.close()
        opposing_stances_cfacts_w.close()
        opposing_users_cfacts_w.close()
        post_stance_cfacts_w.close()
        user_stance_cfacts_w.close()
        voter_stance_cfacts_w.close()
        vote_for_cfacts_w.close()
        vote_same_cfacts_w.close()
        inferred_post_learn.close()
        inferred_post_eval.close()

        all_cfacts = os.path.join(dataset, fold, "all.cfacts")
        os.system("cat {0} {1} {2} {3} {4} {5} {6} {7} {8} {9} > {10}".format(is_author_cfacts, opposing_author_cfacts, same_author_cfacts, opposing_users_cfacts, opposing_stances_cfacts, post_stance_cfacts, user_stance_cfacts, voter_stance_cfacts, vote_for_cfacts, vote_same_cfacts, all_cfacts))
