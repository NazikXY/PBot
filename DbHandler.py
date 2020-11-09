import pickle
import sqlite3 as sq
from datetime import datetime, timedelta
# from pickle import dumps, loads
from ast import literal_eval
from sqlite3 import OperationalError
from json import loads, dumps
from config import *
# from main import Holder


class DBHandler:
    def __init__(self, db):
        self._db = sq.connect(db, check_same_thread=False)
        self._cursor = self._db.cursor()
        self._current_order = None

    def get_order_by_id(self, id):
        return self._cursor.execute("SELECT * FROM history WHERE order_id == {}".format(id)).fetchone()

    def get_order_list(self):
        return self._cursor.execute("SELECT * FROM history").fetchall()

    def get_order_by_place(self, place):
        return self._cursor.execute('SELECT * FROM "' + self.get_order_name_for_place(place) + '"').fetchall()

    def set_current_order_from_history(self, order_id):
        if self._current_order is None:
            try:
                target_order = self._cursor.execute(
                    'SELECT * FROM history WHERE "order_id" == {}'.format(order_id)).fetchone()
                self.create_order()
                try:

                    try:  # is json data try
                        data = loads(target_order[2])
                    except Exception as e:
                        print(e)  # pickled writes
                        data = pickle.loads(literal_eval(target_order[2]))

                except Exception as e:
                    print(e)
                    data = pickle.loads(literal_eval(target_order[2]))
                    print ('Histroy str was pickled, not json')

                for i in data:
                    self._cursor.execute(
                        'INSERT INTO "{}" ("goods_id", "count") VALUES ({},{})'.format(self._current_order, i[0], i[1]))
                self._db.commit()
            except Exception as e:
                print(e)

    def get_order(self, place):
         return self.get_order_name_for_place(place), self._cursor.execute('SELECT * FROM "' + self.get_order_name_for_place(place) + '"').fetchall()


    def get_goods_list(self):
        return self._cursor.execute('SELECT * FROM "goods"').fetchall()

    def add_to_goods(self, name, units, category):
        self._current_order = 'order_'+str(datetime.today().date())
        self._cursor.execute(
            'INSERT INTO "main"."goods" (name, units, category) VALUES ("{}", "{}", "{}")'.format(name, units, category))
        self._db.commit()

    def add_many_to_goods(self, goods_list):
        pass
        # TODO

    def get_goods_list_by_category(self, category):
        return self._cursor.execute('SELECT * FROM "goods" WHERE "category" == {} ORDER BY "goods"."name"'.format(category)).fetchall()

    def get_goods_by_id(self, id):
        return self._cursor.execute('SELECT * FROM "goods" WHERE "gid" == {}'.format(id)).fetchone()

    def get_goods_name_by_id(self, id):
        return self._cursor.execute('SELECT "name" FROM "goods" WHERE "gid" == {}'.format(id)).fetchone()[0]

    def create_order(self):
        if self._current_order is not None:
            return self._current_order, False


        date = datetime.today().date()
        new_order = 'order_' + str(date)

        try:
            self._cursor.execute('CREATE TABLE "'+new_order+'" ("goods_id" INTEGER NOT NULL,'
                                 ' "count" INTEGER NOT NULL, '
                                 'FOREIGN KEY("goods_id") REFERENCES "goods"("gid"))')
            self._db.commit()

        except sq.OperationalError as e:
            print(e)
            self._current_order = new_order
            return self._current_order, False

        self._current_order = new_order
        return new_order, True

    def order_is_present(self, other_order=None):
        target_order = ('order_'+str(datetime.today().date())) if other_order is None else other_order
        tables = self._cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        if (target_order,) in tables:
            if self._current_order is None:
                self._current_order = 'order_'+str(datetime.today().date())
            return True
        else:
            return False

    def add_to_order(self, gid, category, place, count):
        order_name, order = self.get_order(place)
        gid_in_order = False
        if len(order) == 0:
            gid_in_order = False
        else:
            for i in order:
                if i[0] == int(gid):
                    gid_in_order = True
                    break

        if not gid_in_order:
            self._cursor.execute(
                'INSERT INTO "main"."'+self.get_order_name_for_place(place)+'" ("goods_id", "count") VALUES ('+str(gid)+', ' + count + ');')
            self._db.commit()
        else:
            self._cursor.execute(
                'UPDATE "main"."'+self.get_order_name_for_place(place)+'" SET count = count + {} WHERE goods_id == {}'.format(count, gid)
            )
            self._db.commit()

    def clear_order(self, raw_order):
        for i in raw_order:
            if i[1] <= 0:
                raw_order.remove(i)

        return raw_order

    def close_order(self, place, number):

        target_order = self.get_order_name_for_place(place=place)

        raw_order = self._cursor.execute('SELECT * FROM "' + str(target_order)+'"').fetchall()
        if len(raw_order) == 0:
            return

        order = self.clear_order(raw_order)
        dumped_order = dumps(order)

        try:
            self._cursor.execute('''INSERT INTO history ("time", "value", "target") VALUES ("{}", "{}", "{}");'''.format(
                str(target_order)+'_'+str(datetime.now().date()),
                str(dumped_order), str(number)))
        except OperationalError:
            self._cursor.execute ('''INSERT INTO history ("time", value, "target") VALUES ("{}", "{}", "{}");'''.format (
                str (target_order)+'_'+str(datetime.now().date()),
                str (dumped_order), str(number)))
            pass
        self._db.commit()
        self._cursor.execute('DELETE FROM "'+target_order+'";')
        self._db.commit()
        self._current_order = None

    def delete_order(self, place):
        if self.order_is_present():
            self._cursor.execute ('DELETE FROM "' + self.get_order_name_for_place(place) + '";')
            self._db.commit ( )

    def delete_from_goods(self, gid):
        try:
            self._cursor.execute('DELETE FROM "goods" WHERE "gid" == {}'.format(gid))
            self._db.commit()
        except Exception as e:
            print(e)

    def delete_from_order_by_id(self, place, id):
        self._cursor.execute('DELETE FROM "'+self.get_order_name_for_place(place)+'" WHERE goods_id == {}'.format(id))


    def close_old_order(self):
        if self._current_order is None:
            return

        def last_day_of_month(any_day) :
            next_month = any_day.replace (day=28) + timedelta (days=4)
            return next_month - timedelta (days=next_month.day)

        def get_yesterday(today) :
            if today.day == 1 :
                if today.month == 1 :
                    tomorrow_month = 12
                    tomorrow_year = today.year - 1
                else :
                    tomorrow_month = today.month - 1
                    tomorrow_year = today.year
                tomorrow_day = last_day_of_month (today).day
            else :
                tomorrow_month = today.month
                tomorrow_year = today.year
                tomorrow_day = today.day - 1

            return datetime.strptime (str (tomorrow_day) + '.' + str (tomorrow_month) + '.' + str (tomorrow_year),
                                      '%d.%m.%Y').date()

        old_order = 'order_' + str(get_yesterday(datetime.now().date()))

        if self.order_is_present(old_order):
            self.close_order(old_order)


    def get_order_name_for_place(self, place):
        places = {KITCHEN: 'kitchen_order',
                  BAR:'bar_order',
                  ZEH:'zeh_order',
                  Z_6:'z_6_order'}

        return places[place]

    def get_categories_list(self):
        return self._cursor.execute("SELECT * FROM \"category\"").fetchall()

    def new_category(self, text):
        self._cursor.execute("INSERT INTO \"category\" (\"name\") VALUES (\"{}\")".format(text))
        self._db.commit()

    def delete_category(self, category):
        self._cursor.execute("DELETE FROM \"category\" WHERE id == {}".format(category))
        self._db.commit()
        self._cursor.execute("DELETE FROM \"goods\" WHERE \"category\" == {}".format(category))
        self._db.commit()

    def get_contacts(self):
        return self._cursor.execute('SELECT * FROM "contacts"').fetchall()


def main():
    db = DBHandler('bot.db')
    db.create_order()
    print(db.get_order(KITCHEN))
    print(db.get_goods_name_by_id(2))
    print(db.add_to_goods("Мята", "п.", 2))

db = DBHandler('bot.db')

def get_db():
    return db


if __name__ == "__main__":
    main()
