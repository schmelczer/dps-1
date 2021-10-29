genhtml: genhtml.c
	gcc genhtml.c -lm -o genhtml

parsehtml: parsehtml.c
	gcc -lm -L/usr/lib64/libcrypto.so.10  -lcrypto hashtable.c hashtable_itr.c parsehtml.c -o parsehtml
	
run: genhtml
	rm -rf docs
	mkdir docs
	./genhtml
