CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic
.PHONY: all test clean
all: libmcsobel.so
libmcsobel.so: sobel.c sobel.h
	$(CC) $(CFLAGS) -fPIC -shared sobel.c -o $@
test_sobel: test_sobel.c sobel.c sobel.h
	$(CC) $(CFLAGS) -o $@ test_sobel.c sobel.c
test: test_sobel
	./test_sobel
clean:
	rm -f libmcsobel.so test_sobel
