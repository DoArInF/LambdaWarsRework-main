from srctests.gametestsuite import GameTestSuite
from srctests.gametestcase import GenericGameTestCase

if isserver:
    from vmath import Vector
    from entities import D_HT
    from srcbase import IN_SPEED
    from core.abilities.attackmove import GroupAttackMove
    from core.abilities.target import AbilityTarget
    from core.units import BehaviorGeneric
    from core.units.intention import BaseAction, CHANGETO, SUSPENDFOR, DONE
    from core.units.orders import Order


def CreateAbilityOrdersTestSuite():
    suite = GameTestSuite()
    if isserver:
        suite.addTest(AbilityOrdersRegressionTestCase())
    return suite


if isserver:
    class FakePlayer(object):
        def __init__(self, buttons=0):
            self.buttons = buttons

        def GetOwnerNumber(self):
            return 2


    class FakeActiveAbility(object):
        interruptible = False


    class FakeQueuedAbilityInfo(object):
        queueorder_defer_requirements = set(['notinterruptible', 'recharging'])
        allowqueueorder_defer_requirements = True

        @classmethod
        def GetRequirements(cls, player, unit):
            return set(unit.requirements)

        @classmethod
        def CanQueueOrderWithRequirements(cls, requirements):
            return bool(requirements) and requirements <= cls.queueorder_defer_requirements


    class FakeAbilityAction(BaseAction):
        def Init(self, order):
            super().Init()
            self.order = order


    class FakeQueuedAbility(object):
        behaviorgeneric_action = FakeAbilityAction
        autocasted = False
        stopped = False

        def __init__(self, requirements, deferredrequirements):
            self.player = FakePlayer()
            self.requirements = set(requirements)
            self.deferredrequirements = set(deferredrequirements)

        def GetDeferredQueueOrderRequirements(self, unit):
            return set(self.deferredrequirements)

        def GetRequirements(self, player, unit):
            return set(self.requirements)


    class FakeSelectableUnit(object):
        def __init__(self, requirements=None, activeability=None):
            self.requirements = set(requirements or [])
            self.activeability = activeability
            self.abilitiesbyname = {'fake_queued_ability': FakeQueuedAbilityInfo}
            self.orders = []

        def GetHandle(self):
            return self

        def CanPlayerControlUnit(self, player):
            return True


    class FakeOrder(object):
        type = Order.ORDER_ABILITY

        def __init__(self, ability):
            self.ability = ability
            self.removed = False

        def Remove(self, *args, **kwargs):
            self.removed = True


    class FakeIdleUnit(object):
        def __init__(self, order):
            self.curorder = order
            self.orders = [order]
            self.attacks = []
            self.enemy = None

        @property
        def activeability(self):
            return self.curorder.ability if self.curorder else None

        def entindex(self):
            return 10002


    class FakeBehavior(object):
        name = 'behaviorgeneric'
        ActionIdle = BehaviorGeneric.ActionIdle

        def __init__(self, outer):
            self.outer = outer


    class FakeSenses(object):
        def __init__(self):
            self.force_sensing_count = 0

        def ForcePerformSensing(self):
            self.force_sensing_count += 1


    class FakeAttackMoveUnit(object):
        def __init__(self):
            self.enemy = None
            self.senses = FakeSenses()
            self.updated_enemy_count = 0
            self.curorder = None
            self.orders = []
            self.canshootmove = False
            self.navigator = FakeNavigator()
            self.maxattackrange = 640.0
            self.minattackrange = 0.0

        def entindex(self):
            return 10003

        def IRelationType(self, target):
            return D_HT

        def AddEntityRelationship(self, target, disposition, priority):
            pass

        def UpdateEnemy(self, senses):
            self.updated_enemy_count += 1

        def IsValidEnemy(self, enemy, require_alive=True):
            return enemy is not None and (not require_alive or enemy.IsAlive())


    class FakeAttackMoveBehavior(object):
        name = 'behaviorgeneric'
        ActionAbilityAttackMove = BehaviorGeneric.ActionAbilityAttackMove
        ActionOrderAttack = BehaviorGeneric.ActionOrderAttack
        ActionOrderAttackMove = BehaviorGeneric.ActionOrderAttackMove
        ActionOrderMove = BehaviorGeneric.ActionOrderMove
        ActionAttack = BehaviorGeneric.ActionAttack
        ActionIdle = BehaviorGeneric.ActionIdle


    class FakeTarget(object):
        def __init__(self, alive=False):
            self.alive = alive
            self.health = 100 if alive else 0

        def IsWorld(self):
            return False

        def IsUnit(self):
            return True

        def CanBeSeen(self):
            return True

        def IsAlive(self):
            return self.alive

        def GetHandle(self):
            return self


    class FakePath(object):
        maxmovedist = 0
        pathcontext = None


    class FakeNavigator(object):
        def __init__(self):
            self.stopmoving_count = 0
            self.path = FakePath()
            self.facingtarget = None
            self.facingcone = 0.0
            self.last_goal = None
            self.goal_distance = 999.0

        def StopMoving(self):
            self.stopmoving_count += 1

        def SetGoal(self, targetorigin, tolerance, goalflags):
            self.last_goal = (targetorigin, tolerance, goalflags)
            return True

        def SetGoalTarget(self, target, tolerance, goalflags):
            self.last_goal = (target, tolerance, goalflags)
            return True

        def GetGoalDistance(self):
            return self.goal_distance


    class FakeAttackMoveOrder(object):
        type = Order.ORDER_ABILITY

        def __init__(self, target, position, ability=None, repeat=False):
            self.target = target
            self.position = position
            self.ability = ability
            self.repeat = repeat
            self.removed = False
            self.unit = None

        def Remove(self, *args, **kwargs):
            self.removed = True


    class FakeMoveOrder(object):
        type = Order.ORDER_MOVE
        target = None
        hidespot = None
        force_face_angle = False
        repeat = False
        ability = None
        angle = None

        def __init__(self, position):
            self.position = position
            self.removed = False
            self.unit = None

        def Remove(self, *args, **kwargs):
            self.removed = True
            if not self.unit:
                return
            self.unit.orders.remove(self)
            self.unit.curorder = self.unit.orders[0] if self.unit.orders else None


    class FakePatrolAbility(object):
        name = 'patrol'
        behaviorgeneric_action = BehaviorGeneric.ActionAbilityAttackMove
        autocasted = False


    class FakeGroupAttackMovePlayer(object):
        def __init__(self, target):
            self.mousedata = type('FakeMouseData', (object,), {'ent': target})()

        def GetMouseData(self):
            return self.mousedata


    class FakeGroupAttackMoveUnit(FakeAttackMoveUnit):
        OnNewOrder = 'OnNewOrder'
        OnOrderQueued = 'OnOrderQueued'

        def __init__(self):
            super().__init__()
            self.dispatched_target_only = None

        def AbilityOrder(self, target=None, position=None, ability=None, dispatchevent=True, **kwargs):
            order = FakeAttackMoveOrder(target, position, ability=ability)
            order.unit = self
            self.orders.append(order)
            if not self.curorder:
                self.curorder = order
            if dispatchevent:
                self.DispatchEvent(self.OnNewOrder if self.curorder == order else self.OnOrderQueued, order)
            return order

        def DispatchEvent(self, eventname, order):
            self.dispatched_target_only = getattr(order, 'attackmove_target_only', False)


    class AbilityOrdersRegressionTestCase(GenericGameTestCase):
        def setUp(self):
            super().setUp()
            self.testsleft = [
                (self.testShiftQueueAllowsTemporaryUnitRequirements, []),
                (self.testShiftQueueRejectsNonDeferredRequirements, []),
                (self.testQueuedOrderRechecksDeferredRequirements, []),
                (self.testQueuedOrderDoesNotTreatItselfAsNotInterruptibleBlocker, []),
                (self.testAttackMoveWorldClickUsesPosition, []),
                (self.testAttackMoveEntityClickMarksTargetOnlyBeforeDispatch, []),
                (self.testAttackMoveEntityClickUsesAttackOrder, []),
                (self.testAttackMoveEntityClickStopsWhenTargetDies, []),
                (self.testAttackMovePreservesMovementWhenAutoAttackingEnemy, []),
                (self.testAttackMoveResumeRebuildsClickedGoalAfterAutoAttack, []),
                (self.testPatrolRepeatStartsNextPointWithoutGoingIdle, []),
                (self.testPatrolRepeatCanFinishMoveWithoutStopMoving, []),
                (self.testPatrolRepeatAdvancesBeforeNavigatorStopsAtWaypoint, []),
                (self.testQueuedMoveAdvancesBeforeNavigatorStopsAtWaypoint, []),
            ]

        def MakeTargetAbility(self, queueorder):
            ability = AbilityTarget.__new__(AbilityTarget)
            ability.name = 'fake_queued_ability'
            ability.player = FakePlayer(IN_SPEED if queueorder else 0)
            ability.queueorder = queueorder
            ability.queueorder_deferred_requirements = {}
            ability.autocasted = False
            return ability

        def testShiftQueueAllowsTemporaryUnitRequirements(self):
            ability = self.MakeTargetAbility(queueorder=True)
            unit = FakeSelectableUnit(requirements=['notinterruptible'], activeability=FakeActiveAbility())

            self.assertTrue(ability.UnitPassesAbilitySelection(unit, FakeQueuedAbilityInfo))
            self.assertEqual(ability.GetDeferredQueueOrderRequirements(unit), set(['notinterruptible']))

        def testShiftQueueRejectsNonDeferredRequirements(self):
            ability = self.MakeTargetAbility(queueorder=True)
            unit = FakeSelectableUnit(requirements=['energy'])

            self.assertFalse(ability.UnitPassesAbilitySelection(unit, FakeQueuedAbilityInfo))
            self.assertEqual(ability.GetDeferredQueueOrderRequirements(unit), set())

        def testQueuedOrderRechecksDeferredRequirements(self):
            ability = FakeQueuedAbility(requirements=['recharging'], deferredrequirements=['recharging'])
            order = FakeOrder(ability)
            unit = FakeIdleUnit(order)
            behavior = FakeBehavior(unit)
            action = BehaviorGeneric.ActionIdle(unit, behavior)
            action.Init()

            transition = action.DoOrder(order)

            self.assertTrue(order.removed)
            self.assertEqual(transition, CHANGETO)
            self.assertIsInstance(action.nextaction, BehaviorGeneric.ActionIdle)

        def testQueuedOrderDoesNotTreatItselfAsNotInterruptibleBlocker(self):
            ability = FakeQueuedAbility(requirements=['notinterruptible'], deferredrequirements=['notinterruptible'])
            order = FakeOrder(ability)
            unit = FakeIdleUnit(order)
            behavior = FakeBehavior(unit)
            action = BehaviorGeneric.ActionIdle(unit, behavior)
            action.Init()

            transition = action.DoOrder(order)

            self.assertFalse(order.removed)
            self.assertEqual(transition, CHANGETO)
            self.assertIsInstance(action.nextaction, FakeAbilityAction)

        def testAttackMoveWorldClickUsesPosition(self):
            position = Vector(128, 64, 0)
            order = FakeAttackMoveOrder(None, position)
            unit = FakeAttackMoveUnit()
            behavior = FakeAttackMoveBehavior()
            action = BehaviorGeneric.ActionAbilityAttackMove(unit, behavior)
            action.Init(order)

            transition = action.OnStart()

            self.assertEqual(transition, SUSPENDFOR)
            self.assertIsInstance(action.nextaction, BehaviorGeneric.ActionOrderAttackMove)
            self.assertIsNone(action.nextaction.target)
            self.assertEqual(action.nextaction.targetorigin, position)

        def testAttackMoveEntityClickMarksTargetOnlyBeforeDispatch(self):
            target = FakeTarget(alive=True)
            player = FakeGroupAttackMovePlayer(target)
            unit = FakeGroupAttackMoveUnit()
            attackmove = GroupAttackMove(player, Vector(128, 64, 0), [unit])
            attackmove.ability = FakePatrolAbility()

            attackmove.ExecuteUnitForPosition(unit, Vector(128, 64, 0))

            self.assertTrue(unit.dispatched_target_only)

        def testAttackMoveEntityClickUsesAttackOrder(self):
            position = Vector(128, 64, 0)
            target = FakeTarget(alive=True)
            order = FakeAttackMoveOrder(target, position)
            order.attackmove_target_only = True
            unit = FakeAttackMoveUnit()
            behavior = FakeAttackMoveBehavior()
            action = BehaviorGeneric.ActionAbilityAttackMove(unit, behavior)
            action.Init(order)

            transition = action.OnStart()

            self.assertEqual(transition, SUSPENDFOR)
            self.assertIsInstance(action.nextaction, BehaviorGeneric.ActionOrderAttack)
            self.assertEqual(action.nextaction.order, order)

        def testAttackMoveEntityClickStopsWhenTargetDies(self):
            position = Vector(128, 64, 0)
            target = FakeTarget(alive=False)
            order = FakeAttackMoveOrder(target, position)
            order.attackmove_target_only = True
            unit = FakeAttackMoveUnit()
            unit.curorder = order
            unit.orders = [order]
            behavior = FakeAttackMoveBehavior()
            action = BehaviorGeneric.ActionOrderAttackMove(unit, behavior)
            action.Init(order, position, tolerance=32.0, goalflags=0)

            transition = action.OnResume()

            self.assertEqual(transition, DONE)
            self.assertIsNone(unit.navigator.last_goal)

        def testAttackMovePreservesMovementWhenAutoAttackingEnemy(self):
            unit = FakeAttackMoveUnit()
            behavior = FakeAttackMoveBehavior()
            action = BehaviorGeneric.ActionAttackMove(unit, behavior)
            action.Init(Vector(128, 64, 0), tolerance=32.0, goalflags=0)

            transition = action.OnNewEnemy(FakeTarget(alive=True))

            self.assertEqual(transition, SUSPENDFOR)
            self.assertIsInstance(action.nextaction, BehaviorGeneric.ActionAttack)
            self.assertTrue(action.nextaction.preserve_movement_on_end)

        def testAttackMoveResumeRebuildsClickedGoalAfterAutoAttack(self):
            position = Vector(256, 32, 0)
            unit = FakeAttackMoveUnit()
            behavior = FakeAttackMoveBehavior()
            action = BehaviorGeneric.ActionAttackMove(unit, behavior)
            action.Init(position, tolerance=32.0, goalflags=0)
            action.savedpath = object()

            transition = action.OnResume()

            self.assertFalse(transition)
            self.assertEqual(unit.navigator.last_goal, (position, 32.0, 0))

        def testPatrolRepeatStartsNextPointWithoutGoingIdle(self):
            ability = FakePatrolAbility()
            oldorder = FakeAttackMoveOrder(None, Vector(0, 0, 0), ability=ability, repeat=True)
            neworder = FakeAttackMoveOrder(None, Vector(128, 0, 0), ability=ability, repeat=True)
            unit = FakeAttackMoveUnit()
            unit.curorder = neworder
            behavior = FakeAttackMoveBehavior()
            action = BehaviorGeneric.ActionAbilityAttackMove(unit, behavior)
            action.Init(oldorder)

            transition = action.OnResume()

            self.assertEqual(transition, CHANGETO)
            self.assertIsInstance(action.nextaction, BehaviorGeneric.ActionAbilityAttackMove)
            self.assertEqual(action.nextaction.order, neworder)

        def testPatrolRepeatCanFinishMoveWithoutStopMoving(self):
            unit = FakeAttackMoveUnit()
            behavior = FakeAttackMoveBehavior()
            action = BehaviorGeneric.ActionOrderAttackMove(unit, behavior)
            action.Init(FakeAttackMoveOrder(None, Vector(128, 0, 0)), Vector(128, 0, 0), tolerance=32.0, goalflags=0)
            action.preserve_movement_on_end = True

            action.OnEnd()

            self.assertEqual(unit.navigator.stopmoving_count, 0)

        def testPatrolRepeatAdvancesBeforeNavigatorStopsAtWaypoint(self):
            oldorder = FakeAttackMoveOrder(None, Vector(0, 0, 0), repeat=True)
            neworder = FakeAttackMoveOrder(None, Vector(128, 0, 0), repeat=True)
            unit = FakeAttackMoveUnit()
            unit.orders = [oldorder, neworder]
            unit.curorder = oldorder
            unit.navigator.goal_distance = 48.0
            behavior = FakeAttackMoveBehavior()
            action = BehaviorGeneric.ActionOrderAttackMove(unit, behavior)
            action.Init(oldorder, oldorder.position, tolerance=32.0, goalflags=0)

            transition = action.Update()

            self.assertEqual(transition, DONE)
            self.assertTrue(action.preserve_movement_on_end)
            self.assertTrue(oldorder.removed)

        def testQueuedMoveAdvancesBeforeNavigatorStopsAtWaypoint(self):
            oldorder = FakeMoveOrder(Vector(0, 0, 0))
            neworder = FakeMoveOrder(Vector(128, 0, 0))
            unit = FakeAttackMoveUnit()
            unit.orders = [oldorder, neworder]
            unit.curorder = oldorder
            oldorder.unit = unit
            neworder.unit = unit
            unit.navigator.goal_distance = 48.0
            behavior = FakeAttackMoveBehavior()
            action = BehaviorGeneric.ActionOrderMove(unit, behavior)
            action.Init(oldorder)

            transition = action.Update()

            self.assertEqual(transition, CHANGETO)
            self.assertTrue(action.preserve_movement_on_end)
            self.assertTrue(oldorder.removed)
            self.assertIsInstance(action.nextaction, BehaviorGeneric.ActionOrderMove)
            self.assertEqual(action.nextaction.order, neworder)
