-- Цена продукта опциональна (бесплатно / «см. описание»).
ALTER TABLE products ALTER COLUMN price DROP NOT NULL;
