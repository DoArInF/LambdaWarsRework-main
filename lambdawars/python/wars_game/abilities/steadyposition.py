""" Steady position ability. Puts the unit in a crouch position on the spot. """
from core.abilities import AbilityInstant
from fields import FloatField
from gameinterface import ConVar, FCVAR_CHEAT

if isserver:
    from core.units import BehaviorGeneric, BaseAction

    steadyposition_debug = ConVar('wars_steadyposition_debug', '0', FCVAR_CHEAT)

    def _DebugEntIndex(ent):
        if not ent:
            return 'None'
        entindex = getattr(ent, 'entindex', None)
        if not entindex:
            return 'no_entindex'
        try:
            return str(entindex())
        except ReferenceError:
            return 'stale'

    def DebugSteadyPosition(unit, action, reason, target=None):
        if not steadyposition_debug.GetBool():
            return

        behavior = getattr(action, 'behavior', None)
        actions = getattr(behavior, 'actions', None)
        state = 'none'
        if actions:
            state = '>'.join([a.__class__.__name__ for a in actions])

        order = getattr(action, 'order', None)
        orderid = 'None' if not order else str(id(order))
        slotid = getattr(unit, 'hidingspotid', None)
        if slotid is None and order:
            slotid = getattr(order, 'hidespot', None)
        if slotid is None:
            slotid = 'None'

        target = target if target is not None else getattr(unit, 'enemy', None)

        DevMsg(1, '#%s steadyposition: state=%s order=%s slot=%s target=%s reason=%s steadying=%s insteady=%s crouching=%s aimoving=%s\n' % (
            _DebugEntIndex(unit), state, orderid, slotid, _DebugEntIndex(target), reason,
            getattr(unit, 'steadying', None), getattr(unit, 'insteadyposition', None),
            getattr(unit, 'crouching', None), getattr(unit, 'aimoving', None)))

