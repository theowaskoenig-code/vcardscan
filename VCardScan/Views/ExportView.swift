import SwiftUI
import Contacts
import ContactsUI

struct ExportView: View {
    let contact: ContactModel
    var onScanAnother: () -> Void

    @State private var showContactVC  = false
    @State private var shareItems: [Any] = []
    @State private var showShare      = false
    @State private var saved          = false

    var displayName: String {
        [contact.name, contact.company].first { !$0.isEmpty } ?? "Contact"
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                // Name hero
                VStack(spacing: 6) {
                    Text("contact")
                        .font(.mono(11, weight: .bold))
                        .foregroundStyle(Color.appAccent)
                    Text(displayName)
                        .font(.mono(26, weight: .black))
                        .foregroundStyle(Color.appText)
                        .multilineTextAlignment(.center)
                    if !contact.title.isEmpty && !contact.name.isEmpty {
                        Text(contact.title)
                            .font(.mono(13, weight: .medium))
                            .foregroundStyle(Color.appMuted)
                    }
                }
                .frame(maxWidth: .infinity)
                .padding(.top, 48)
                .padding(.bottom, 32)

                // Detail card
                VStack(spacing: 0) {
                    if !contact.company.isEmpty && !contact.name.isEmpty {
                        ContactRow(icon: "building.2.fill", label: "company", value: contact.company)
                        rowDivider
                    }
                    if !contact.title.isEmpty && contact.name.isEmpty {
                        ContactRow(icon: "briefcase.fill", label: "title", value: contact.title)
                        rowDivider
                    }
                    ForEach(Array(contact.phones.enumerated()), id: \.offset) { _, p in
                        ContactRow(icon: "phone.fill", label: "phone", value: p)
                        rowDivider
                    }
                    ForEach(Array(contact.emails.enumerated()), id: \.offset) { _, e in
                        ContactRow(icon: "envelope.fill", label: "email", value: e)
                        rowDivider
                    }
                    if !contact.website.isEmpty {
                        ContactRow(icon: "globe", label: "website", value: contact.website)
                        rowDivider
                    }
                    if !contact.address.isEmpty {
                        ContactRow(icon: "location.fill", label: "address", value: contact.address)
                    }
                }
                .background(Color.appCard)
                .clipShape(RoundedRectangle(cornerRadius: 16))
                .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.appBorder, lineWidth: 1))
                .padding(.horizontal, 20)

                // Action buttons
                VStack(spacing: 10) {
                    Button(action: { showContactVC = true }) {
                        HStack(spacing: 8) {
                            Image(systemName: saved ? "checkmark.circle.fill" : "person.badge.plus")
                            Text(saved ? "saved!" : "save to contacts")
                        }
                        .font(.mono(15, weight: .black))
                        .foregroundStyle(Color.appBg)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 18)
                        .background(saved ? Color.green : Color.appAccent)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                        .animation(.spring(response: 0.3), value: saved)
                    }

                    Button(action: prepareShare) {
                        HStack(spacing: 8) {
                            Image(systemName: "square.and.arrow.up")
                            Text("share .vcf")
                        }
                        .font(.mono(14, weight: .bold))
                        .foregroundStyle(Color.appText)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 16)
                        .background(Color.appCard)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.appBorder, lineWidth: 1))
                    }

                    Button(action: onScanAnother) {
                        Text("← scan another")
                            .font(.mono(12, weight: .medium))
                            .foregroundStyle(Color.appMuted)
                            .padding(.vertical, 8)
                    }
                }
                .padding(.horizontal, 20)
                .padding(.top, 24)
                .padding(.bottom, 40)
            }
        }
        .background(Color.appBg.ignoresSafeArea())
        .sheet(isPresented: $showContactVC) {
            ContactSaveSheet(contact: contact) { didSave in
                showContactVC = false
                if didSave { saved = true }
            }
        }
        .sheet(isPresented: $showShare) {
            ActivitySheet(items: shareItems)
        }
    }

    private var rowDivider: some View {
        Divider().background(Color.appBorder).padding(.leading, 48)
    }

    private func prepareShare() {
        let vcf  = buildVCard()
        let url  = FileManager.default.temporaryDirectory
            .appendingPathComponent(
                displayName.replacingOccurrences(of: " ", with: "_") + ".vcf"
            )
        try? vcf.write(to: url, atomically: true, encoding: .utf8)
        shareItems = [url]
        showShare  = true
    }

    private func buildVCard() -> String {
        func esc(_ s: String) -> String {
            s.replacingOccurrences(of: "\\", with: "\\\\")
             .replacingOccurrences(of: ";",  with: "\\;")
             .replacingOccurrences(of: ",",  with: "\\,")
             .replacingOccurrences(of: "\n", with: "\\n")
        }
        let parts = contact.name.split(separator: " ")
        let first = parts.dropLast().joined(separator: " ")
        let last  = parts.last.map(String.init) ?? ""
        var lines = [
            "BEGIN:VCARD", "VERSION:3.0",
            "N:\(esc(last));\(esc(first));;;",
            "FN:\(esc(contact.name.isEmpty ? contact.company : contact.name))"
        ]
        if !contact.company.isEmpty  { lines.append("ORG:\(esc(contact.company))") }
        if !contact.title.isEmpty    { lines.append("TITLE:\(esc(contact.title))") }
        contact.phones.forEach  { lines.append("TEL;TYPE=WORK,VOICE:\(esc($0))") }
        contact.emails.forEach  { lines.append("EMAIL;TYPE=INTERNET,WORK:\(esc($0))") }
        if !contact.website.isEmpty  { lines.append("URL:\(esc(contact.website))") }
        if !contact.address.isEmpty  { lines.append("ADR;TYPE=WORK:;;\(esc(contact.address));;;;") }
        lines.append("END:VCARD")
        return lines.joined(separator: "\r\n") + "\r\n"
    }
}

