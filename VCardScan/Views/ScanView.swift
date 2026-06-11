import SwiftUI

struct ScanView: View {
    let image: UIImage
    var onComplete: ([OCRToken]) -> Void

    @State private var tokens:        [OCRToken] = []
    @State private var scanProgress:  CGFloat    = 0     // 0 → 1 top-to-bottom
    @State private var litBoxes:      Set<UUID>  = []
    @State private var flyOut:        Bool       = false
    @State private var phase:         Phase      = .ocr

    enum Phase { case ocr, scanning, extracting, done }

    var body: some View {
        ZStack {
            Color.appBg.ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer(minLength: 0)

                GeometryReader { geo in
                    let imgRect = fittedRect(imageSize: image.size, in: geo.size)

                    ZStack {
                        // Card photo
                        Image(uiImage: image)
                            .resizable()
                            .scaledToFit()
                            .clipShape(RoundedRectangle(cornerRadius: 14))
                            .shadow(color: .black.opacity(0.4), radius: 20, y: 8)

                        // OCR highlight boxes
                        ForEach(tokens) { token in
                            if litBoxes.contains(token.id) {
                                let r = convertBox(token.boundingBox, imageRect: imgRect)
                                RoundedRectangle(cornerRadius: 3)
                                    .stroke(Color.appAccent, lineWidth: 1.5)
                                    .background(
                                        RoundedRectangle(cornerRadius: 3)
                                            .fill(Color.appAccent.opacity(0.08))
                                    )
                                    .frame(width: r.width, height: r.height)
                                    .position(x: r.midX, y: r.midY)
                                    .opacity(flyOut ? 0 : 1)
                                    .scaleEffect(flyOut ? 0.2 : 1)
                                    .animation(.spring(response: 0.3, dampingFraction: 0.65), value: flyOut)
                            }
                        }

                        // Scan line
                        if phase == .scanning || phase == .ocr {
                            ScanLine()
                                .offset(y: imgRect.minY + imgRect.height * scanProgress - geo.size.height / 2)
                                .frame(width: geo.size.width)
                        }
                    }
                    .frame(width: geo.size.width, height: geo.size.height)
                }
                .aspectRatio(image.size.width / image.size.height, contentMode: .fit)
                .padding(.horizontal, 28)

                Spacer(minLength: 0)

                // Status label
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

            // Animate scan line over 1.4 s
            withAnimation(.linear(duration: 1.4)) { scanProgress = 1 }

            // Light up boxes as line passes them
            for token in found {
                // Vision Y is from bottom; convert to display progress (0=top)
                let displayY = 1 - (token.boundingBox.midY)
                let delay    = 1.4 * displayY
                DispatchQueue.main.asyncAfter(deadline: .now() + delay) {
                    withAnimation(.easeOut(duration: 0.18)) { litBoxes.insert(token.id) }
                }
            }

            // After scan completes
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                phase = .extracting
                // Fly boxes out
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.45) {
                    withAnimation(.easeIn(duration: 0.3)) { flyOut = true }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.35) {
                        phase = .done
                        onComplete(tokens)
                    }
                }
            }
        }
    }

    // MARK: - Geometry helpers

    private func fittedRect(imageSize: CGSize, in viewSize: CGSize) -> CGRect {
        let iA = imageSize.width / imageSize.height
        let vA = viewSize.width / viewSize.height
        if iA > vA {
            let h = viewSize.width / iA
            return CGRect(x: 0, y: (viewSize.height - h) / 2, width: viewSize.width, height: h)
        } else {
            let w = viewSize.height * iA
            return CGRect(x: (viewSize.width - w) / 2, y: 0, width: w, height: viewSize.height)
        }
    }

    /// Convert Vision normalized box → CGRect in GeometryReader coords
    private func convertBox(_ box: CGRect, imageRect: CGRect) -> CGRect {
        let x = imageRect.minX + box.minX * imageRect.width
        let y = imageRect.minY + (1 - box.maxY) * imageRect.height   // flip Y
        return CGRect(x: x, y: y, width: box.width * imageRect.width, height: box.height * imageRect.height)
    }
}

// MARK: - Scan line

struct ScanLine: View {
    @State private var glow = false

    var body: some View {
        ZStack {
            Rectangle()
                .fill(
                    LinearGradient(
                        stops: [
                            .init(color: .clear,                             location: 0),
                            .init(color: Color.appAccent.opacity(0.6),       location: 0.45),
                            .init(color: Color.appAccent,                    location: 0.5),
                            .init(color: Color.appAccent.opacity(0.6),       location: 0.55),
                            .init(color: .clear,                             location: 1),
                        ],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .frame(height: 2)
                .shadow(color: Color.appAccent.opacity(glow ? 0.9 : 0.5), radius: glow ? 8 : 4)
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 0.5).repeatForever(autoreverses: true)) { glow = true }
        }
    }
}
