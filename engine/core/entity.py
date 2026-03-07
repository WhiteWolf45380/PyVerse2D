# ======================================== IMPORTS ========================================

# ======================================== CLASSE ABSTRAITE ========================================
class Entity:
    """Classe représentant les entités en accumulant des composants"""
    _NEXT_ID = 0
    def __init__(self):
        self._id = self._NEXT_ID
        self._NEXT_ID += 1
    
    def get_id(self):
        """Renvoie l'id de l'entité"""
        return self._id