from hyPI._parsers import Recipe as _Recipe
from pysettings.jsonConfig import JsonConfig as _JsonConfig
from pysettings import iterDict
import os

_RECIPE_MAPPING_PATH = os.path.join(os.path.split(__file__)[0], "recipeMapping.json")
_RECIPE_MAPPING = _JsonConfig.loadConfig(_RECIPE_MAPPING_PATH)




class RecipeAPI:
    @staticmethod
    def getRecipeFromID(itemID:str)->_Recipe | None:
        itemID = itemID.value if hasattr(itemID, "value") else itemID
        recipe = _RECIPE_MAPPING.get(itemID, None)
        if recipe is None: return None
        return _Recipe(recipe, itemID)
    @staticmethod
    def getRecipes():
        for id_, item in iterDict(_RECIPE_MAPPING):
            yield _Recipe(item, id_)



