
ORDERS_START, STOP = map(chr, range(2))

SELECTING_PLACE, KITCHEN, BAR, ZEH, Z_6, ADD_NEW_POSITION, PRODUCT_HANDLER, HANDLE_POSITION = map(chr, range(2, 10))

CREATING_ORDER, SENDING_ORDER, HISTORY, CHANGE_ORDER, CLOSING_ORDER, DELETING_ORDER, DELETE_FROM_ORDER, TYPING, TYPING_COUNT = map(chr, range(10, 19))

MENU, START = map(chr, range(19, 21))

REPORTING, GET_REPORT, GET_REPORT_XLSX, KITCHEN_REPORT, BAR_REPORT, ZEH_REPORT = map(chr, range(21, 27))

END = map(chr, range(198, 199))

DELETE_POSITION, EDIT_CATEGORY, ADD_CATEGORY, REMOVE_CATEGORY, TYPING_CATEGORY, TYPING_TNUMBER, SET_CONTACT= map(chr, range(68, 75))

DELETE_MESSAGE_PAUSE = 5

reg_place_str = '('+str(KITCHEN) + '|' + str(BAR) + '|' + str(ZEH) + '|' + str(Z_6)+')'


