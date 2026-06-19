from srctests.gametestsuite import GameTestSuite
from srctests.gametestcase import GenericGameTestCase
from vmath import vec3_origin

if isserver:
    from core.units import BehaviorGeneric, BaseBehavior
    from wars_game.abilities.steadyposition import AbilitySteadyPosition


def CreateSteadyPositionTestSuite():
    suite = GameTestSuite()
    if isserver:
        suite.addTest(SteadyPositionRegressionTestCase())
    return suite


if isserver:
    class FakeNavigator(object):
        def __init__(self):
            self.facingtarget = None
            self.facingcone = 0.0
            self.nopathvelocity = False
            self.stopmoving_count = 0

        def StopMoving(self):
            self.stopmoving_count += 1


    class FakeUnit(object):
        def __init__(self):
            self.navigator = FakeNavigator()
            self.enemy = None
            self.steadying = False
            self.insteadyposition = False
            self.aimoving = False
            self.crouching = False
            self.in_cover = False
            self.lastidleposition = vec3_origin
            self.nav_obstacle_enabled = False
            self.maxattackrange = 1408.0
            self.minattackrange = 0.0
            self.attacks = []
            self.forcedenemy = False

        def entindex(self):
            return 10001

        def GetAbsOrigin(self):
            return vec3_origin

        def IsMoving(self):
            return False

        def IsValidEnemy(self, enemy, require_alive=False):
            return bool(enemy and (not require_alive or enemy.IsAlive()))

        def EnableAsNavObstacle(self):
            self.nav_obstacle_enabled = True

        def DisableAsNavObstacle(self):
            self.nav_obstacle_enabled = False


    class FakeEnemy(object):
        def __init__(self, alive=True):
            self.alive = alive

        def IsAlive(self):
            return self.alive

        def GetHandle(self):
            return self

        def entindex(self):
            return 20001


    class FakeAbility(object):
        autocasted = True
        steadytime = 0.1

        def __init__(self):
            self.cancelled = False
            self.completed = False
            self.recharged = False

        def Cancel(self, *args, **kwargs):
            self.cancelled = True

        def Completed(self):
            self.completed = True

        def SetRecharge(self, unit):
            self.recharged = True


    class FakeOrder(object):
        def __init__(self):
            self.removed = False

        def Remove(self, *args, **kwargs):
            self.removed = True


    class FakeBehavior(object):
        handlers = BaseBehavior.handlers
        EndTopActions = BaseBehavior.EndTopActions
        DispatchEvent = BaseBehavior.DispatchEvent

        def __init__(self, outer):
            self.outer = outer
            self.actions = []
            self.in_on_start_call = False


    class SteadyPositionRegressionTestCase(GenericGameTestCase):
        def setUp(self):
            super().setUp()
            self.testsleft = [
                (self.testTargetDiesDuringMoveDoesNotEndAttackAction, []),
                (self.testTargetDiesDuringSteadyTransitionDoesNotCancelPosture, []),
                (self.testTargetLostDuringSteadyTransitionDoesNotCancelPosture, []),
                (self.testNewTargetDuringSteadyTransitionDoesNotRestartSteadyAction, []),
                (self.testSeveralTargetsDieDoesNotRestartSteadyAction, []),
                (self.testNoTargetsAfterSteadyKeepsOccupiedPosture, []),
                (self.testNewMoveOrderIsNotEatenBySteadyTransition, []),
                (self.testExplicitSteadyCancelStillClearsOldOrder, []),
                (self.testTargetEventsDoNotLeaveDanglingOrderReferences, []),
            ]

        def MakeSteadyAction(self):
            unit = FakeUnit()
            behavior = FakeBehavior(unit)
            ability = FakeAbility()
            action = AbilitySteadyPosition.ActionDoSteadyPosition(unit, behavior)
            action.Init(ability, None)
            action.OnStart()
            unit.crouching = True
            unit.aimoving = True
            return unit, behavior, ability, action

        def testTargetDiesDuringMoveDoesNotEndAttackAction(self):
            unit = FakeUnit()
            behavior = FakeBehavior(unit)
            enemy = FakeEnemy(alive=False)
            action = BehaviorGeneric.ActionAttack(unit, behavior)
            action.Init(enemy)

            transition = action.OnNavFailed()

            self.assertEqual(transition, action.Continue())
            self.assertNotEqual(action.reason, 'NavFailed, lost target?')
            self.assertEqual(unit.navigator.stopmoving_count, 0)

        def testTargetDiesDuringSteadyTransitionDoesNotCancelPosture(self):
            unit, behavior, ability, action = self.MakeSteadyAction()

            transition = action.OnNavFailed()

            self.assertEqual(transition, action.Continue())
            self.assertTrue(unit.steadying)
            self.assertTrue(unit.crouching)
            self.assertTrue(unit.aimoving)
            self.assertFalse(ability.cancelled)

        def testTargetLostDuringSteadyTransitionDoesNotCancelPosture(self):
            unit, behavior, ability, action = self.MakeSteadyAction()

            transition = action.OnEnemyLost()

            self.assertEqual(transition, action.Continue())
            self.assertTrue(unit.steadying)
            self.assertTrue(unit.crouching)
            self.assertFalse(ability.cancelled)

        def testNewTargetDuringSteadyTransitionDoesNotRestartSteadyAction(self):
            unit, behavior, ability, action = self.MakeSteadyAction()
            enemy = FakeEnemy(alive=True)

            transition = action.OnNewEnemy(enemy)

            self.assertEqual(transition, action.Continue())
            self.assertTrue(unit.steadying)
            self.assertTrue(unit.crouching)
            self.assertFalse(ability.cancelled)

        def testSeveralTargetsDieDoesNotRestartSteadyAction(self):
            unit, behavior, ability, action = self.MakeSteadyAction()

            for i in range(3):
                self.assertEqual(action.OnNavFailed(), action.Continue())
                self.assertEqual(action.OnEnemyLost(), action.Continue())

            self.assertTrue(unit.steadying)
            self.assertTrue(unit.crouching)
            self.assertFalse(ability.cancelled)

        def testNoTargetsAfterSteadyKeepsOccupiedPosture(self):
            unit = FakeUnit()
            behavior = FakeBehavior(unit)
            action = AbilitySteadyPosition.ActionInSteadyPosition(unit, behavior)
            action.Init(autocasted=True)
            action.OnStart()
            behavior.actions = [action]

            handled = behavior.DispatchEvent('OnEnemyLost')

            self.assertTrue(handled)
            self.assertTrue(unit.insteadyposition)
            self.assertTrue(unit.crouching)

        def testNewMoveOrderIsNotEatenBySteadyTransition(self):
            unit, behavior, ability, action = self.MakeSteadyAction()

            self.assertFalse(hasattr(action, 'OnNewOrder'))

        def testExplicitSteadyCancelStillClearsOldOrder(self):
            unit, behavior, ability, action = self.MakeSteadyAction()
            order = FakeOrder()
            action.order = order

            action.OnEnd()

            self.assertFalse(unit.steadying)
            self.assertFalse(unit.crouching)
            self.assertTrue(ability.cancelled)
            self.assertFalse(order.removed)

        def testTargetEventsDoNotLeaveDanglingOrderReferences(self):
            unit, behavior, ability, action = self.MakeSteadyAction()
            order = FakeOrder()
            action.order = order

            action.OnNavFailed()
            action.OnEnemyLost()
            action.OnNewEnemy(None)

            self.assertIs(action.order, order)
            self.assertFalse(order.removed)
            self.assertFalse(ability.cancelled)
