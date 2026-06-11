import SwiftUI

// One-way flow: capture → scan → match → export → back to capture
enum AppScreen: Equatable {
    case capture
    case scan(UIImage)
    case match([OCRToken], UIImage)
    case export(ContactModel)

    static func == (lhs: AppScreen, rhs: AppScreen) -> Bool {
        switch (lhs, rhs) {
        case (.capture, .capture):   return true
        case (.scan, .scan):         return true
        case (.match, .match):       return true
        case (.export, .export):     return true
        default:                     return false
        }
    }
}

struct ContentView: View {
    @State private var screen: AppScreen = .capture
    @State private var direction: Edge = .trailing

    var body: some View {
        ZStack {
            Color.appBg.ignoresSafeArea()
            screenView
        }
        .animation(.spring(response: 0.42, dampingFraction: 0.85), value: screen)
    }

    @ViewBuilder
    private var screenView: some View {
        switch screen {
        case .capture:
            CaptureView { img in
                direction = .trailing
                screen = .scan(img)
            }
            .transition(.push(from: .leading))

        case .scan(let img):
            ScanView(image: img) { tokens in
                direction = .trailing
                screen = .match(tokens, img)
            }
            .transition(.push(from: direction))

        case .match(let tokens, let img):
            MatchView(tokens: tokens, cardImage: img) { contact in
                direction = .trailing
                screen = .export(contact)
            } onBack: {
                direction = .leading
                screen = .capture
            }
            .transition(.push(from: direction))

        case .export(let contact):
            ExportView(contact: contact) {
                direction = .leading
                screen = .capture
            }
            .transition(.push(from: direction))
        }
    }
}
