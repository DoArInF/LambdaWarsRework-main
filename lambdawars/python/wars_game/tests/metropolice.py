from srctests.gametestsuite import GameTestSuite
from srctests.gametestcase import GenericGameTestCase

from entities import Activity
from wars_game.units.metropolice import MetroPolice


def CreateMetropoliceTestSuite():
    suite = GameTestSuite()
    suite.addTest(MetropoliceRegressionTestCase())
    return suite


class MetropoliceRegressionTestCase(GenericGameTestCase):
    def setUp(self):
        super().setUp()
        self.testsleft = [
            (self.testShieldRunKeepsOriginalWalkShieldActivity, []),
        ]

    def testShieldRunKeepsOriginalWalkShieldActivity(self):
        shieldmap = MetroPolice.acttables['weapon_stunstick_shield']
        stationedmap = MetroPolice.acttables['weapon_stunstick_stationed']

        self.assertEqual(shieldmap[Activity.ACT_RUN], 'ACT_WALK_SHIELD_ANGRY')
        self.assertEqual(shieldmap[Activity.ACT_RUN_AIM], 'ACT_WALK_SHIELD_ANGRY')
        self.assertEqual(stationedmap[Activity.ACT_RUN], 'ACT_WALK_SHIELD_ANGRY')
        self.assertEqual(stationedmap[Activity.ACT_RUN_AIM], 'ACT_WALK_SHIELD_ANGRY')
