const directionPhoto = document.querySelector("[data-direction-photo]");

if (directionPhoto) {
    const input = directionPhoto.querySelector('input[type="file"]');
    const select = directionPhoto.querySelector("[data-photo-select]");
    const preview = directionPhoto.querySelector("[data-photo-preview]");
    const image = directionPhoto.querySelector("[data-photo-image]");
    const caption = directionPhoto.querySelector("[data-photo-caption]");
    const error = directionPhoto.querySelector("[data-photo-error]");
    const opener = directionPhoto.querySelector("[data-photo-open]");
    const dialog = directionPhoto.querySelector("dialog");
    const fullPhoto = dialog.querySelector("[data-photo-full]");
    const currentPhoto = image.getAttribute("src");
    let previewUrl = null;

    function showError() {
        if (!image.getAttribute("src")) return;
        preview.hidden = true;
        error.hidden = false;
    }

    function updatePreview() {
        if (previewUrl) URL.revokeObjectURL(previewUrl);
        const file = input.files[0];
        previewUrl = file ? URL.createObjectURL(file) : null;
        const source = previewUrl || currentPhoto;
        preview.hidden = !source;
        error.hidden = true;
        caption.textContent = file ? "Новое фото · сохранится после нажатия «Сохранить»" : "Текущее фото";
        if (source && image.getAttribute("src") !== source) {
            image.src = source;
        } else if (!source) {
            image.removeAttribute("src");
        }
        if (source && image.complete && !image.naturalWidth) showError();
    }

    input.addEventListener("change", updatePreview);
    image.addEventListener("error", showError);
    image.addEventListener("load", () => {
        preview.hidden = false;
        error.hidden = true;
    });
    input.classList.add("sr-only");
    select.hidden = false;
    updatePreview();

    if (typeof dialog.showModal === "function") {
        opener.disabled = false;
        opener.addEventListener("click", () => {
            fullPhoto.src = image.src;
            dialog.showModal();
        });
        dialog.querySelector("[data-photo-close]").addEventListener("click", () => dialog.close());
        dialog.addEventListener("close", () => fullPhoto.removeAttribute("src"));
    }
}
