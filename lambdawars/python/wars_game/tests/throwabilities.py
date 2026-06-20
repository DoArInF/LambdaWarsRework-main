from srctests.gametestsuite import GameTestSuite
from srctests.gametestcase import GenericGameTestCase

from vmath import Vector
from core.abilities.throwobject import AbilityThrowObject, IsGroundTargetWithinUnitRadius
from wars_game.abilities.throwmolotov import AbilityThrowMolotov
from wars_game.abilities.throwstinkbomb import AbilityThrowStinkBomb


def CreateThrowAbilitiesTestSuite():
    suite = GameTestSuite()
    suite.addTest(ThrowAbilitiesRegressionTestCase())
    return suite


class ThrowAbilitiesRegressionTestCase(GenericGameTestCase):
    def setUp(self):
        super().setUp()
        self.testsleft = [
            (self.testStinkBombDoesNotRandomizeExplicitGroundPoint, []),
            (self.testStinkBombDoesNotRandomizeTargetedThrow, []),
            (self.testTargetedThrowUsesTargetCenterXYAndGroundZ, []),
            (self.testExplicitGroundThrowUnderUnitUsesSelfDrop, []),
            (self.testGroundThrowNearUnitHullUsesSelfDrop, []),
            (self.testSelectedUnitEntityClickIsTreatedAsGroundTarget, []),
            (self.testTargetedThrowDoesNotUseSelfDrop, []),
        ]

    def testStinkBombDoesNotRandomizeExplicitGroundPoint(self):
        ability = AbilityThrowStinkBomb.__new__(AbilityThrowStinkBomb)
        ability.throwtarget = None

        self.assertFalse(ability.ShouldRandomizeThrowEnd())

    def testStinkBombDoesNotRandomizeTargetedThrow(self):
        ability = AbilityThrowStinkBomb.__new__(AbilityThrowStinkBomb)
        ability.throwtarget = object()

        self.assertFalse(ability.ShouldRandomizeThrowEnd())

    def testTargetedThrowUsesTargetCenterXYAndGroundZ(self):
        ability = AbilityThrowMolotov.__new__(AbilityThrowMolotov)
        ability.throwtarget = FakeThrowUnit(Vector(120, 8, 0), radius=32.0, center=Vector(128, 0, 48))
        ability.throwtargetpos = Vector(120, 8, 0)
        ability.throwstartattachment = ''
        ability.throwstartoffset = Vector(0, 0, 0)
        unit = FakeThrowUnit(Vector(0, 0, 0), radius=32.0)

        start, end = ability.GetTossStartAndEnd(unit)

        self.assertEqual(start, unit.WorldSpaceCenter())
        self.assertEqual(end, Vector(128, 0, 0))

    def testExplicitGroundThrowUnderUnitUsesSelfDrop(self):
        ability = AbilityThrowMolotov.__new__(AbilityThrowMolotov)
        ability.throwtarget = None
        unit = FakeThrowUnit(Vector(0, 0, 0), radius=32.0)
        targetpos = Vector(8, 8, 0)

        self.assertTrue(IsGroundTargetWithinUnitRadius(unit, targetpos))
        self.assertTrue(ability.ShouldDropOnSelfGroundTarget(unit, targetpos))

    def testGroundThrowNearUnitHullUsesSelfDrop(self):
        ability = AbilityThrowStinkBomb.__new__(AbilityThrowStinkBomb)
        ability.throwtarget = None
        unit = FakeThrowUnit(Vector(0, 0, 0), radius=32.0)
        targetpos = Vector(88, 0, 0)

        self.assertTrue(IsGroundTargetWithinUnitRadius(unit, targetpos))
        self.assertTrue(ability.ShouldDropOnSelfGroundTarget(unit, targetpos))

    def testSelectedUnitEntityClickIsTreatedAsGroundTarget(self):
        ability = AbilityThrowMolotov.__new__(AbilityThrowMolotov)
        unit = FakeThrowUnit(Vector(0, 0, 0), radius=32.0)
        ability.units = [unit]

        self.assertTrue(ability.ShouldTreatEntityAsGroundTarget(unit))

    def testTargetedThrowDoesNotUseSelfDrop(self):
        ability = AbilityThrowObject.__new__(AbilityThrowObject)
        ability.throwtarget = object()
        unit = FakeThrowUnit(Vector(0, 0, 0), radius=32.0)
        targetpos = Vector(8, 8, 0)

        self.assertFalse(ability.ShouldDropOnSelfGroundTarget(unit, targetpos))


class FakeCollisionProp(object):
    def __init__(self, radius):
        self.radius = radius

    def BoundingRadius2D(self):
        return self.radius


class FakeThrowUnit(object):
    def __init__(self, origin, radius, center=None):
        self.origin = origin
        self.center = center if center is not None else origin + Vector(0, 0, 32)
        self.collisionprop = FakeCollisionProp(radius)

    def GetAbsOrigin(self):
        return self.origin

    def WorldSpaceCenter(self):
        return self.center

    def CollisionProp(self):
        return self.collisionprop

    def GetHandle(self):
        return self
