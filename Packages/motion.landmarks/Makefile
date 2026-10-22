CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic
.PHONY: all test clean
all: libmcmotion.so
libmcmotion.so: motion.c motion.h
	$(CC) $(CFLAGS) -fPIC -shared motion.c -lm -o $@
test_motion: test_motion.c motion.c motion.h
	$(CC) $(CFLAGS) test_motion.c motion.c -lm -o $@
test: test_motion
	./test_motion
clean:
	rm -f test_motion libmcmotion.so
