import SwiftUI

extension Color {
    static let appBg        = Color(red: 0.059, green: 0.055, blue: 0.051)   // #0F0E0D
    static let appCard      = Color(red: 0.110, green: 0.106, blue: 0.098)   // #1C1B19
    static let appAccent    = Color(red: 0.722, green: 1.000, blue: 0.176)   // #B8FF2D
    static let appText      = Color(red: 0.949, green: 0.941, blue: 0.910)   // #F2F0E8
    static let appMuted     = Color(red: 0.420, green: 0.416, blue: 0.392)   // #6B6A64
    static let appBorder    = Color(red: 0.180, green: 0.176, blue: 0.165)   // #2E2D2A
}

// Token palette — warm pastels on dark
let tokenPalette: [Color] = [
    Color(red: 0.749, green: 0.969, blue: 0.710),   // mint
    Color(red: 1.000, green: 0.839, blue: 0.690),   // peach
    Color(red: 0.800, green: 0.776, blue: 0.980),   // lavender
    Color(red: 0.659, green: 0.898, blue: 0.980),   // sky
    Color(red: 0.980, green: 0.953, blue: 0.722),   // cream
    Color(red: 1.000, green: 0.784, blue: 0.863),   // blush
]

extension Font {
    static func mono(_ size: CGFloat, weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight, design: .monospaced)
    }
}
