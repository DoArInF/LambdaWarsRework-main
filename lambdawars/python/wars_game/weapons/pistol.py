from entities import entity
from core.weapons import WarsWeaponMachineGun, VECTOR_CONE_PRECALCULATED

@entity('weapon_pistol', networked=True)
class WeaponPistol(WarsWeaponMachineGun):
    def __init__(self):
        super().__init__()
        
        self.bulletspread = VECTOR_CONE_PRECALCULATED

    clientclassname = 'weapon_pistol'
    muzzleoptions = 'PISTOL MUZZLE'

    class AttackPrimary(WarsWeaponMachineGun.AttackPrimary):
        minrange = 24.0
        maxrange = 640.0
        attackspeed = 0.59
        cone = WarsWeaponMachineGun.AttackPrimary.DOT_3DEGREE
        attributes = ['bullet']
