// tee-photogrammetry — thin CLI over Apple PhotogrammetrySession (RealityKit).
// Contract: compact newline-JSON events on stdout; loud errors naming the fix;
// exit 0 ok / 2 usage / 3 processing error / 4 unsupported hardware.
// The full quality ladder is exposed (preview|reduced|medium|full|raw); output
// format follows the output path's extension (.usdz native).
import Foundation
import RealityKit

func emit(_ fields: [String: Any]) {
    let parts = fields.map { key, value -> String in
        if let n = value as? Double { return "\"\(key)\":\(String(format: "%.4f", n))" }
        if let n = value as? Int { return "\"\(key)\":\(n)" }
        let s = "\(value)".replacingOccurrences(of: "\\", with: "\\\\")
            .replacingOccurrences(of: "\"", with: "\\\"")
            .replacingOccurrences(of: "\n", with: " ")
        return "\"\(key)\":\"\(s)\""
    }
    print("{" + parts.sorted().joined(separator: ",") + "}")
    fflush(stdout)
}

func fail(_ code: Int32, _ message: String, fix: String) -> Never {
    emit(["event": "error", "message": message, "fix": fix])
    exit(code)
}

func parseDetail(_ s: String) -> PhotogrammetrySession.Request.Detail? {
    switch s {
    case "preview": return .preview
    case "reduced": return .reduced
    case "medium": return .medium
    case "full": return .full
    case "raw": return .raw
    default: return nil
    }
}

let usage = """
usage: tee-photogrammetry <images-dir> <output-model-path> \
[--detail preview|reduced|medium|full|raw] [--ordered] [--high-sensitivity]
"""

@main
struct TeePhotogrammetry {
    static func main() async {
        var positional: [String] = []
        var detail: PhotogrammetrySession.Request.Detail = .reduced
        var ordered = false
        var highSensitivity = false
        var argIter = CommandLine.arguments.dropFirst().makeIterator()
        while let arg = argIter.next() {
            switch arg {
            case "--detail":
                guard let value = argIter.next(), let parsed = parseDetail(value) else {
                    fail(2, "bad --detail", fix: usage)
                }
                detail = parsed
            case "--ordered": ordered = true
            case "--high-sensitivity": highSensitivity = true
            case "--help", "-h": print(usage); exit(0)
            default: positional.append(arg)
            }
        }
        guard positional.count == 2 else { fail(2, "expected <images-dir> <output-model-path>", fix: usage) }
        guard PhotogrammetrySession.isSupported else {
            fail(4, "PhotogrammetrySession unsupported on this machine", fix: "run on Apple Silicon macOS 12+")
        }
        let inputURL = URL(fileURLWithPath: positional[0], isDirectory: true)
        guard FileManager.default.fileExists(atPath: inputURL.path) else {
            fail(2, "images dir not found: \(inputURL.path)", fix: "pass a directory of overlapping photos (HEIC/JPEG)")
        }
        let outputURL = URL(fileURLWithPath: positional[1])

        var config = PhotogrammetrySession.Configuration()
        config.sampleOrdering = ordered ? .sequential : .unordered
        config.featureSensitivity = highSensitivity ? .high : .normal

        let session: PhotogrammetrySession
        do {
            session = try PhotogrammetrySession(input: inputURL, configuration: config)
        } catch {
            fail(3, "session refused: \(error.localizedDescription)",
                 fix: "need a folder holding >=10 sharp overlapping photos of one subject")
        }
        emit(["event": "start", "detail": "\(detail)", "input": inputURL.path,
              "ordered": ordered ? 1 : 0, "sensitivity": highSensitivity ? "high" : "normal"])

        let start = Date()
        var lastTenth = -1
        let watcher = Task {
            do {
                for try await output in session.outputs {
                    switch output {
                    case .requestProgress(_, let fraction):
                        let tenth = Int(fraction * 10)
                        if tenth > lastTenth {  // budgeted: at most 10 progress lines
                            lastTenth = tenth
                            emit(["event": "progress", "fraction": fraction])
                        }
                    case .requestComplete(_, let result):
                        if case .modelFile(let url) = result { emit(["event": "model", "path": url.path]) }
                    case .requestError(_, let error):
                        emit(["event": "error", "message": "\(error)",
                              "fix": "check photo overlap/sharpness; >=10 images of one subject"])
                        exit(3)
                    case .invalidSample(let id, let reason):
                        emit(["event": "invalid_sample", "id": id, "reason": reason])
                    case .skippedSample(let id):
                        emit(["event": "skipped_sample", "id": id])
                    case .automaticDownsampling:
                        emit(["event": "automatic_downsampling"])
                    case .processingCancelled:
                        emit(["event": "cancelled"])
                        exit(3)
                    case .processingComplete:
                        emit(["event": "done", "seconds": Date().timeIntervalSince(start)])
                        exit(0)
                    default: break
                    }
                }
            } catch {
                fail(3, "output stream failed: \(error.localizedDescription)", fix: "rerun; if repeated, recapture the set")
            }
        }
        do {
            try session.process(requests: [.modelFile(url: outputURL, detail: detail)])
        } catch {
            fail(3, "process refused: \(error.localizedDescription)", fix: "verify output path is writable")
        }
        await watcher.value
    }
}
