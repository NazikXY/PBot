import sqlite3 as sq
from datetime import datetime
from pickle import dumps, loads
from ast import literal_eval


class DBHandler:
    def __init__(self, db):
        self._db = sq.connect(db, check_same_thread=False)
        self._cursor = self._db.cursor()
        self._current_order = None

    def get_order_by_id(self, id):
        return self._cursor.execute("SELECT * FROM history WHERE order_id == {}".format(id)).fetchone()

    def get_order_list(self):
        return self._cursor.execute("SELECT * FROM history").fetchall()

    def set_current_order_from_history(self, order_id):
        if self._current_order is None:
            try:
                target_order = self._cursor.execute(
                    'SELECT * FROM history WHERE "order_id" == {}'.format(order_id)).fetchone()
                self.create_order()
                data = loads(literal_eval(target_order[2]))
                for i in data:
                    self._cursor.execute(
                        'INSERT INTO "{}" ("goods_id", "count") VALUES ({},{})'.format(self._current_order, i[0], i[1]))
                self._db.commit()
            except Exception as e:
                print(e)

    def get_current_order(self):
        return self._current_order, self._cursor.execute('SELECT * FROM "' + str(self._current_order) + '"').fetchall()

    def add_to_goods(self, name, units, group):
        groups = {'К': 1,
                  'Б': 2,
                  'Ц': 3}
        self._cursor.execute(
            'INSERT INTO "main"."goods" (name, units, gr) VALUES ("{}", "{}", {})'.format(name, units, groups[group]))
        self._db.commit()

    def add_many_to_goods(self, goods_list):
        pass
        # TODO

    def get_goods_list(self, gr):
        return self._cursor.execute('SELECT * FROM "goods" WHERE "gr" == {} ORDER BY "goods"."name"'.format(gr)).fetchall()

    def get_goods_by_id(self, id):
        return self._cursor.execute('SELECT * FROM "goods" goods.name WHERE "gid" == {}'.format(id)).fetchone()

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

    def order_is_present(self):
        tables = self._cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        if ('order_'+str(datetime.today().date()),) in tables:
            if self._current_order is None:
                self._current_order = 'order_'+str(datetime.today().date())
            return True
        else:
            return False

    def add_to_order(self, gid):
        order_name, order = self.get_current_order()
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
                'INSERT INTO "main"."'+str(self._current_order)+'" ("goods_id", "count") VALUES ('+str(gid)+', 1);')
            self._db.commit()
        else:
            self._cursor.execute(
                'UPDATE "main"."'+str(self._current_order)+'" SET count = count + 1 WHERE goods_id == {}'.format(gid)
            )
            self._db.commit()

    def close_order(self):
        if self._current_order is not None:
            try:
                order = self._cursor.execute('SELECT * FROM "' + str(self._current_order)+'"').fetchall()
                dumped_order = dumps(order)
                self._cursor.execute('INSERT INTO history ("time", value) VALUES ("' + str(self._current_order) +
                                     '", "'+str(dumped_order)+'");')
                self._db.commit()
                self._cursor.execute('DROP TABLE "'+self._current_order+'";')
                self._db.commit()
                self._current_order = None
            except Exception as e:
                print(e)


def main():
    db = DBHandler('bot.db')
    db.create_order()
    print(db.get_current_order())
    print(db.get_goods_name_by_id(2))
    print(db.add_to_goods("Мята", "п.", 2))


if __name__ == "__main__":
    main()
