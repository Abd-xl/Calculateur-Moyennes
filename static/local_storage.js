(() => {
    const STORAGE_KEY = "calculateur-moyennes:data:v1";
    const BACKUP_KEY = "calculateur-moyennes:data:v1:backup";
    const stateElement = document.getElementById("server-state");

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
        section.className = "section";
        const button = document.createElement("button");
        button.id = "download-data-backup";
        button.type = "button";
        button.className = "primary-action";
        button.textContent = "Télécharger une sauvegarde des données";
        button.style.cursor = "pointer";
        button.style.border = "0";
        button.style.font = "inherit";
        button.style.width = "100%";
        const help = document.createElement("p");
        help.className = "action__description";
        help.textContent = "Exporte les données locales, la copie précédente et l'état serveur dans un fichier JSON.";
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
        section.appendChild(button);
        section.appendChild(help);
        main.prepend(section);
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
                writeLocalState(savedState);
                window.location.reload();
            } catch (error) {
                if (error.status === 409 && error.payload?.data) {
                    writeLocalState(error.payload.data);
                    window.alert("Ce profil a été synchronisé ailleurs. Les données serveur les plus récentes sont chargées; vérifie-les avant de continuer.");
                    window.location.reload();
                    return;
                }
                // Ne jamais effacer la copie locale si l'import échoue.
                console.warn("Import initial impossible ; les données locales sont conservées.", error);
            }
            return;
        }

        // Après l'import initial, PostgreSQL est la source de vérité.
        if (localState === null || !sameState(localState, serverState)) {
            writeLocalState(serverState);
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
