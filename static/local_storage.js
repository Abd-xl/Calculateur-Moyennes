(() => {
    const STORAGE_KEY = "calculateur-moyennes:data:v1";
    const BACKUP_KEY = "calculateur-moyennes:data:v1:backup";
    const stateElement = document.getElementById("server-state");

    if (!stateElement) {
        return;
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

    function readLocalState() {
        const raw = readRaw(STORAGE_KEY);
        if (raw === null) return null;
        try {
            return JSON.parse(raw);
        } catch (error) {
            console.warn("Le stockage local contient un JSON invalide ; la copie brute est conservée.", error);
            return null;
        }
    }

    // Avant toute modification, conserver la valeur précédente dans une clé distincte.
    // Si la sauvegarde échoue, ne pas écraser la valeur originale.
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

    function cleanSyncParameter(url) {
        url.searchParams.delete("sync");
        return url.toString();
    }

    function buildBackupBundle() {
        const raw = readRaw(STORAGE_KEY);
        const backupRaw = readRaw(BACKUP_KEY);
        let serverState = null;

        try {
            serverState = JSON.parse(stateElement.textContent);
        } catch (error) {
            console.warn("Impossible de lire l'état serveur pour l'export.", error);
        }

        return {
            format_version: 1,
            exported_at: new Date().toISOString(),
            note: "Conserve ce fichier hors du navigateur. Il contient les données locales et la dernière copie précédente disponible.",
            local_storage: {
                key: STORAGE_KEY,
                raw,
                data: parseRaw(raw),
            },
            previous_local_backup: parseRaw(backupRaw),
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
        help.textContent = "Exporte les données locales, la dernière copie de sécurité et l'état serveur dans un fichier JSON.";

        button.addEventListener("click", () => {
            const bundle = buildBackupBundle();
            const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json;charset=utf-8" });
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

    async function synchroniserAvecLeServeur(localState) {
        const response = await fetch("/api/synchroniser", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(localState),
        });

        if (!response.ok) {
            throw new Error("La synchronisation a échoué (" + response.status + ").");
        }

        window.location.reload();
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

        if (localState === null) {
            // Si la clé existe mais que son JSON est invalide, ne pas remplacer
            // la valeur brute : l'export de sauvegarde permettra de la récupérer.
            if (readRaw(STORAGE_KEY) !== null) return;
            writeLocalState(serverState);
            return;
        }

        if (!sameState(localState, serverState)) {
            try {
                await synchroniserAvecLeServeur(localState);
            } catch (error) {
                // Ne jamais supprimer les données locales en cas d'échec réseau ou serveur.
                console.warn("Impossible de synchroniser les données ; la copie locale est conservée.", error);
            }
        }
    }

    function sameState(first, second) {
        return JSON.stringify(first) === JSON.stringify(second);
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

        if (!(form instanceof HTMLFormElement) || form.method.toLowerCase() !== "post") return;
        if (form.dataset.nativeSubmit === "true" || form.dataset.submitting === "true") return;

        event.preventDefault();
        form.dataset.submitting = "true";

        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) submitButton.disabled = true;

        let response;
        try {
            response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
            });
        } catch (error) {
            console.warn("La soumission JavaScript a échoué.", error);
            form.dataset.submitting = "false";
            if (submitButton) submitButton.disabled = false;
            form.dataset.nativeSubmit = "true";
            form.submit();
            return;
        }

        if (response.redirected) {
            const redirectUrl = new URL(response.url);
            if (redirectUrl.searchParams.get("sync") !== "0") {
                try {
                    const state = await recupererEtatApresModification();
                    // Si la copie de sécurité ou l'écriture échoue, on garde la valeur locale existante.
                    writeLocalState(state);
                } catch (error) {
                    console.warn("Impossible de mettre à jour le stockage local ; les données existantes sont conservées.", error);
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
