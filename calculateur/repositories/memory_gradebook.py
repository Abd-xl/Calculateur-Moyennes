"""Cache mémoire temporaire des carnets, réhydraté depuis le navigateur.

Le cache ne constitue pas une persistance durable : localStorage reste la source
de récupération et les sauvegardes JSON restent sous le contrôle de l'utilisateur.
"""

from collections import OrderedDict
from copy import deepcopy
from threading import RLock

from calculateur.services.validation import validate_data


EMPTY_GRADEBOOK = {"notes": {}, "coef": {}}


class GradebookConflictError(Exception):
    """Une autre requête a modifié le carnet depuis la version attendue."""


class InMemoryGradebookRepository:
    """Stocke temporairement les carnets dans le processus Flask courant."""

    def __init__(self, max_profiles=1000):
        if isinstance(max_profiles, bool) or not isinstance(max_profiles, int) or max_profiles < 1:
            raise ValueError("max_profiles doit être un entier positif.")
        self.max_profiles = max_profiles
        self._profiles = OrderedDict()
        self._lock = RLock()

    def _get_or_create(self, profile_id):
        profile = self._profiles.get(profile_id)
        if profile is None:
            profile = {
                "data": deepcopy(EMPTY_GRADEBOOK),
                "initialized": False,
                "version": 1,
            }
            self._profiles[profile_id] = profile
        else:
            self._profiles.move_to_end(profile_id)

        while len(self._profiles) > self.max_profiles:
            # Un profil évincé pourra être rechargé depuis le localStorage
            # de son navigateur lors de sa prochaine visite.
            self._profiles.popitem(last=False)

        return profile

    def load(self, profile_id):
        if not profile_id:
            raise ValueError("Identifiant de profil manquant.")
        with self._lock:
            return deepcopy(self._get_or_create(profile_id))

    def save(self, profile_id, data, expected_version):
        if not profile_id:
            raise ValueError("Identifiant de profil manquant.")
        validate_data(data)

        with self._lock:
            profile = self._get_or_create(profile_id)
            if profile["version"] != expected_version:
                raise GradebookConflictError

            profile["data"] = deepcopy(data)
            profile["initialized"] = True
            profile["version"] += 1
            return profile["version"]
