import os
from decimal import Decimal
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.models import (
    QuoteType,
    UnitType, 
    Material,
    Product,
    ProductMaterial,
    VariationGroup,
    VariationOption,
    VariationOptionMaterial,
    QuoteConfig, ProductCategory, ProductProductCategoryLink,
    Quote, QuoteProductEntry, QuoteProductEntryVariation
)
from data.seed_data import (
    UNIT_TYPES_DATA,
    MATERIALS_DATA,
    PRODUCT_CATEGORIES_DATA,
    PRODUCTS_DATA,
    QUOTE_CONFIGS_DATA,
    QUOTES_DATA
)

class BaseSeeder:
    def __init__(self, session: Session):
        self.session = session

    def _get_or_create(self, model, defaults=None, **kwargs):
        instance = self.session.exec(select(model).filter_by(**kwargs)).first()
        if instance:
            return instance, False
        else:
            params = {**kwargs, **(defaults or {})}
            instance = model(**params)
            try:
                self.session.add(instance)
                self.session.commit()
                self.session.refresh(instance)
                return instance, True
            except IntegrityError:
                self.session.rollback()
                instance = self.session.exec(select(model).filter_by(**kwargs)).first()
                return instance, False

    def seed(self):
        raise NotImplementedError("Subclasses should implement this method.")

class UnitTypeSeeder(BaseSeeder):
    def seed(self):
        print("Seeding Unit Types...")
        for ut_data in UNIT_TYPES_DATA:
            unit_type, created = self._get_or_create(
                UnitType,
                name=ut_data["name"],
                defaults={'category': ut_data["category"]} # Removed description as it's not in UnitTypeBase
            )
            if created:
                print(f"Created UnitType: {unit_type.name}")
            else:
                print(f"UnitType already exists: {unit_type.name}")
        print("Unit Types seeding complete.")

class MaterialSeeder(BaseSeeder):
    def _get_unit_type_id_by_name(self, name: str) -> int:
        unit_type = self.session.exec(select(UnitType).where(UnitType.name == name)).first()
        if not unit_type:
            raise ValueError(f"UnitType with name '{name}' not found. Ensure it was seeded first.")
        return unit_type.id

    def seed(self):
        print("Seeding Materials...")
        for mat_data in MATERIALS_DATA:
            # Use unit_type_name as the single unit_type
            unit_type_id = self._get_unit_type_id_by_name(mat_data["unit_type_name"])
            
            material, created = self._get_or_create(
                Material,
                name=mat_data["name"],
                defaults={
                    'description': mat_data.get("description"),
                    'cost_per_supplier_unit': Decimal(str(mat_data["cost_per_supplier_unit"])),
                    'quantity_in_supplier_unit': Decimal(str(mat_data.get("quantity_in_supplier_unit", "1.0"))),
                    'unit_type_id': unit_type_id,
                    'cull_rate': float(mat_data.get("cull_rate", 0.0))
                }
            )
            if created:
                print(f"Created Material: {material.name}")
            else:
                print(f"Material already exists: {material.name}")
        print("Materials seeding complete.")

class ProductCategorySeeder(BaseSeeder):
    def seed(self):
        print("Seeding Product Categories...")
        for cat_data in PRODUCT_CATEGORIES_DATA:
            category, created = self._get_or_create(
                ProductCategory,
                name=cat_data["name"],
                defaults={
                    'type': cat_data.get("type", "general"),
                    'image_url': cat_data.get("image_url")
                }
            )
            if created:
                print(f"Created ProductCategory: {category.name}")
            else:
                print(f"ProductCategory already exists: {category.name}")
        print("Product Categories seeding complete.")

