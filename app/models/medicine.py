class Medicine:
    def __init__(
        self,
        id,
        name,
        category,
        manufacturer,
        price,
        stock_quantity,
        expiry_date,
        description,
        requires_prescription,
    ):
        self.id = id
        self.name = name
        self.category = category
        self.manufacturer = manufacturer
        self.price = price
        self.stock_quantity = stock_quantity
        self.expiry_date = expiry_date
        self.description = description
        self.requires_prescription = bool(requires_prescription)
