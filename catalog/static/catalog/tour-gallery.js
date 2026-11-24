const tourGallery = document.querySelector("[data-tour-gallery]");

if (tourGallery && typeof FormDataEvent === "function") {
    const form = tourGallery.closest("form");
    const grid = tourGallery.querySelector("[data-gallery-grid]");
    const input = tourGallery.querySelector('input[type="file"]');
    const order = form.elements.photo_order;
    const revision = form.elements.revision;
    const submit = form.querySelector('button[type="submit"]');
    const galleryError = tourGallery.querySelector("[data-gallery-error]");
    const photoTemplate = tourGallery.querySelector("[data-gallery-photo]");
    const buttonTemplate = tourGallery.querySelector("[data-gallery-buttons]");
    const status = tourGallery.querySelector("[data-gallery-status]");
    const previews = new Map();
    let dragged = null;
    let deleting = false;
    const dialog = tourGallery.querySelector("[data-gallery-dialog]");
    const fullImage = dialog.querySelector("[data-gallery-full-image]");
    const confirmDialog = tourGallery.querySelector("[data-photo-confirm]");
    const confirmText = confirmDialog.querySelector("[data-photo-confirm-text]");
    let orderedUploads = [];

    function enableMoving(card) {
        card.draggable = true;
        card.append(buttonTemplate.content.cloneNode(true));
        const fallback = card.querySelector("[data-photo-delete-fallback]");
        if (fallback && !fallback.querySelector("input").checked) fallback.hidden = true;
    }

    function syncGallery() {
        const files = [];
        const keys = [];
        const cards = Array.from(grid.children);

        cards.forEach((card, index) => {
            const preview = previews.get(card);
            const markedForDeletion = card.querySelector('input[type="checkbox"]:checked');

            card.querySelector("[data-photo-cover]").hidden = keys.length > 0 || Boolean(markedForDeletion);
            card.querySelector('[data-photo-move="-1"]').disabled = index === 0;
            card.querySelector('[data-photo-move="1"]').disabled = index === cards.length - 1;

            if (preview) {
                keys.push(`new-${files.length}`);
                files.push(preview.file);
            } else if (!markedForDeletion) {
                keys.push(card.dataset.photoKey);
            }
        });

        orderedUploads = files;
        order.value = JSON.stringify(keys);
        tourGallery.querySelector("[data-gallery-hint]").hidden = !cards.length;
    }

    function movePhoto(card, target) {
        const cards = Array.from(grid.children);
        if (!target || target === card) return;

        if (cards.indexOf(card) < cards.indexOf(target)) {
            target.after(card);
        } else {
            target.before(card);
        }
        card.scrollIntoView({ block: "nearest", inline: "nearest" });
        syncGallery();
        status.textContent = `Фото перемещено на позицию ${Array.from(grid.children).indexOf(card) + 1}.`;
    }

    function confirmPhotoRemoval(isNew) {
        const message = isNew
            ? "Фото будет убрано из списка загрузки."
            : "Фото сразу исчезнет из галереи тура.";

        if (typeof confirmDialog.showModal !== "function") {
            return Promise.resolve(window.confirm(`Удалить фото? ${message}`));
        }

        confirmText.textContent = message;
        confirmDialog.returnValue = "";

        return new Promise(resolve => {
            confirmDialog.addEventListener("close", () => {
                resolve(confirmDialog.returnValue === "delete");
            }, { once: true });

            confirmDialog.showModal();
        });
    }

    async function removePhoto(card, button) {
        if (deleting || confirmDialog.open) return;

        const preview = previews.get(card);
        if (!await confirmPhotoRemoval(Boolean(preview))) return;

        galleryError.hidden = true;
        if (preview) {
            URL.revokeObjectURL(preview.url);
            previews.delete(card);
        } else {
            deleting = true;
            button.disabled = true;
            submit.disabled = true;

            const failureMessage = "Не удалось удалить фото. Попробуйте ещё раз.";
            try {
                const body = new URLSearchParams({
                    csrfmiddlewaretoken: form.elements.csrfmiddlewaretoken.value,
                    revision: revision.value,
                });
                const response = await fetch(card.dataset.photoDeleteUrl, { method: "POST", body });

                if (response.status === 409) {
                    const result = await response.json();
                    galleryError.textContent = result.error;
                    galleryError.hidden = false;
                    return;
                }
                if (!response.ok) throw new Error(failureMessage);

                const result = await response.json();
                revision.value = result.revision;
            } catch {
                galleryError.textContent = failureMessage;
                galleryError.hidden = false;
                return;
            } finally {
                deleting = false;
                button.disabled = false;
                submit.disabled = false;
            }
        }

        const nextCard = card.nextElementSibling || card.previousElementSibling;
        card.remove();
        syncGallery();
        status.textContent = preview ? "Фото убрано из загрузки." : "Фото удалено.";
        const nextControl = nextCard?.querySelector("[data-photo-remove]") || input;
        nextControl.focus();
    }

    const savedCards = new Map(Array.from(grid.children, card => [card.dataset.photoKey, card]));
    let previousOrder;
    try {
        previousOrder = JSON.parse(order.value);
    } catch {
        previousOrder = [];
    }

    if (Array.isArray(previousOrder)) {
        for (const key of previousOrder) {
            const card = savedCards.get(key);
            if (card) grid.append(card);
        }
    }

    for (const card of grid.children) enableMoving(card);

    input.addEventListener("change", () => {
        const chosen = Array.from(input.files);
        input.value = "";

        for (const file of chosen) {
            const card = photoTemplate.content.firstElementChild.cloneNode(true);
            const url = URL.createObjectURL(file);

            previews.set(card, { file, url });
            card.querySelector("[data-photo-preview]").href = url;
            card.querySelector("img").src = url;
            enableMoving(card);
            grid.append(card);
        }

        syncGallery();
        if (chosen.length) {
            grid.lastElementChild.scrollIntoView({ block: "nearest", inline: "nearest" });
        }
    });

    grid.addEventListener("change", syncGallery);

    grid.addEventListener("click", event => {
        const card = event.target.closest(".manager-photo");
        if (!card) return;

        const preview = event.target.closest("[data-photo-preview]");
        if (preview && typeof dialog.showModal === "function") {
            event.preventDefault();
            fullImage.src = preview.href;
            fullImage.alt = preview.querySelector("img").alt;
            dialog.showModal();
            return;
        }

        const button = event.target.closest("[data-photo-move]");
        if (button) {
            const target = button.dataset.photoMove === "-1" ? card.previousElementSibling : card.nextElementSibling;
            movePhoto(card, target);
            const focus = button.disabled ? card.querySelector("[data-photo-move]:not(:disabled)") : button;
            focus?.focus({ preventScroll: true });
        }

        const removeButton = event.target.closest("[data-photo-remove]");
        if (removeButton) removePhoto(card, removeButton);
    });

    grid.addEventListener("dragstart", event => {
        dragged = event.target.closest(".manager-photo");
        if (!dragged) return;

        event.dataTransfer.setData("text/plain", "photo");
        event.dataTransfer.effectAllowed = "move";
        dragged.classList.add("is-dragging");
    });

    grid.addEventListener("dragover", event => {
        const target = event.target.closest(".manager-photo");
        if (!dragged || !target || target === dragged) return;

        event.preventDefault();
        grid.querySelector(".is-drop-target")?.classList.remove("is-drop-target");
        target.classList.add("is-drop-target");
        event.dataTransfer.dropEffect = "move";
    });

    grid.addEventListener("drop", event => {
        if (!dragged) return;

        event.preventDefault();
        movePhoto(dragged, event.target.closest(".manager-photo"));
    });

    grid.addEventListener("dragend", () => {
        dragged?.classList.remove("is-dragging");
        grid.querySelector(".is-drop-target")?.classList.remove("is-drop-target");
        dragged = null;
    });

    form.addEventListener("submit", event => {
        if (deleting) {
            event.preventDefault();
            return;
        }
        syncGallery();
    });

    dialog.querySelector("[data-gallery-close]").addEventListener("click", () => dialog.close());
    dialog.addEventListener("close", () => fullImage.removeAttribute("src"));
    confirmDialog.querySelector("[data-photo-confirm-cancel]").addEventListener("click", () => {
        confirmDialog.close();
    });
    confirmDialog.querySelector("[data-photo-confirm-delete]").addEventListener("click", () => {
        confirmDialog.close("delete");
    });

    form.addEventListener("formdata", event => {
        event.formData.delete(input.name);
        for (const file of orderedUploads) {
            event.formData.append(input.name, file, file.name);
        }
    });

    tourGallery.classList.add("manager-gallery-ready");
    syncGallery();
}