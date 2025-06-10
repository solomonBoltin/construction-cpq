import json
from sqlmodel import Session, select # Ensure Session and select are imported
from app.database import engine, create_db_and_tables
from app.models import (
    UnitType, UnitTypeBase,
    Material, MaterialBase,
    Product, ProductBase,
    ProductMaterial, ProductMaterialBase,
    VariationGroup, VariationGroupBase,
    VariationOption, VariationOptionBase,
    VariationOptionMaterial, VariationOptionMaterialBase,
    QuoteConfig, QuoteConfigBase,
    ProductCategory, ProductCategoryBase,
    ProductProductCategoryLink
)

# Path to your seed JSON file
SEED_FILE_PATH = "seed.json"

def get_unit_type_id_by_name(session: Session, name: str) -> int:
    unit_type = session.exec(select(UnitType).where(UnitType.name == name)).first()
    if not unit_type:
        raise ValueError(f"UnitType with name '{name}' not found in the database. Ensure it was seeded first.")
    return unit_type.id

def get_material_id_by_name(session: Session, name: str) -> int:
    material = session.exec(select(Material).where(Material.name == name)).first()
    if not material:
        raise ValueError(f"Material with name '{name}' not found in the database. Ensure it was seeded first.")
    return material.id

def get_product_category_id_by_name(session: Session, name: str) -> int:
    category = session.exec(select(ProductCategory).where(ProductCategory.name == name)).first()
    if not category:
        raise ValueError(f"ProductCategory with name '{name}' not found. Ensure it was seeded first.")
    return category.id

def seed_unit_types(session: Session, unit_types_data: list):
    print("Seeding Unit Types...")
    for ut_data in unit_types_data:
        existing_ut = session.exec(select(UnitType).where(UnitType.name == ut_data["name"])).first()
        if not existing_ut:
            unit_type = UnitType.model_validate(ut_data)
            session.add(unit_type)
    session.commit()
    print("Unit Types seeded.")

def seed_materials(session: Session, materials_data: list):
    print("Seeding Materials...")
    for mat_data in materials_data:
        existing_mat = session.exec(select(Material).where(Material.name == mat_data["name"])).first()
        if not existing_mat:
            # Resolve unit type IDs from names
            supplier_unit_type_id = None
            if mat_data.get("supplier_unit_type_name"):
                 supplier_unit_type_id = get_unit_type_id_by_name(session, mat_data["supplier_unit_type_name"])
            
            base_unit_type_id = get_unit_type_id_by_name(session, mat_data["base_unit_type_name"])
            
            material_create = MaterialBase(
                name=mat_data["name"],
                description=mat_data.get("description"),
                cost_per_supplier_unit=mat_data["cost_per_supplier_unit"],
                supplier_unit_type_id=supplier_unit_type_id,
                quantity_in_supplier_unit=mat_data.get("quantity_in_supplier_unit", 1.0),
                base_unit_type_id=base_unit_type_id
            )
            material = Material.model_validate(material_create)
            session.add(material)
    session.commit()
    print("Materials seeded.")

def seed_product_categories(session: Session, categories_data: list):
    print("Seeding Product Categories...")
    for cat_data in categories_data:
        existing_cat = session.exec(select(ProductCategory).where(ProductCategory.name == cat_data["name"])).first()
        if not existing_cat:
            category = ProductCategory.model_validate(cat_data)
            session.add(category)
    session.commit()
    print("Product Categories seeded.")

