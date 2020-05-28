for i in {0..9}
  do
    echo "RAND f$i"
    CUDA_VISIBLE_DEVICES=1,2 python3 demo.py --dataset rand --fold f$i --epochs 30 --opt_predicate user
    echo "HARD f$i"
    CUDA_VISIBLE_DEVICES=1,2 python3 demo.py --dataset hard --fold f$i --epochs 30 --opt_predicate user
  done