// MARK: - Contact row

struct ContactRow: View {
    let icon: String
    let label: String
    let value: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 12))
                .foregroundStyle(Color.appAccent)
                .frame(width: 20, height: 20)
                .padding(.top, 2)
            VStack(alignment: .leading, spacing: 2) {
                Text(label)
                    .font(.mono(9, weight: .bold))
                    .foregroundStyle(Color.appMuted)
                Text(value)
                    .font(.mono(13, weight: .medium))
                    .foregroundStyle(Color.appText)
            }
            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
    }
}

// MARK: - ContactsUI sheet

struct ContactSaveSheet: UIViewControllerRepresentable {
    let contact: ContactModel
    var onComplete: (Bool) -> Void

    func makeUIViewController(context: Context) -> UINavigationController {
        let cn = buildCNContact()
        let vc = CNContactViewController(forNewContact: cn)
        vc.contactStore = CNContactStore()
        vc.delegate     = context.coordinator
        return UINavigationController(rootViewController: vc)
    }
    func updateUIViewController(_ uiViewController: UINavigationController, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    class Coordinator: NSObject, CNContactViewControllerDelegate {
        let parent: ContactSaveSheet
        init(_ p: ContactSaveSheet) { parent = p }

        func contactViewController(_ vc: CNContactViewController,
                                   didCompleteWith contact: CNContact?) {
            let saved = contact != nil
            parent.onComplete(saved)
            vc.navigationController?.dismiss(animated: true)
        }
    }

    private func buildCNContact() -> CNMutableContact {
        let cn   = CNMutableContact()
        let parts = contact.name.split(separator: " ")
        cn.givenName        = parts.dropLast().joined(separator: " ")
        cn.familyName       = parts.last.map(String.init) ?? ""
        cn.jobTitle         = contact.title
        cn.organizationName = contact.company
        cn.phoneNumbers     = contact.phones.map {
            CNLabeledValue(label: CNLabelWork, value: CNPhoneNumber(stringValue: $0))
        }
        cn.emailAddresses   = contact.emails.map {
            CNLabeledValue(label: CNLabelWork, value: $0 as NSString)
        }
        if !contact.website.isEmpty {
            cn.urlAddresses = [CNLabeledValue(label: CNLabelWork, value: contact.website as NSString)]
        }
        return cn
    }
}

// MARK: - UIActivityViewController wrapper

struct ActivitySheet: UIViewControllerRepresentable {
    let items: [Any]
    @Environment(\.dismiss) private var dismiss

    func makeUIViewController(context: Context) -> UIActivityViewController {
        let vc = UIActivityViewController(activityItems: items, applicationActivities: nil)
        vc.completionWithItemsHandler = { _, _, _, _ in dismiss() }
        return vc
    }
    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}
