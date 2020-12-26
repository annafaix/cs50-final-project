from db import get_db


class FoodItem():
    def __init__(self, id_, name, date, quantity, quantity_update, unit, user, cathegory):
        self.id = id_
        self.name = name
        self.date = date
        self.quantity = quantity
        self.quantity_update = quantity_update
        self.unit = unit
        self.user = user
        self.cathegory = cathegory

    @staticmethod
    def get(user):
        db = get_db()
        food_Item = db.execute(
            "SELECT * FROM fridge WHERE user = ?", (user,)
        ).fetchall()
        if not food_Item:
            return None
        foodList = []
        for food in food_Item:
            food_Item = FoodItem(
                id_=food[0], name=food[1], date=food[2], quantity=food[3], 
                quantity_update=food[4], unit=food[5], user=food[6], cathegory=food[7]
            )
            foodList.append(food_Item)
        return foodList

    @staticmethod
    def create(name, date, quantity, quantity_update, unit, user, cathegory):
        db = get_db()
        db.execute(
            "INSERT INTO fridge (name, date, quantity, quantity_update, unit, user, cathegory) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, date, quantity, quantity_update, unit, user, cathegory),
        )
        db.commit()

    @staticmethod
    def delete(id):
        db = get_db()
        db.execute("DELETE FROM fridge WHERE id = ?", (id,))
        db.commit()
    
    @staticmethod
    def update(quantity, id):
        db = get_db()
        db.execute("UPDATE fridge SET quantity_update = ? WHERE id = ?", (quantity, id))
        db.commit()
