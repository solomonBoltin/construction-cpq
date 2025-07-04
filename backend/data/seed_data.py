from app.models import QuoteType


UNIT_TYPES_DATA = [
    { "name": "Each", "category": "count", "description": "A single item." },
    { "name": "Linear Foot", "category": "length", "description": "Measurement in linear feet." },
    { "name": "Square Foot", "category": "area" },
    { "name": "Cubic Foot", "category": "volume" },
    { "name": "Kg", "category": "mass" },
    { "name": "Lb", "category": "mass" },
    { "name": "Box", "category": "count" },
    { "name": "Sheet", "category": "count" },
    { "name": "Item", "category": "count" },
    { "name": "Set", "category": "count" },
    { "name": "Bag", "category": "count", "description": "A standard bag of material." }
]

MATERIALS_DATA = [
    {
      "name": "JPC Picket 5.5in x 6ft",
      "description": "Standard Japanese Cedar Picket",
      "cost_per_supplier_unit": 6.50,
      "quantity_in_supplier_unit": 1,
      "unit_type_name": "Each",
      "cull_rate": 0.0
    },
    {
      "name": "Postmaster Post 8ft",
      "description": "Galvanized Steel Postmaster Post, 8ft length",
      "cost_per_supplier_unit": 35.00,
      "quantity_in_supplier_unit": 1,
      "unit_type_name": "Each",
      "cull_rate": 0.0
    },
    {
      "name": "JPC 1x6x8 Raw Picket",
      "description": "Japanese Cedar Picket, 1x6x8, Raw",
      "cost_per_supplier_unit": 5.40,
      "quantity_in_supplier_unit": 1,
      "unit_type_name": "Each",
      "cull_rate": 0.05
    },
    {
      "name": "Concrete Mix 80lb",
      "description": "Standard 80lb bag of concrete mix",
      "cost_per_supplier_unit": 7.00,
      "quantity_in_supplier_unit": 1,
      "unit_type_name": "Bag",
      "cull_rate": 0.0
    },
    {
      "name": "JPC Cap Board 2x4x8",
      "description": "Japanese Cedar Cap Board 2x4, 8ft long, for cap rail variation.",
      "cost_per_supplier_unit": 12.00,
      "quantity_in_supplier_unit": 1,
      "unit_type_name": "Each",
      "cull_rate": 0.0
    }
]

PRODUCT_CATEGORIES_DATA = [
    {
      "name": "Wood Fence",
      "type": "fence",
      "image_url": "/images/categories/wood_fence.jpg"
    },
    {
      "name": "Metal Fence",
      "type": "fence",
      "image_url": "/images/categories/metal_fence.jpg"
    },
    {
      "name": "Vinyl Fence",
      "type": "fence",
      "image_url": "/images/categories/vinyl_fence.jpg"
    },
    {
      "name": "Gate",
      "type": "gate",
      "image_url": "/images/categories/gate.jpg"
    },
    {
      "name": "Project Add-ons",
      "type": "additional",
      "image_url": "/images/categories/addons.jpg"
    }
]

