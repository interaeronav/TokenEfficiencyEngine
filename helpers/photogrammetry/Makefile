BIN := tee-photogrammetry

$(BIN): TeePhotogrammetry.swift
	swiftc -O -parse-as-library -o $@ $<

clean:
	rm -f $(BIN)

.PHONY: clean
