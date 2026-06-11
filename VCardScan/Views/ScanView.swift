import SwiftUI

struct ScanView: View {
    let image: UIImage
    var onComplete: ([OCRToken]) -> Void

    @State private var tokens:       [OCRToken] = []
    @State private var scanProgress: CGFloat    = 0     // 0 → 1, top to bottom
    @State private var litBoxes:     Set<UUID>  = []
    @State private var flyOut:       Bool       = false
    @State private var phase:        Phase      = .ocr

    enum Phase { case ocr, scanning, extracting, done }

    var body: some View {
        ZStack {
            Color.appBg.ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer(minLength: 0)

                // Image with scan overlay
                Image(uiImage: image)
                    .resizable()
                    .scaledToFit()
                    .clipShape(RoundedRectangle(cornerRadius: 14))
                    .shadow(color: .black.opacity(0.4), radius: 20, y: 8)
                    .overlay(scanOverlay)
                    .padding(.horizontal, 28)

                Spacer(minLength: 0)

                // Status
                HStack(spacing: 8) {
                    if phase != .done {
                        ProgressView()
                            .scaleEffect(0.75)
                            .tint(Color.appAccent)
                    }
                    Text(statusText)
                        .font(.mono(12, weight: .medium))
                        .foregroundStyle(Color.appAccent)
                }
                .frame(height: 36)
                .padding(.bottom, 40)
            }
        }
        .onAppear(perform: runPipeline)
    }

    // MARK: - Overlay — placed directly on the image, so geo.size == displayed image size

    private var scanOverlay: some View {
        GeometryReader { geo in
            ZStack(alignment: .topLeading) {
                // OCR bounding box highlights
                ForEach(tokens) { token in
                    if litBoxes.contains(token.id) {
                        let r = visionToView(token.boundingBox, size: geo.size)
                        RoundedRectangle(cornerRadius: 3)
                            .stroke(Color.appAccent, lineWidth: 1.5)
                            .background(
                                RoundedRectangle(cornerRadius: 3)
                                    .fill(Color.appAccent.opacity(0.09))
                            )
                            .frame(width: r.width, height: r.height)
                            .offset(x: r.minX, y: r.minY)
                            .opacity(flyOut ? 0 : 1)
                            .scaleEffect(flyOut ? 0.15 : 1, anchor: .center)
                            .animation(.spring(response: 0.3, dampingFraction: 0.65), value: flyOut)
                    }
                }

                // Neon scan line
                if phase == .scanning || phase == .ocr {
                    ScanLine()
                        .frame(width: geo.size.width, height: 3)
                        .offset(y: scanProgress * geo.size.height)
                }
            }
        }
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }

    private var statusText: String {
        switch phase {
        case .ocr:        return "reading card..."
        case .scanning:   return "scanning..."
        case .extracting: return "extracting text"
        case .done:       return "done"
        }
    }

    // MARK: - Pipeline

    private func runPipeline() {
        OCRService.recognize(image) { found in
            tokens = found
            phase  = .scanning

            withAnimation(.linear(duration: 1.4)) { scanProgress = 1 }

            // Light each box as the scan line crosses its midpoint
            for token in found {
                let displayY = 1 - token.boundingBox.midY   // Vision Y is bottom-origin
                let delay    = 1.4 * displayY
                DispatchQueue.main.asyncAfter(deadline: .now() + max(delay, 0)) {
                    withAnimation(.easeOut(duration: 0.15)) { litBoxes.insert(token.id) }
                }
            }

            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                phase = .extracting
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.45) {
                    withAnimation(.easeIn(duration: 0.28)) { flyOut = true }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.32) {
                        phase = .done
                        onComplete(tokens)
                    }
                }
            }
        }
    }

    // MARK: - Coordinate conversion

    /// Vision box (normalized, Y=0 at bottom) → CGRect in overlay coords (Y=0 at top)
    private func visionToView(_ box: CGRect, size: CGSize) -> CGRect {
        CGRect(
            x:      box.minX * size.width,
            y:      (1 - box.maxY) * size.height,
            width:  box.width  * size.width,
            height: box.height * size.height
        )
    }
}

// MARK: - Animated scan line

struct ScanLine: View {
    @State private var glow = false

    var body: some View {
        ZStack {
            Rectangle()
                .fill(
                    LinearGradient(
                        stops: [
                            .init(color: .clear,                       location: 0),
                            .init(color: Color.appAccent.opacity(0.5), location: 0.3),
                            .init(color: Color.appAccent,              location: 0.5),
                            .init(color: Color.appAccent.opacity(0.5), location: 0.7),
                            .init(color: .clear,                       location: 1),
                        ],
                        startPoint: .leading,
                        endPoint:   .trailing
                    )
                )
            Rectangle()
                .fill(Color.appAccent.opacity(glow ? 0.35 : 0.15))
                .blur(radius: 6)
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 0.55).repeatForever(autoreverses: true)) {
                glow = true
            }
        }
    }
}