def seed_products(session: Session, products_data: list):
    print("Seeding Products...")
    for prod_data in products_data:
        existing_prod = session.exec(select(Product).where(Product.name == prod_data["name"])).first()
        if not existing_prod:
            product_unit_type_id = get_unit_type_id_by_name(session, prod_data["product_unit_type_name"])
            
            product_create = ProductBase(
                name=prod_data["name"],
                description=prod_data.get("description"),
                product_unit_type_id=product_unit_type_id,
                unit_labor_cost=prod_data.get("unit_labor_cost", 0.00)
            )
            product = Product.model_validate(product_create)
            session.add(product)
            session.commit() # Commit product to get its ID for relations
            session.refresh(product)

            # Seed ProductMaterials
            if "materials" in prod_data:
                for pm_data in prod_data["materials"]:
                    material_id = get_material_id_by_name(session, pm_data["material_name"])
                    product_material_create = ProductMaterialBase(
                        product_id=product.id,
                        material_id=material_id,
                        material_amount=pm_data["quantity_per_product_unit"]
                    )
                    product_material = ProductMaterial.model_validate(product_material_create)
                    session.add(product_material)
            
            # Seed Product-Category Links
            if "category_names" in prod_data:
                for cat_name in prod_data["category_names"]:
                    try:
                        category_id = get_product_category_id_by_name(session, cat_name)
                        link = ProductProductCategoryLink(product_id=product.id, product_category_id=category_id)
                        session.add(link)
                    except ValueError as e:
                        print(f"Warning: Could not link product '{product.name}' to category '{cat_name}': {e}")
            
            # Seed VariationGroups and VariationOptions
            if "variation_groups" in prod_data:
                for vg_data in prod_data["variation_groups"]:
                    variation_group_create = VariationGroupBase(
                        product_id=product.id,
                        name=vg_data["name"],
                        selection_type=vg_data.get("selection_type", "single_choice"),
                        is_required=vg_data.get("is_required", False)
                    )
                    variation_group = VariationGroup.model_validate(variation_group_create)
                    session.add(variation_group)
                    session.commit() # Commit group to get ID
                    session.refresh(variation_group)

                    if "options" in vg_data:
                        for vo_data in vg_data["options"]:
                            variation_option_create = VariationOptionBase(
                                variation_group_id=variation_group.id,
                                name=vo_data["name"],
                                value_description=vo_data.get("value_description"),
                                additional_price=vo_data.get("additional_price", 0.00),
                                price_multiplier=vo_data.get("price_multiplier", 1.000),
                                additional_labor_cost_per_product_unit=vo_data.get("additional_labor_cost_per_product_unit", 0.00)
                            )
                            variation_option = VariationOption.model_validate(variation_option_create)
                            session.add(variation_option)
                            session.commit() # Commit option to get ID
                            session.refresh(variation_option)

                            if "materials_added" in vo_data:
                                for vom_data in vo_data["materials_added"]:
                                    material_id = get_material_id_by_name(session, vom_data["material_name"])
                                    vom_create = VariationOptionMaterialBase(
                                        variation_option_id=variation_option.id,
                                        material_id=material_id,
                                        quantity_of_material_base_units_added=vom_data["quantity_added"]
                                    )
                                    vom = VariationOptionMaterial.model_validate(vom_create)
                                    session.add(vom)
    session.commit()
    print("Products, their materials, categories, and variations seeded.")

def seed_quote_configs(session: Session, quote_configs_data: list):
    print("Seeding Quote Configs...")
    for qc_data in quote_configs_data:
        existing_qc = session.exec(select(QuoteConfig).where(QuoteConfig.name == qc_data["name"])).first()
        if not existing_qc:
            quote_config = QuoteConfig.model_validate(qc_data)
            session.add(quote_config)
    session.commit()
    print("Quote Configs seeded.")

def main():
    print("Starting database seeding process...")
    # Ensure tables are created before seeding
    # In a real app, this might be handled by Alembic migrations or app startup
    # For this script, we call it directly.
    print("Ensuring database and tables are created...")
    create_db_and_tables() # This function is in app.database
    print("Database and tables ready.")

    with open(SEED_FILE_PATH, 'r') as f:
        seed_data = json.load(f)

    with Session(engine) as session:
        if "unit_types" in seed_data:
            seed_unit_types(session, seed_data["unit_types"])
        
        if "materials" in seed_data:
            seed_materials(session, seed_data["materials"])
        
        if "product_categories" in seed_data: 
            seed_product_categories(session, seed_data["product_categories"])
        
        if "products" in seed_data:
            seed_products(session, seed_data["products"])
        
        if "quote_configs" in seed_data:
            seed_quote_configs(session, seed_data["quote_configs"])
        
        session.commit() # Final commit for any pending changes

    print("Database seeding completed successfully!")

if __name__ == "__main__":
    main()
