import typing as t

from fastapi import Depends

from libs.ingestible import make_get_dependency, make_get_translation_dependency, make_get_writable_dependency
from modules.drinks.models import Drink, DrinkTranslation
from modules.users.dependencies import CurrentUserDependency, LocaleDependency, OptionalUserDependency

get_drink_dependency = make_get_dependency(Drink, OptionalUserDependency)
DrinkDependency = t.Annotated[Drink, Depends(get_drink_dependency)]

get_writable_drink_dependency = make_get_writable_dependency(Drink, CurrentUserDependency)
WritableDrinkDependency = t.Annotated[Drink, Depends(get_writable_drink_dependency)]

get_drink_translation_dependency = make_get_translation_dependency(
    DrinkDependency, DrinkTranslation, DrinkTranslation.drink_id, LocaleDependency
)
DrinkTranslationDependency = t.Annotated[DrinkTranslation | None, Depends(get_drink_translation_dependency)]
