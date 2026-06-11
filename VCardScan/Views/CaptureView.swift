import SwiftUI
import PhotosUI

struct CaptureView: View {
    var onImageSelected: (UIImage) -> Void

    @State private var showActionSheet = false
    @State private var showCamera      = false
    @State private var showLibrary     = false
    @State private var libraryItem: PhotosPickerItem?
    @State private var pulse           = false

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            // App wordmark
            VStack(alignment: .leading, spacing: -4) {
                Text("vcard")
                    .font(.mono(52, weight: .black))
                    .foregroundStyle(Color.appText)
                Text("scan")
                    .font(.mono(52, weight: .black))
                    .foregroundStyle(Color.appAccent)
                    .padding(.leading, 28)
            }
            .padding(.bottom, 56)

            // Viewfinder card
            Button { showActionSheet = true } label: {
                ZStack {
                    RoundedRectangle(cornerRadius: 24)
                        .fill(Color.appCard)
                        .overlay(
                            RoundedRectangle(cornerRadius: 24)
                                .strokeBorder(
                                    Color.appAccent.opacity(pulse ? 0.55 : 0.2),
                                    lineWidth: 1.5
                                )
                        )
                        .frame(width: 220, height: 140)
                        .shadow(color: Color.appAccent.opacity(pulse ? 0.18 : 0.05), radius: 20)

                    VStack(spacing: 14) {
                        Image(systemName: "viewfinder")
                            .font(.system(size: 44, weight: .ultraLight))
                            .foregroundStyle(Color.appAccent)
                            .scaleEffect(pulse ? 1.06 : 1.0)

                        Text("tap to scan")
                            .font(.mono(12, weight: .medium))
                            .foregroundStyle(Color.appMuted)
                    }
                }
            }
            .buttonStyle(.plain)

            Spacer()
            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.appBg.ignoresSafeArea())
        .onAppear {
            withAnimation(.easeInOut(duration: 1.8).repeatForever(autoreverses: true)) {
                pulse = true
            }
        }
        .confirmationDialog("Scan Business Card", isPresented: $showActionSheet, titleVisibility: .visible) {
            Button("Camera") { showCamera = true }
            Button("Photo Library") { showLibrary = true }
        }
        .fullScreenCover(isPresented: $showCamera) {
            ImagePickerController(source: .camera, onPick: { img in
                showCamera = false
                onImageSelected(img)
            }, onCancel: { showCamera = false })
            .ignoresSafeArea()
        }
        .photosPicker(isPresented: $showLibrary, selection: $libraryItem, matching: .images)
        .onChange(of: libraryItem) { _, item in
            guard let item else { return }
            Task {
                if let data = try? await item.loadTransferable(type: Data.self),
                   let img  = UIImage(data: data) {
                    onImageSelected(img)
                }
                libraryItem = nil
            }
        }
    }
}

// MARK: - UIImagePickerController wrapper

struct ImagePickerController: UIViewControllerRepresentable {
    var source: UIImagePickerController.SourceType
    var onPick: (UIImage) -> Void
    var onCancel: () -> Void

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let vc = UIImagePickerController()
        vc.sourceType = source
        vc.delegate   = context.coordinator
        return vc
    }
    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let parent: ImagePickerController
        init(_ p: ImagePickerController) { parent = p }

        func imagePickerController(_ picker: UIImagePickerController,
                                   didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]) {
            if let img = info[.originalImage] as? UIImage { parent.onPick(img) }
        }
        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            parent.onCancel()
        }
    }
}