class ProductSeeder(BaseSeeder):
    def _get_unit_type_id_by_name(self, name: str) -> int:
        unit_type = self.session.exec(select(UnitType).where(UnitType.name == name)).first()
        if not unit_type:
            raise ValueError(f"UnitType with name '{name}' not found.")
        return unit_type.id

    def _get_material_id_by_name(self, name: str) -> int:
        material = self.session.exec(select(Material).where(Material.name == name)).first()
        if not material:
            raise ValueError(f"Material with name '{name}' not found.")
        return material.id

    def _get_product_category_id_by_name(self, name: str) -> int:
        category = self.session.exec(select(ProductCategory).where(ProductCategory.name == name)).first()
        if not category:
            raise ValueError(f"ProductCategory with name '{name}' not found.")
        return category.id

    def seed(self):
        print("Seeding Products, ProductMaterials, Categories, and Variations...")
        for prod_data in PRODUCTS_DATA:
            product_unit_type_id = self._get_unit_type_id_by_name(prod_data["product_unit_type_name"])
            
            product, created = self._get_or_create(
                Product,
                name=prod_data["name"],
                defaults={
                    'description': prod_data.get("description"),
                    'product_unit_type_id': product_unit_type_id,
                    'unit_labor_cost': Decimal(str(prod_data.get("unit_labor_cost", "0.00"))),
                    'image_url': prod_data.get("image_url")
                }
            )

            if created:
                print(f"Created Product: {product.name}")
            else:
                print(f"Product already exists: {product.name}")

            # Seed ProductMaterials
            if "materials" in prod_data:
                for pm_data in prod_data["materials"]:
                    material_id = self._get_material_id_by_name(pm_data["material_name"])
                    pm, pm_created = self._get_or_create(
                        ProductMaterial,
                        product_id=product.id,
                        material_id=material_id,
                        defaults={'material_amount': Decimal(str(pm_data["quantity_per_product_unit"]))}
                    )
                    if pm_created:
                        print(f"  Linked Material '{pm_data['material_name']}' to Product '{product.name}'")

            # Seed Product-Category Links
            if "category_names" in prod_data:
                for cat_name in prod_data["category_names"]:
                    try:
                        category_id = self._get_product_category_id_by_name(cat_name)
                        link, link_created = self._get_or_create(
                            ProductProductCategoryLink,
                            product_id=product.id,
                            product_category_id=category_id
                        )
                        if link_created:
                             print(f"  Linked Category '{cat_name}' to Product '{product.name}'")
                    except ValueError as e:
                        print(f"  Warning: Could not link product '{product.name}' to category '{cat_name}': {e}")
            
            # Seed VariationGroups and VariationOptions
            if "variation_groups" in prod_data:
                for vg_data in prod_data["variation_groups"]:
                    vg, vg_created = self._get_or_create(
                        VariationGroup,
                        product_id=product.id,
                        name=vg_data["name"],
                        defaults={
                            'selection_type': vg_data.get("selection_type", "single_choice"),
                            'is_required': vg_data.get("is_required", False)
                        }
                    )
                    if vg_created:
                        print(f"  Created VariationGroup '{vg.name}' for Product '{product.name}'")

                    if "options" in vg_data:
                        for vo_data in vg_data["options"]:
                            vo, vo_created = self._get_or_create(
                                VariationOption,
                                variation_group_id=vg.id,
                                name=vo_data["name"],
                                defaults={
                                    'value_description': vo_data.get("value_description"),
                                    'additional_price': Decimal(str(vo_data.get("additional_price", "0.00"))),
                                    'price_multiplier': Decimal(str(vo_data.get("price_multiplier", "1.000"))),
                                    'additional_labor_cost_per_product_unit': Decimal(str(vo_data.get("additional_labor_cost_per_product_unit", "0.00")))
                                }
                            )
                            if vo_created:
                                print(f"    Created VariationOption '{vo.name}' for Group '{vg.name}'")

                            if "materials_added" in vo_data:
                                for vom_data in vo_data["materials_added"]:
                                    material_id = self._get_material_id_by_name(vom_data["material_name"])
                                    vom, vom_created = self._get_or_create(
                                        VariationOptionMaterial,
                                        variation_option_id=vo.id,
                                        material_id=material_id,
                                        defaults={'quantity_of_material_base_units_added': Decimal(str(vom_data["quantity_added"]))}
                                    )
                                    if vom_created:
                                        print(f"      Added Material '{vom_data['material_name']}' to Option '{vo.name}'")
        print("Products, their materials, categories, and variations seeding complete.")

class QuoteConfigSeeder(BaseSeeder):
    def seed(self):
        print("Seeding Quote Configs...")
        for qc_data in QUOTE_CONFIGS_DATA:
            qc, created = self._get_or_create(
                QuoteConfig,
                name=qc_data["name"],
                defaults={
                    'margin_rate': Decimal(str(qc_data["margin_rate"])),
                    'tax_rate': Decimal(str(qc_data["tax_rate"])),
                    'sales_commission_rate': Decimal(str(qc_data["sales_commission_rate"])),
                    'franchise_fee_rate': Decimal(str(qc_data["franchise_fee_rate"])),
                    'additional_fixed_fees': Decimal(str(qc_data["additional_fixed_fees"])),
                    'round_up_materials': qc_data.get("round_up_materials", True)
                }
            )
            if created:
                print(f"Created QuoteConfig: {qc.name}")
            else:
                print(f"QuoteConfig already exists: {qc.name}")
        print("Quote Configs seeding complete.")

