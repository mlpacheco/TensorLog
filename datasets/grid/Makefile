expt.log:
	python3 expt.py acc 16 > expt.log

actual.txt: expt.log
	echo \# actual result on `date` > actual.txt
	for f in tmp-cache/*.solutions.txt; do \
	echo file $$f >> actual.txt ; \
	proppr eval tmp-cache/test.examples $$f --metric auc --defaultNeg >> actual.txt ; \
	done
#	tail -13 expt.log  >> actual.txt

check: actual.txt
	diff -y actual.txt expected.txt || true

setup:
	mkdir -p inputs tmp-cache

unittest:
	python3 testexpt.py 

test:
	python3 expt.py time 16
	python3 expt.py time 64
	python3 expt.py acc

clean:
	rm -f *.pyc *.cfacts *.exam *~ visualize.png expt.log actual.txt inputs/* tmp-cache/*


