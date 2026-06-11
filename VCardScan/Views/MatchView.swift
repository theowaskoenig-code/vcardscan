import SwiftUI

struct MatchView: View {
    @State var tokens: [OCRToken]
    let cardImage: UIImage
    var onDone: (ContactModel) -> Void
    var onBack: () -> Void

    var unassigned: [OCRToken] { tokens.filter { $0.assignedField == nil } }

    var body: some View {
        VStack(spacing: 0) {
            header
            tokenTray
            Divider().background(Color.appBorder)
            fieldList
            doneButton
        }
        .background(Color.appBg.ignoresSafeArea())
    }

    // MARK: - Header

    private var header: some View {
        HStack(spacing: 12) {
            Button(action: onBack) {
                Image(systemName: "arrow.left")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(Color.appMuted)
            }

            Image(uiImage: cardImage)
                .resizable()
                .scaledToFill()
                .frame(width: 56, height: 36)
                .clipShape(RoundedRectangle(cornerRadius: 6))

            VStack(alignment: .leading, spacing: 2) {
                Text("match fields")
                    .font(.mono(18, weight: .black))
                    .foregroundStyle(Color.appText)
                Text("drag text → field")
                    .font(.mono(10, weight: .medium))
                    .foregroundStyle(Color.appMuted)
            }
            Spacer()
        }
        .padding(.horizontal, 20)
        .padding(.top, 16)
        .padding(.bottom, 12)
    }

    // MARK: - Token tray (unassigned)

    @ViewBuilder
    private var tokenTray: some View {
        if unassigned.isEmpty {
            HStack {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundStyle(Color.appAccent)
                Text("all tokens assigned")
                    .font(.mono(11, weight: .medium))
                    .foregroundStyle(Color.appMuted)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(Color.appCard)
        } else {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    Text("unmatched")
                        .font(.mono(9, weight: .bold))
                        .foregroundStyle(Color.appMuted)
                        .padding(.leading, 4)
                    ForEach(unassigned) { token in
                        TokenPill(token: token)
                            .draggable(token.id.uuidString)
                    }
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 14)
            }
            .background(Color.appCard)
        }
    }

    // MARK: - Field list

    private var fieldList: some View {
        ScrollView {
            VStack(spacing: 6) {
                ForEach(FieldKey.allCases) { field in
                    FieldDropRow(
                        field: field,
                        assigned: tokens.filter { $0.assignedField == field },
                        onDrop: { idStr in
                            guard let id = UUID(uuidString: idStr),
                                  let i  = tokens.firstIndex(where: { $0.id == id }) else { return false }
                            withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                                tokens[i].assignedField = field
                            }
                            return true
                        },
                        onRemove: { id in
                            guard let i = tokens.firstIndex(where: { $0.id == id }) else { return }
                            withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                                tokens[i].assignedField = nil
                            }
                        }
                    )
                }
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 12)
        }
    }

    // MARK: - Done button

    private var doneButton: some View {
        Button(action: buildContact) {
            Text("save contact  →")
                .font(.mono(16, weight: .black))
                .foregroundStyle(Color.appBg)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 18)
                .background(Color.appAccent)
                .clipShape(RoundedRectangle(cornerRadius: 16))
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 16)
        .background(Color.appBg)
    }

    private func buildContact() {
        func joined(_ key: FieldKey) -> String {
            tokens.filter { $0.assignedField == key }.map(\.text).joined(separator: " ")
        }
        var c = ContactModel()
        c.name    = joined(.name)
        c.title   = joined(.title)
        c.company = joined(.company)
        c.phones  = tokens.filter { $0.assignedField == .phone }.map(\.text)
        c.emails  = tokens.filter { $0.assignedField == .email }.map(\.text)
        c.website = joined(.website)
        c.address = joined(.address)
        onDone(c)
    }
}

// MARK: - Token Pill

struct TokenPill: View {
    let token: OCRToken

    var body: some View {
        Text(token.text)
            .font(.mono(12, weight: .semibold))
            .foregroundStyle(Color(red: 0.08, green: 0.08, blue: 0.08))
            .lineLimit(1)
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(tokenPalette[token.colorIndex % tokenPalette.count])
            .clipShape(RoundedRectangle(cornerRadius: 8))
            .rotationEffect(.degrees(token.rotation))
            .shadow(color: tokenPalette[token.colorIndex % tokenPalette.count].opacity(0.35),
                    radius: 4, x: 0, y: 2)
    }
}

// MARK: - Field drop row

struct FieldDropRow: View {
    let field: FieldKey
    let assigned: [OCRToken]
    let onDrop: (String) -> Bool
    let onRemove: (UUID) -> Void

    @State private var targeted = false

    var body: some View {
        HStack(spacing: 0) {
            // Label
            HStack(spacing: 5) {
                Image(systemName: field.icon)
                    .font(.system(size: 10))
                    .foregroundStyle(Color.appAccent)
                    .frame(width: 16)
                Text(field.label.lowercased())
                    .font(.mono(10, weight: .bold))
                    .foregroundStyle(Color.appMuted)
            }
            .frame(width: 74, alignment: .leading)

            // Drop zone
            ZStack {
                RoundedRectangle(cornerRadius: 10)
                    .fill(targeted ? Color.appAccent.opacity(0.07) : Color.appCard)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .strokeBorder(
                                targeted ? Color.appAccent : Color.appBorder,
                                style: StrokeStyle(
                                    lineWidth: 1.2,
                                    dash: assigned.isEmpty ? [5, 3] : []
                                )
                            )
                    )
                    .animation(.easeInOut(duration: 0.15), value: targeted)

                if assigned.isEmpty {
                    Text("drop here")
                        .font(.mono(9, weight: .medium))
                        .foregroundStyle(Color.appMuted.opacity(0.45))
                } else {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 5) {
                            ForEach(assigned) { token in
                                AssignedChip(token: token, onRemove: { onRemove(token.id) })
                            }
                        }
                        .padding(.horizontal, 8)
                        .padding(.vertical, 7)
                    }
                }
            }
            .frame(minHeight: 40)
            .dropDestination(for: String.self) { items, _ in
                guard let first = items.first else { return false }
                return onDrop(first)
            } isTargeted: { t in
                targeted = t
            }
        }
    }
}

// MARK: - Assigned chip (inside field row)

struct AssignedChip: View {
    let token: OCRToken
    let onRemove: () -> Void

    var body: some View {
        HStack(spacing: 4) {
            Text(token.text)
                .font(.mono(11, weight: .semibold))
                .foregroundStyle(Color(red: 0.08, green: 0.08, blue: 0.08))
                .lineLimit(1)
            Button(action: onRemove) {
                Image(systemName: "xmark")
                    .font(.system(size: 7, weight: .bold))
                    .foregroundStyle(Color(red: 0.25, green: 0.25, blue: 0.25))
            }
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 5)
        .background(tokenPalette[token.colorIndex % tokenPalette.count])
        .clipShape(RoundedRectangle(cornerRadius: 6))
    }
}