class QuoteSeeder(BaseSeeder):
    def _get_quote_config_id_by_name(self, name: str) -> int:
        quote_config = self.session.exec(select(QuoteConfig).where(QuoteConfig.name == name)).first()
        if not quote_config:
            raise ValueError(f"QuoteConfig with name '{name}' not found.")
        return quote_config.id

    def _get_product_id_by_name(self, name: str) -> int:
        product = self.session.exec(select(Product).where(Product.name == name)).first()
        if not product:
            raise ValueError(f"Product with name '{name}' not found.")
        return product.id

    def _get_variation_option_id(self, product_id: int, group_name: str, option_name: str) -> int:
        variation_group = self.session.exec(
            select(VariationGroup).where(VariationGroup.product_id == product_id, VariationGroup.name == group_name)
        ).first()
        if not variation_group:
            raise ValueError(f"VariationGroup '{group_name}' for product_id '{product_id}' not found.")
        
        variation_option = self.session.exec(
            select(VariationOption).where(VariationOption.variation_group_id == variation_group.id, VariationOption.name == option_name)
        ).first()
        if not variation_option:
            raise ValueError(f"VariationOption '{option_name}' for group '{group_name}' not found.")
        return variation_option.id

    def seed(self):
        print("Seeding Quotes...")
        for quote_data in QUOTES_DATA:
            quote_config_id = self._get_quote_config_id_by_name(quote_data["quote_config_name"])
            
            quote, created = self._get_or_create(
                Quote,
                name=quote_data["name"],
                quote_config_id=quote_config_id,
                # Add other Quote fields from quote_data if necessary, e.g., user_id, status
                defaults={ # Ensure all required fields for QuoteBase are covered or have defaults
                    'user_id': quote_data.get('user_id'), # Example: add if you have user_id
                    # 'status': quote_data.get('status', 'DRAFT'),
                    'quote_type': quote_data.get('quote_type', QuoteType.GENERAL) 
                }
            )

            if created:
                print(f"Created Quote: {quote.name}")
            else:
                print(f"Quote already exists: {quote.name}")

            if "product_entries" in quote_data:
                for entry_data in quote_data["product_entries"]:
                    product_id = self._get_product_id_by_name(entry_data["product_name"])
                    
                    quote_entry, entry_created = self._get_or_create(
                        QuoteProductEntry,
                        quote_id=quote.id,
                        product_id=product_id,
                        # Using a combination of quote_id and product_id might not be unique enough
                        # if a quote can have the same product multiple times without other distinctions.
                        # Consider adding a unique identifier from entry_data if available, or rely on creation order.
                        defaults={
                            'quantity_of_product_units': Decimal(str(entry_data["quantity_of_product_units"])),
                            'product_role': entry_data.get('product_role', 'default')
                            # Add other QuoteProductEntry fields from entry_data if necessary
                        }
                    )
                    if entry_created:
                        print(f"  Added ProductEntry for '{entry_data['product_name']}' to Quote '{quote.name}'")
                    else:
                        # This might indicate an issue if you expect multiple entries of the same product
                        # without a more specific key for _get_or_create.
                        print(f"  ProductEntry for '{entry_data['product_name']}' in Quote '{quote.name}' already exists.") 


                    if "selected_variations" in entry_data and quote_entry:
                        for var_data in entry_data["selected_variations"]:
                            try:
                                variation_option_id = self._get_variation_option_id(
                                    product_id=product_id, 
                                    group_name=var_data["variation_group_name"], 
                                    option_name=var_data["variation_option_name"]
                                )
                                qpev, qpev_created = self._get_or_create(
                                    QuoteProductEntryVariation,
                                    quote_product_entry_id=quote_entry.id,
                                    variation_option_id=variation_option_id
                                )
                                if qpev_created:
                                    print(f"    Selected Variation '{var_data['variation_option_name']}' for entry.")
                            except ValueError as e:
                                print(f"    Warning: Could not select variation for entry in quote '{quote.name}': {e}")
        print("Quotes seeding complete.")

def should_seed():
    """Only seed in development or when explicitly requested"""
    env = os.getenv("ENVIRONMENT", "development")
    force_seed = os.getenv("FORCE_SEED", "false").lower() == "true"
    # Add a print statement to check the values of env and force_seed
    should_seed = env == "development" or force_seed
    print(f"ENVIRONMENT: {env}, FORCE_SEED: {force_seed}, Should Seed: {should_seed}")
    return should_seed

def run_all_seeders(session: Session):
    UnitTypeSeeder(session).seed()
    MaterialSeeder(session).seed()
    ProductCategorySeeder(session).seed()
    ProductSeeder(session).seed() # Must run after UnitType, Material, ProductCategory
    QuoteConfigSeeder(session).seed()
    QuoteSeeder(session).seed() # Must run after Product, QuoteConfig, VariationOption

    print("All seeders executed.")
