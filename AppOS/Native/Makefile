CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic
LDFLAGS ?=
# make TIMING=1; MC_TIMING=1 ./build/demo
TIMING ?= 0
CPPFLAGS += -DMC_TIMING=$(TIMING)
OUT = build/demo

.PHONY: all clean run
all: $(OUT)
$(OUT): demo.c frame.c frame.h timing.c timing.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) demo.c frame.c timing.c -o $@ $(LDFLAGS)
run: all
	./$(OUT)
clean:
	rm -rf build
