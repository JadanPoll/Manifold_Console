CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic
.PHONY: all test clean replay-check
all: libmcmotion.so
libmcmotion.so: motion.c motion.h
	$(CC) $(CFLAGS) -fPIC -shared motion.c -lm -o $@
test_motion: test_motion.c motion.c motion.h
	$(CC) $(CFLAGS) test_motion.c motion.c -lm -o $@
replay: replay.c motion.c motion.h
	$(CC) $(CFLAGS) replay.c motion.c -lm -o $@
replay-check: replay
	./replay fixtures/pinch.csv > replay.events.tmp
	diff -u fixtures/expected_events.csv replay.events.tmp
	rm -f replay.events.tmp
test: test_motion replay-check
	./test_motion
clean:
	rm -f test_motion replay replay.events.tmp libmcmotion.so
