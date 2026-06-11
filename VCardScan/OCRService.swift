import Vision
import UIKit

enum OCRService {
    static func recognize(_ image: UIImage, completion: @escaping ([OCRToken]) -> Void) {
        guard let cg = image.cgImage else { return completion([]) }

        let req = VNRecognizeTextRequest { req, _ in
            let obs = (req.results as? [VNRecognizedTextObservation]) ?? []
            let tokens: [OCRToken] = obs.compactMap { o in
                guard let top = o.topCandidates(1).first, top.confidence > 0.25 else { return nil }
                let txt = top.string.trimmingCharacters(in: .whitespacesAndNewlines)
                guard !txt.isEmpty else { return nil }
                return OCRToken(text: txt, boundingBox: o.boundingBox)
            }
            DispatchQueue.main.async { completion(tokens) }
        }
        req.recognitionLevel = .accurate
        req.usesLanguageCorrection = true

        DispatchQueue.global(qos: .userInitiated).async {
            let handler = VNImageRequestHandler(cgImage: cg, options: [:])
            try? handler.perform([req])
        }
    }
}
