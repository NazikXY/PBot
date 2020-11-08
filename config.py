
ORDERS_START, STOP = map(chr, range(2))
SELECTING_PLACE, KITCHEN, BAR, ZEH, Z_6, ADD_NEW_POSITION, DELETE_POSITIONa, HANDLE_POSITION = map(chr, range(2, 10))
CREATING_ORDER, SENDING_ORDER, HISTORY, CHANGE_ORDER, CLOSING_ORDER, DELETING_ORDER, DELETE_FROM_ORDER, TYPING, TYPING_COUNT = map(chr, range(10, 19))
MENU, START = map(chr, range(19, 21))
REPORTING, GET_REPORT, GET_REPORT_XLSX, KITCHEN_REPORT, BAR_REPORT, ZEH_REPORT = map(chr, range(21, 27))

GREENS, VEGS, FRUIT, MEAT, MILK, DRINK, NUTS_DRIED_FRUIT = map(int, range(0, 7))

END = map(chr, range(98, 99))

DELETE_POSITION = map(chr, range(88,89))

DELETE_MESSAGE_PAUSE = 5

reg_category_str = '('+str(GREENS) + '|' + str(VEGS) + '|' + str(FRUIT) + '|' + str(MEAT) + '|' + str(MILK) + '|' + str(DRINK) + '|' + str(NUTS_DRIED_FRUIT)+')'
reg_place_str = '('+str(KITCHEN) + '|' + str(BAR) + '|' + str(ZEH) + '|' + str(Z_6)+')'

categories = {"Овощи": 0,
              "Фрукты": 1,
              "Зелень":    2,
              "Мясо/Рыба": 3,
              "Молочные продукты": 4,
              "Напитки": 5,
              "Орехи/Сухофрукты": 6}