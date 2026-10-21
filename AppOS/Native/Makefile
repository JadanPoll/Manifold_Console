CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic
LDFLAGS ?=
# make TIMING=1; MC_TIMING=1 ./build/demo
TIMING ?= 0
CPPFLAGS += -DMC_TIMING=$(TIMING)
OUT = build/demo
OBSERVER = build/observer_demo

.PHONY: all clean run
all: $(OUT) $(OBSERVER)
$(OUT): demo.c frame.c frame.h timing.c timing.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) demo.c frame.c timing.c -o $@ $(LDFLAGS)
$(OBSERVER): observer_demo.c frame.c frame.h timing.c timing.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) observer_demo.c frame.c timing.c -o $@ $(LDFLAGS)
run: all
	./$(OUT)
clean:
	rm -rf build
