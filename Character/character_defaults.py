
from enum import Enum

from Character.archer import Archer
from Character.character import Character
from Character.druid import Druid
from Character.mage import Mage
from Character.warrior import Warrior


class CharacterDefault(Enum):
    WARRIOR = Warrior(500, 500, 0, 0, 200, 100, 50, 50)
    MAGE = Mage(500, 500, 0, 0, 50, 100, 100, 100)
    DRUID = Druid(500, 500, 0, 0, 100, 100, 100, 100)
    ARCHER = Archer(500, 500, 0, 0, 100, 100, 300, 300)

    @staticmethod
    def handleSelection(characterType: str):
        if characterType == "Warrior":
            return CharacterDefault.WARRIOR.value
        elif characterType == "Mage":
            return CharacterDefault.MAGE.value
        elif characterType == "Druid":
            return CharacterDefault.DRUID.value
        elif characterType == "Archer":
            return CharacterDefault.ARCHER.value
        else:
            pass

