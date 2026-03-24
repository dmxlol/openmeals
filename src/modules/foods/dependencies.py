import typing as t

from fastapi import Depends

from libs.ingestible import make_get_dependency, make_get_translation_dependency, make_get_writable_dependency
from modules.foods.models import Food, FoodTranslation
from modules.users.dependencies import CurrentUserDependency, LocaleDependency, OptionalUserDependency

get_food_dependency = make_get_dependency(Food, OptionalUserDependency)
FoodDependency = t.Annotated[Food, Depends(get_food_dependency)]

get_writable_food_dependency = make_get_writable_dependency(Food, CurrentUserDependency)
WritableFoodDependency = t.Annotated[Food, Depends(get_writable_food_dependency)]

get_food_translation_dependency = make_get_translation_dependency(
    FoodDependency, FoodTranslation, FoodTranslation.food_id, LocaleDependency
)
FoodTranslationDependency = t.Annotated[FoodTranslation | None, Depends(get_food_translation_dependency)]
