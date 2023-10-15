from enum import Enum


class Scope(Enum):
    categories = 1
    hot_meals = 2
    drinks = 3
    deserts = 4


class MenuInfo(Enum):
    id = 1
    name = 2
    description = 3
    next_position = 4
    price = 5
    size = 6


CATS_DIR = {
    Scope.categories: 'categories',
    Scope.hot_meals: 'hot_meals',
    Scope.drinks: 'drinks',
    Scope.deserts: 'deserts',
}

MENU_DIR = {
    MenuInfo.id: 'id',
    MenuInfo.name: 'name',
    MenuInfo.description: 'description',
    MenuInfo.next_position: 'next_position',
    MenuInfo.price: 'price',
    MenuInfo.size: 'size'
}


class Descriptor:

    def __set_name__(self, owner, name):
        self.__name = f'_{owner.__name__}__{name}'

    def __check_value(self, value):
        raise NotImplementedError

    def __get__(self, instance, owner):
        return getattr(instance, self.__name)

    def __set__(self, instance, value):
        setattr(instance, self.__name, value)


class NameValue(Descriptor):

    def __check_value(self, value):
        if not isinstance(value, str):
            raise TypeError('Значение должно быть строкой')

    def __set__(self, instance, value):
        self.__check_value(value)
        super().__set__(instance, value)


class IntOrFloatValue(Descriptor):

    def __check_value(self, value):
        if type(value) not in (int, float):
            raise TypeError('Значение должно быть целым или вещественным числом')

    def __set__(self, instance, value):
        self.__check_value(value)
        super().__set__(instance, value)


class MenuPosition:
    ID = 0
    MAX_ID = 0
    name = NameValue()
    description = NameValue()
    next_position = NameValue()

    def __new__(cls, *args, **kwargs):
        if cls.ID >= cls.MAX_ID:
            return AttributeError('ID переполнен')
        cls.ID += 1
        return super().__new__(cls)

    def __init__(self, name, description, next_position):
        self.id = self.ID
        self.name = name
        self.description = description
        self.next_position = next_position

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class Category(MenuPosition):
    ID = 0
    MAX_ID = 99

    def __call__(self, *args, **kwargs):
        return {
            MENU_DIR[MenuInfo.id]: self.id,
            MENU_DIR[MenuInfo.name]: self.name,
            MENU_DIR[MenuInfo.description]: self.description,
            MENU_DIR[MenuInfo.next_position]: self.next_position
        }


class Meal(MenuPosition):
    price = IntOrFloatValue()
    size = IntOrFloatValue()

    def __init__(self, name, price, size, description, next_position):
        self.price = price
        self.size = size
        super().__init__(name, description, next_position)

    def __call__(self, *args, **kwargs):
        return {
            MENU_DIR[MenuInfo.id]: self.id,
            MENU_DIR[MenuInfo.name]: self.name,
            MENU_DIR[MenuInfo.price]: self.price,
            MENU_DIR[MenuInfo.size]: self.size,
            MENU_DIR[MenuInfo.description]: self.description,
            MENU_DIR[MenuInfo.next_position]: self.next_position
        }


class HotMeal(Meal):
    ID = 99
    MAX_ID = 299


class Drink(Meal):
    ID = 299
    MAX_ID = 399


class Desert(Meal):
    ID = 399
    MAX_ID = 499


if __name__ == '__main__':
    categories = (Category('Горячие блюда', 'Топовые горячие блюда', CATS_DIR[Scope.hot_meals]),
                  Category('Напитки', 'Охлаждающие напитки', CATS_DIR[Scope.drinks]),
                  Category('Десерты', 'Сладкие десерты', CATS_DIR[Scope.deserts]))

    hot_meals = (
        HotMeal('Свинина с грибами', 14, 300, 'Свинина с грибами в сливочном соусе', CATS_DIR[Scope.hot_meals]),
        HotMeal('Овсянка', 4, 250, 'Овсянка с апельсиновым джемом', CATS_DIR[Scope.hot_meals]))

    drinks = (Drink('Мохито', 7, 200, 'Мохито со льдом', CATS_DIR[Scope.drinks]),
              Drink('Кока-кола', 3, 200, 'Кока-кола со льдом', CATS_DIR[Scope.drinks]))

    deserts = (Desert('Яблочный пирог', 10, 250, 'Яблочный пирог со сливками', CATS_DIR[Scope.deserts]),
               Desert('Ягодный пирог', 12, 250, 'Ягодный пирог с заварным кремом', CATS_DIR[Scope.deserts]))