PRODUCTS_DATA = [
    {
      "name": "6ft Postmaster Horizontal JPC Stained Fence",
      "description": "A 6ft tall Postmaster fence with horizontal Japanese Cedar pickets, stained.",
      "product_unit_type_name": "Linear Foot",
      "unit_labor_cost": 10.00,
      "image_url": None,
      "category_names": ["Wood Fence"],
      "materials": [
        { "material_name": "JPC Picket 5.5in x 6ft", "quantity_per_product_unit": 2.182 },
        { "material_name": "Postmaster Post 8ft", "quantity_per_product_unit": 0.125 },
        { "material_name": "Concrete Mix 80lb", "quantity_per_product_unit": 0.25 }
      ],
      "variation_groups": [
        {
          "name": "Style",
          "selection_type": "SINGLE_SELECT",
          "is_required": True,
          "options": [
            {
              "name": "Side-by-Side",
              "value_description": "Pickets are placed side by side.",
              "additional_price": 0.00,
              "price_multiplier": 1.000,
              "additional_labor_cost_per_product_unit": 0.00,
              "materials_added": []
            },
            {
              "name": "Board-on-Board",
              "value_description": "Pickets overlap for full privacy.",
              "additional_price": 0.00,
              "price_multiplier": 1.000,
              "additional_labor_cost_per_product_unit": 2.00,
              "materials_added": [
                { "material_name": "JPC Picket 5.5in x 6ft", "quantity_added": 1.091 }
              ]
            }
          ]
        },
        {
          "name": "Add Cap Rail",
          "selection_type": "SINGLE_SELECT",
          "is_required": False,
          "options": [
            {
              "name": "No Cap Rail",
              "value_description": "Standard top.",
              "additional_price": 0.00,
              "materials_added": []
            },
            {
              "name": "Yes - Add Cap Rail",
              "value_description": "Adds a 2x4 cap rail on top of the fence.",
              "additional_price": 0.00,
              "additional_labor_cost_per_product_unit": 1.50,
              "materials_added": [
                { "material_name": "JPC Cap Board 2x4x8", "quantity_added": 0.125 }
              ]
            }
          ]
        }
      ]
    },
    {
      "name": "Wood Gate",
      "description": "A standard wood gate.",
      "product_unit_type_name": "Each",
      "unit_labor_cost": 50.00,
      "image_url": None,
      "category_names": ["Gate"],
      "materials": [
        { "material_name": "JPC Picket 5.5in x 6ft", "quantity_per_product_unit": 10 },
        { "material_name": "Postmaster Post 8ft", "quantity_per_product_unit": 2 },
        { "material_name": "Concrete Mix 80lb", "quantity_per_product_unit": 1 }
      ],
      "variation_groups": []
    },
    {
      "name": "Hard Digging",
      "description": "Additional labor for rocky or difficult soil (per foot).",
      "product_unit_type_name": "Linear Foot",
      "unit_labor_cost": 5.00,
      "image_url": None,
      "category_names": ["Project Add-ons"],
      "materials": [
        { "material_name": "Concrete Mix 80lb", "quantity_per_product_unit": 0.05 }
      ],
      "variation_groups": []
    },
    {
      "name": "Special Permit",
      "description": "Required for certain projects, includes filing and processing fees.",
      "product_unit_type_name": "Each",
      "unit_labor_cost": 22.00,
      "image_url": None,
      "category_names": ["Project Add-ons"],
      "materials": [
      ],
      "variation_groups": []
    }
]

QUOTE_CONFIGS_DATA = [
    {
      "name": "Residential Default",
      "margin_rate": 0.35,
      "tax_rate": 0.0825,
      "sales_commission_rate": 0.02,
      "franchise_fee_rate": 0.01,
      "additional_fixed_fees": 50.00,
      "round_up_materials": True
    },
    {
      "name": "Commercial Project Config",
      "margin_rate": 0.25,
      "tax_rate": 0.0825,
      "sales_commission_rate": 0.03,
      "franchise_fee_rate": 0.01,
      "additional_fixed_fees": 250.00,
      "round_up_materials": True
    }
]

QUOTES_DATA = [
    {
        "name": "Residential Fence Project - 100ft",
        "quote_config_name": "Residential Default",
        "quote_type": QuoteType.FENCE_PROJECT,
        "product_entries": [
            {
                "product_name": "6ft Postmaster Horizontal JPC Stained Fence",
                "quantity_of_product_units": "100.0",
                "selected_variations": [
                    {"variation_group_name": "Style", "variation_option_name": "Side-by-Side"},
                    {"variation_group_name": "Add Cap Rail", "variation_option_name": "No Cap Rail"}
                ]
            }
        ]
    }
]
