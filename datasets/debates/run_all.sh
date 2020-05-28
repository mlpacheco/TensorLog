for i in {0..9}
  do
    echo "RAND f$i"
    python3 demo.py --dataset rand --fold f$i
    echo "HARD f$i"
    python3 demo.py --dataset hard --fold f$i
  done
