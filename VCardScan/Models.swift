import Foundation
import CoreGraphics

// MARK: - Field keys

enum FieldKey: String, CaseIterable, Identifiable, Codable {
    case name    = "name"
    case title   = "title"
    case company = "company"
    case phone   = "phone"
    case email   = "email"
    case website = "website"
    case address = "address"

    var id: String { rawValue }

    var label: String {
        switch self {
        case .name:    return "Name"
        case .title:   return "Title"
        case .company: return "Company"
        case .phone:   return "Phone"
        case .email:   return "Email"
        case .website: return "Website"
        case .address: return "Address"
        }
    }

    var icon: String {
        switch self {
        case .name:    return "person.fill"
        case .title:   return "briefcase.fill"
        case .company: return "building.2.fill"
        case .phone:   return "phone.fill"
        case .email:   return "envelope.fill"
        case .website: return "globe"
        case .address: return "location.fill"
        }
    }
}

// MARK: - OCR Token

struct OCRToken: Identifiable, Equatable {
    let id: UUID
    let text: String
    var assignedField: FieldKey?
    let boundingBox: CGRect     // Vision normalized coords (origin bottom-left)
    let rotation: Double        // slight display tilt
    let colorIndex: Int

    init(text: String, boundingBox: CGRect) {
        self.id           = UUID()
        self.text         = text
        self.boundingBox  = boundingBox
        self.assignedField = Self.guess(text)
        self.rotation     = Double.random(in: -3.5...3.5)
        self.colorIndex   = Int.random(in: 0...5)
    }

    // Heuristic auto-assignment
    static func guess(_ text: String) -> FieldKey? {
        let t = text.trimmingCharacters(in: .whitespaces)
        if t.contains("@") { return .email }
        let digits = t.filter(\.isNumber).count
        let nonDigit = t.filter { !$0.isNumber && !"+-()./ ".contains($0) }.count
        if digits >= 7 && nonDigit < 4 { return .phone }
        let lower = t.lowercased()
        if lower.hasPrefix("www.") || lower.hasPrefix("http") { return .website }
        return nil
    }
}

// MARK: - Contact model

struct ContactModel {
    var name:    String   = ""
    var title:   String   = ""
    var company: String   = ""
    var phones:  [String] = []
    var emails:  [String] = []
    var website: String   = ""
    var address: String   = ""
}
