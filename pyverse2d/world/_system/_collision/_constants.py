# ======================================== CORRECTION DE POSITION ========================================
_SLOP: float = 0.5              # penetration minimale ignorée en mètres
_BAUMGARTE: float = 0.2         # facteur de correction de position par frame
_MAX_CORRECTION: float = 8.0    # correction de position maximale par frame en pixels
_MAX_MASS_RATIO: float = 0.95   # ratio masse max pour éviter la correction asymétrique

# ======================================== WARM START ========================================
_WARM_BIAS: float = 0.7         # fraction des impulsions précédentes réappliquées

# ======================================== ITERATIONS ========================================
_EXTRA_ITER_THRESHOLD: float = 4.0      # profondeur de pénétration déclenchant les itérations supplémentaires
_EXTRA_ITER: int = 4                    # nombre d'itérations supplémentaires ajoutées

# ======================================== RESTITUTION ========================================
_RESTITUTION_THRESHOLD: float = 1.0     # vitesse minimale en m/s pour appliquer la restitution
_RESTITUTION_MAX_VEL: float = 10.0      # vitesse en m/s à partir de laquelle la restitution est pleine