class AbilitySteadyPosition(AbilityInstant):
    name = 'steadyposition'
    displayname = '#CombSteadyPosition_Name'
    description = '#CombSteadyPosition_Description'
    image_name = 'vgui/combine/abilities/combine_sniper_steady_position'
    hidden = True
    rechargetime = 1.0
    steadytime = FloatField(value=5.0)
    defaultautocast = True
    serveronly = True
    #  sai_hint = AbilityInstant.sai_hint | set(['sai_deploy'])
    if isserver:
        def DoAbility(self):
            self.SelectGroupUnits()
            alwaysqueue = True if self.autocasted else False
            idx = 0 if alwaysqueue else None
            for unit in self.units:
                if unit.in_cover or unit.insteadyposition or getattr(unit, 'steadying', False):
                    continue
                # From the attack code we stack the action on top of the current attack action, so it does not get
                # ended.
                if not self.kwarguments.get('direct_from_attack', False):
                    unit.AbilityOrder(position=unit.GetAbsOrigin(),
                                      ability=self, alwaysqueue=alwaysqueue, idx=idx)
                self.SetNotInterruptible()

        class ActionInSteadyPosition(BehaviorGeneric.ActionCrouchHoldSpot):
            def Init(self, autocasted=False):
                super().Init()

                self.autocasted = autocasted

            def OnStart(self):
                self.outer.insteadyposition = True
                DebugSteadyPosition(self.outer, self, 'entered steady hold')
                return super().OnStart()

            def OnEnd(self):
                DebugSteadyPosition(self.outer, self, 'leaving steady hold')
                self.outer.insteadyposition = False
                super().OnEnd()

            def OnNavFailed(self):
                DebugSteadyPosition(self.outer, self, 'ignore OnNavFailed while holding steady position')
                return self.Continue()

            def OnEnemyLost(self):
                DebugSteadyPosition(self.outer, self, 'ignore OnEnemyLost while holding steady position')
                return self.Continue()

            # Don't break cover when targeting an enemy
            def OnNewOrder(self, order):
                pos = order.target.GetAbsOrigin() if order.target else None
                if (order.type == order.ORDER_ENEMY or (order.type == order.ORDER_ABILITY and order.ability.name == 'attackmove' and order.target)) and pos.DistTo(self.outer.GetAbsOrigin()) <= self.outer.activeweapon.AttackPrimary.maxrange:
                    return self.SuspendFor(self.behavior.ActionHideSpotAttack,
                                           'Attacking enemy on order from cover/hold spot', order.target)

            autocasted = False
            last_had_valid_enemy_time = 0

        class ActionDoSteadyPosition(BaseAction):
            def Init(self, ability, order=None):
                super().Init()

                self.ability = ability
                self.order = order

            # TODO: Don't interrupt steadying position when a new enemy is targeted while the unit is steadying for the previous attack
            # (e.g. a manhack flies in while the unit is steadying to shoot a more distant target)

            def OnStart(self):
                DebugSteadyPosition(self.outer, self, 'start steady transition')
                self.outer.steadying = True

            def Update(self):
                outer = self.outer

                abi = self.ability
                outer.crouching = True
                outer.aimoving = True
                DebugSteadyPosition(outer, self, 'start steady channel')
                trans = self.SuspendFor(self.behavior.ActionChanneling, 'Steadying position', abi.steadytime,
                                        channel_animation=self.channel_animation)
                self.steadyaction = self.nextaction
                return trans

            def OnNavFailed(self):
                DebugSteadyPosition(self.outer, self, 'ignore OnNavFailed during steady transition')
                return self.Continue()

            def OnEnemyLost(self):
                DebugSteadyPosition(self.outer, self, 'ignore OnEnemyLost during steady transition')
                return self.Continue()

            def OnNewEnemy(self, enemy):
                DebugSteadyPosition(self.outer, self, 'ignore OnNewEnemy during steady transition', target=enemy)
                return self.Continue()

            def OnEnd(self):
                super().OnEnd()

                outer = self.outer
                outer.steadying = False
                outer.aimoving = False
                if not self.steadiedposition:
                    DebugSteadyPosition(outer, self, 'standdown from ActionDoSteadyPosition.OnEnd')
                    outer.crouching = False
                    self.ability.Cancel()
                else:
                    DebugSteadyPosition(outer, self, 'finish ActionDoSteadyPosition.OnEnd')

            def OnResume(self):
                outer = self.outer
                abi = self.ability
                order = self.order
                steadyaction = self.steadyaction
                if steadyaction:
                    self.steadyaction = None
                    if order:
                        order.Remove(dispatchevent=False)

                    if steadyaction.channelsuccess:
                        self.steadiedposition = True
                        DebugSteadyPosition(outer, self, 'steady channel completed')
                        abi.SetRecharge(outer)
                        abi.Completed()
                        return self.ChangeTo(abi.ActionInSteadyPosition, 'In steady position', autocasted=abi.autocasted)

                return super().OnResume()

            steadyaction = None
            steadiedposition = False
            channel_animation = None
            ability = None
            order = None
            #changetoidleonlostorder = False

        class ActionSteadyPosition(BehaviorGeneric.ActionAbility):
            def OnStart(self):
                return self.SuspendFor(self.order.ability.ActionDoSteadyPosition, 'Do steady position',
                                       self.order.ability, self.order)
            def OnStunned(self):
                self.CancelAbilityOrder(debugmsg='Unit stunned while steadying position')
                return self.ChangeTo(self.behavior.ActionStunned, 'Stunned')




        behaviorgeneric_action = ActionSteadyPosition

class AbilitySteadyCharPosition(AbilitySteadyPosition):
    name = 'steadyposition_char'
    displayname = '#CombSteadyPosition_Name'
    description = '#CombSteadyPosition_Description'
    image_name = 'vgui/combine/abilities/combine_sniper_steady_position'
    rechargetime = 1.0
    steadytime = FloatField(value=1.0)

class RebelAbilitySteadyPosition(AbilitySteadyPosition):
    name = 'rebel_steadyposition'
    displayname = '#CombSteadyPosition_Name'
    description = '#CombSteadyPosition_Description'
    image_name = 'vgui/rebels/abilities/rebel_veteran_steady_position'
    rechargetime = 1.99
    steadytime = FloatField(value=2.00)

class RebelAbilitySteadyCharPosition(AbilitySteadyPosition):
    name = 'rebel_steadyposition_char'
    displayname = '#RebSteadyPosition_Name'
    description = '#RebSteadyPosition_Description'
    image_name = 'vgui/rebels/abilities/rebel_veteran_steady_position'
    rechargetime = 1.0
    steadytime = FloatField(value=1.0)
