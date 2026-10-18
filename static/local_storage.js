(() => {
    const STORAGE_KEY = "calculateur-moyennes:data:v1";
    const BACKUP_KEY = "calculateur-moyennes:data:v1:backup";
    const stateElement = document.getElementById("server-state");
    let recoveryUi = null;
    let pendingImportState = null;
    let pendingConflict = false;

    if (!stateElement) {
        return;
    }

    function readLocalState() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            return raw === null ? null : JSON.parse(raw);
        } catch (error) {
            console.warn("Impossible de lire le stockage local.", error);
            return null;
        }
    }

    function readRaw(key) {
        try {
            return localStorage.getItem(key);
        } catch (error) {
            console.warn("Impossible de lire le stockage local.", error);
            return null;
        }
    }

    function parseRaw(raw) {
        if (raw === null) return null;
        try {
            return JSON.parse(raw);
        } catch (error) {
            return null;
        }
    }

    function preserveBeforeMutation(nextRaw) {
        const previousRaw = readRaw(STORAGE_KEY);
        if (previousRaw === null || previousRaw === nextRaw) return true;

        try {
            localStorage.setItem(BACKUP_KEY, JSON.stringify({
                saved_at: new Date().toISOString(),
                storage_key: STORAGE_KEY,
                raw: previousRaw,
                data: parseRaw(previousRaw),
            }));
            return true;
        } catch (error) {
            console.error("Sauvegarde de sécurité impossible : les données originales ne seront pas écrasées.", error);
            return false;
        }
    }

    function buildBackupBundle() {
        const raw = readRaw(STORAGE_KEY);
        let serverState = null;
        try {
            serverState = JSON.parse(stateElement.textContent);
        } catch (error) {
            console.warn("Impossible de lire l'état serveur pour l'export.", error);
        }
        return {
            format_version: 1,
            exported_at: new Date().toISOString(),
            local_storage: { key: STORAGE_KEY, raw, data: parseRaw(raw) },
            previous_local_backup: parseRaw(readRaw(BACKUP_KEY)),
            server_state: serverState,
        };
    }

    function addBackupButton() {
        const main = document.querySelector("main");
        if (!main || document.getElementById("download-data-backup")) return;
        const section = document.createElement("section");
        section.className = "section recovery-section";
        const button = document.createElement("button");
        button.id = "download-data-backup";
        button.type = "button";
        button.className = "primary-action";
        button.textContent = "Télécharger une sauvegarde des données";
        const help = document.createElement("p");
        help.className = "recovery-help";
        help.textContent = "La sauvegarde contient la copie du navigateur et l'état serveur.";

        const restoreButton = document.createElement("button");
        restoreButton.type = "button";
        restoreButton.className = "recovery-button";
        restoreButton.textContent = "Restaurer depuis un fichier JSON";
        const previousButton = document.createElement("button");
        previousButton.type = "button";
        previousButton.className = "recovery-button";
        previousButton.textContent = "Restaurer la copie locale précédente";
        const previousBackup = extractBackupState(parseRaw(readRaw(BACKUP_KEY)));
        previousButton.hidden = !previousBackup;
        const fileInput = document.createElement("input");
        fileInput.type = "file";
        fileInput.accept = ".json,application/json";
        fileInput.hidden = true;

        const status = document.createElement("div");
        status.className = "recovery-status";
        status.setAttribute("role", "status");
        status.setAttribute("aria-live", "polite");
        status.hidden = true;
        const retryButton = document.createElement("button");
        retryButton.type = "button";
        retryButton.className = "recovery-button";
        retryButton.textContent = "Réessayer l'import";
        retryButton.hidden = true;

        const actions = document.createElement("div");
        actions.className = "recovery-actions";
        actions.append(button, restoreButton, previousButton, fileInput);
        section.append(actions, help, status, retryButton);
        main.prepend(section);
        recoveryUi = { main, status, retryButton, fileInput, previousButton };

        button.addEventListener("click", () => {
            const blob = new Blob([JSON.stringify(buildBackupBundle(), null, 2)], {
                type: "application/json;charset=utf-8",
            });
            const objectUrl = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = objectUrl;
            link.download = "sauvegarde-calculateur-moyennes-" + new Date().toISOString().slice(0, 10) + ".json";
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(objectUrl);
        });

        restoreButton.addEventListener("click", () => fileInput.click());
        previousButton.addEventListener("click", async () => {
            const backup = extractBackupState(parseRaw(readRaw(BACKUP_KEY)));
            if (!backup) {
                previousButton.hidden = true;
                setRecoveryMessage("Aucune copie locale précédente n'est disponible.");
                return;
            }
            const counts = describeState(backup);
            if (!window.confirm(
                `Restaurer la copie précédente (${counts.subjects} matière(s), ${counts.grades} note(s)) ? ` +
                "L'état actuel du serveur sera remplacé si l'import réussit."
            )) return;
            await importState(backup);
        });
        fileInput.addEventListener("change", async () => {
            const file = fileInput.files?.[0];
            fileInput.value = "";
            if (!file) return;
            try {
                if (file.size > 2 * 1024 * 1024) {
                    setRecoveryMessage("Ce fichier dépasse la limite de 2 Mo. Aucune donnée n'a été modifiée.");
                    return;
                }
                const backup = JSON.parse(await file.text());
                const state = extractBackupState(backup);
                if (!state) {
                    setRecoveryMessage("Ce fichier ne contient pas de carnet de notes reconnu. Aucune donnée n'a été modifiée.");
                    return;
                }
                const counts = describeState(state);
                if (!window.confirm(
                    `Importer ${counts.subjects} matière(s) et ${counts.grades} note(s) dans ce profil ? ` +
                    "L'état actuel du serveur sera remplacé si l'import réussit."
                )) return;
                await importState(state);
            } catch (error) {
                console.warn("Impossible de lire la sauvegarde sélectionnée.", error);
                setRecoveryMessage("Le fichier est illisible ou invalide. Les données actuelles restent inchangées.");
            }
        });

        retryButton.addEventListener("click", async () => {
            if (!pendingImportState) return;
            if (pendingConflict && !window.confirm(
                "Le serveur contient des données plus récentes. Remplacer ces données par la copie sélectionnée ?"
            )) return;
            await importState(pendingImportState);
        });
    }

    function setRecoveryMessage(message, { showRetry = false, lockEditing = false } = {}) {
        if (!recoveryUi) return;
        recoveryUi.status.textContent = message;
        recoveryUi.status.hidden = false;
        recoveryUi.retryButton.hidden = !showRetry;
        recoveryUi.main.dataset.syncPending = lockEditing ? "true" : "false";
    }

    function refreshPreviousRestoreAvailability() {
        if (!recoveryUi) return;
        recoveryUi.previousButton.hidden = !extractBackupState(parseRaw(readRaw(BACKUP_KEY)));
    }

    function extractBackupState(backup) {
        const candidates = [
            backup?.local_storage?.data,
            parseRaw(backup?.local_storage?.raw),
            backup?.previous_local_backup?.data,
            parseRaw(backup?.previous_local_backup?.raw),
            backup?.server_state,
            backup,
        ];
        return candidates.find((candidate) => (
            candidate !== null
            && typeof candidate === "object"
            && !Array.isArray(candidate)
            && candidate.notes !== null
            && typeof candidate.notes === "object"
            && !Array.isArray(candidate.notes)
            && candidate.coef !== null
            && typeof candidate.coef === "object"
            && !Array.isArray(candidate.coef)
        )) || null;
    }

    function describeState(state) {
        const notes = state?.notes && typeof state.notes === "object" && !Array.isArray(state.notes)
            ? state.notes
            : {};
        return {
            subjects: Object.keys(notes).length,
            grades: Object.values(notes).reduce(
                (total, grades) => total + (Array.isArray(grades) ? grades.length : 0),
                0
            ),
        };
    }

    function writeLocalState(state) {
        let raw;
        try {
            raw = JSON.stringify(state);
        } catch (error) {
            console.warn("Impossible de préparer les données locales.", error);
            return false;
        }
        if (!preserveBeforeMutation(raw)) return false;
        try {
            localStorage.setItem(STORAGE_KEY, raw);
            return true;
        } catch (error) {
            console.warn("Impossible d'écrire dans localStorage ; la copie précédente est conservée.", error);
            return false;
        }
    }

    // L'ordre des clés JSON n'a pas de signification fonctionnelle.
    function normaliserPourComparaison(value) {
        if (Array.isArray(value)) {
            return value.map(normaliserPourComparaison);
        }
        if (value !== null && typeof value === "object") {
            return Object.keys(value).sort().reduce((result, key) => {
                result[key] = normaliserPourComparaison(value[key]);
                return result;
            }, {});
        }
        return value;
    }

    function sameState(first, second) {
        return JSON.stringify(normaliserPourComparaison(first))
            === JSON.stringify(normaliserPourComparaison(second));
    }

    function cleanSyncParameter(url) {
        url.searchParams.delete("sync");
        return url.toString();
    }

    async function envoyerEtatAuServeur(state, version) {
        const response = await fetch("/api/synchroniser", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')?.content || "",
                "If-Match": '"' + version + '"',
            },
            body: JSON.stringify(state),
        });

        if (!response.ok) {
            const error = new Error("La synchronisation a échoué (" + response.status + ").");
            error.status = response.status;
            try {
                error.payload = await response.json();
            } catch (parseError) {
                error.payload = null;
            }
            throw error;
        }

        return response.json();
    }

    async function importState(state) {
        pendingImportState = state;
        pendingConflict = false;
        try {
            const savedState = await envoyerEtatAuServeur(state, stateElement.dataset.version);
            stateElement.dataset.version = String(Number(stateElement.dataset.version) + 1);
            pendingConflict = false;
            const localSaved = writeLocalState(savedState);
            refreshPreviousRestoreAvailability();
            setRecoveryMessage(
                localSaved
                    ? "Import réussi. Les données enregistrées sur le serveur sont rechargées."
                    : "Import réussi sur le serveur, mais le navigateur n'a pas pu actualiser sa copie locale. Télécharge une sauvegarde avant de quitter cette page."
            );
            window.location.reload();
        } catch (error) {
            console.warn("Import des données impossible ; la copie source est conservée.", error);
            if (error.status === 409 && error.payload?.version !== undefined) {
                stateElement.dataset.version = String(error.payload.version);
                if (error.payload.data) {
                    stateElement.textContent = JSON.stringify(error.payload.data);
                }
                pendingConflict = true;
                const localCounts = describeState(state);
                const serverCounts = describeState(error.payload.data || {});
                setRecoveryMessage(
                    `Conflit : la copie à importer contient ${localCounts.subjects} matière(s) et ${localCounts.grades} note(s); le serveur en contient actuellement ${serverCounts.subjects} et ${serverCounts.grades}. Réessaie pour confirmer le remplacement.`,
                    { showRetry: true, lockEditing: stateElement.dataset.initialized === "false" }
                );
                return;
            }
            const reason = error.payload?.error || error.message || "erreur réseau";
            setRecoveryMessage(
                `L'import a échoué (${reason}). La copie de départ n'a pas été effacée. Réessaie ou restaure un fichier JSON.`,
                { showRetry: error.status !== 400, lockEditing: stateElement.dataset.initialized === "false" }
            );
        }
    }

    async function initialiserStockageLocal() {
        let serverState;
        try {
            serverState = JSON.parse(stateElement.textContent);
        } catch (error) {
            console.warn("État serveur invalide.", error);
            return;
        }

        const localState = readLocalState();
        const alreadyInitialized = stateElement.dataset.initialized === "true";

        if (!alreadyInitialized) {
            // Migration unique : on importe l'ancien état du navigateur. Si
            // aucune copie locale n'existe, on initialise le profil avec l'état serveur.
            try {
                const savedState = await envoyerEtatAuServeur(
                    localState ?? serverState,
                    stateElement.dataset.version
                );
                const localSaved = writeLocalState(savedState);
                refreshPreviousRestoreAvailability();
                pendingImportState = null;
                pendingConflict = false;
                if (!localSaved) {
                    setRecoveryMessage("Les données sont enregistrées sur le serveur, mais le navigateur n'a pas pu actualiser sa copie locale. Télécharge une sauvegarde.");
                }
                window.location.reload();
            } catch (error) {
                // Ne jamais remplacer la copie locale avant que l'import soit confirmé.
                console.warn("Import initial impossible ; les données locales sont conservées.", error);
                pendingImportState = localState ?? serverState;
                if (error.status === 409 && error.payload?.version !== undefined) {
                    stateElement.dataset.version = String(error.payload.version);
                    if (error.payload.data) {
                        stateElement.textContent = JSON.stringify(error.payload.data);
                    }
                    pendingConflict = true;
                    const localCounts = describeState(pendingImportState);
                    const serverCounts = describeState(error.payload.data || {});
                    setRecoveryMessage(
                        `Un autre navigateur a initialisé ce profil. Ta copie contient ${localCounts.subjects} matière(s) et ${localCounts.grades} note(s); le serveur en contient ${serverCounts.subjects} et ${serverCounts.grades}. Télécharge une sauvegarde ou confirme l'import local.`,
                        { showRetry: true, lockEditing: true }
                    );
                } else {
                    pendingConflict = false;
                    const reason = error.payload?.error || error.message || "erreur réseau";
                    setRecoveryMessage(
                        `L'import initial a échoué (${reason}). Tes données locales sont conservées. Réessaie ou restaure un fichier JSON.`,
                        { showRetry: true, lockEditing: true }
                    );
                }
            }
            return;
        }

        // Après l'import initial, PostgreSQL est la source de vérité.
        if (localState === null || !sameState(localState, serverState)) {
            const previousLocalCopyExists = readRaw(STORAGE_KEY) !== null;
            if (!writeLocalState(serverState)) {
                setRecoveryMessage("La copie du navigateur diffère des données serveur et n'a pas pu être actualisée. Elle reste conservée; télécharge une sauvegarde avant de la remplacer.");
            } else if (previousLocalCopyExists) {
                refreshPreviousRestoreAvailability();
                setRecoveryMessage("Les données du navigateur différaient du serveur. La copie locale précédente a été sauvegardée; tu peux la restaurer ou télécharger une sauvegarde.");
            } else {
                refreshPreviousRestoreAvailability();
            }
        }
    }

    async function recupererEtatApresModification() {
        const response = await fetch("/api/etat", { cache: "no-store" });
        if (!response.ok) {
            throw new Error("Impossible de récupérer l'état du serveur.");
        }
        return response.json();
    }

    document.addEventListener("submit", async (event) => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement) || form.method.toLowerCase() !== "post") {
            return;
        }
        if (recoveryUi?.main.dataset.syncPending === "true") {
            event.preventDefault();
            setRecoveryMessage("Termine la récupération des données avant de modifier ce profil.", {
                showRetry: Boolean(pendingImportState),
                lockEditing: true,
            });
            return;
        }
        if (form.dataset.nativeSubmit === "true" || form.dataset.submitting === "true") {
            return;
        }

        event.preventDefault();
        form.dataset.submitting = "true";

        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
        }

        let response;
        try {
            response = await fetch(form.action, {
                method: "POST",
                headers: {
                    "If-Match": '"' + stateElement.dataset.version + '"',
                },
                body: new FormData(form),
            });
        } catch (error) {
            console.warn("La soumission JavaScript a échoué.", error);
            form.dataset.submitting = "false";
            if (submitButton) {
                submitButton.disabled = false;
            }
            form.dataset.nativeSubmit = "true";
            form.submit();
            return;
        }

        if (response.status === 409) {
            let conflict;
            try {
                conflict = await response.json();
            } catch (error) {
                conflict = null;
            }
            if (conflict?.data) {
                writeLocalState(conflict.data);
            }
            window.alert("Ce profil a changé dans un autre onglet ou appareil. Les dernières données ont été rechargées; recommence ta modification.");
            window.location.reload();
            return;
        }

        if (response.redirected) {
            const redirectUrl = new URL(response.url);
            if (redirectUrl.searchParams.get("sync") !== "0") {
                try {
                    const state = await recupererEtatApresModification();
                    // En cas d'échec d'écriture, on garde l'ancienne copie :
                    // la supprimer empêcherait toute récupération locale.
                    writeLocalState(state);
                } catch (error) {
                    console.warn("Impossible de mettre à jour le stockage local ; aucune donnée locale n'est supprimée.", error);
                }
            }
            window.location.assign(cleanSyncParameter(redirectUrl));
            return;
        }

        const html = await response.text();
        document.open();
        document.write(html);
        document.close();
    });

    addBackupButton();
    initialiserStockageLocal();
})();
