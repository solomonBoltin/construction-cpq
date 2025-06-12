import pytest 
from unittest.mock import MagicMock, call, patch
from decimal import Decimal
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models import (
    Quote, QuoteConfig, QuoteType, Product, ProductCategory, 
    QuoteProductEntry, ProductRole, VariationGroup, VariationOption, 
    CalculatedQuote, QuoteProductEntryVariation, ProductProductCategoryLink
)
from app.services.quote_process import (
    QuoteProcessService, QuotePreview, CategoryPreview, ProductPreview, 
    MaterializedProductEntry, VariationOptionView, VariationGroupView
)

@pytest.fixture
def quote_process_service(mock_session: MagicMock): 
    return QuoteProcessService(session=mock_session)

@pytest.fixture
def mock_product_entry_with_variations(mock_session: MagicMock, D_fixture): 
    D = D_fixture
    entry = QuoteProductEntry(
        id=1, quote_id=1, product_id=100, 
        quantity_of_product_units=D("1"), role=ProductRole.MAIN, 
        selected_variations=[]
    )
    product = Product(id=100, name="Configurable Product", product_unit_type_id=1, variation_groups=[])
    group_single = VariationGroup(id=10, product_id=100, name="Color", selection_type="single_choice", is_required=True, options=[])
    option_red = VariationOption(id=101, variation_group_id=10, name="Red", additional_price=D("10"), variation_group=group_single)
    option_blue = VariationOption(id=102, variation_group_id=10, name="Blue", additional_price=D("12"), variation_group=group_single)
    group_single.options = [option_red, option_blue]

    group_multi = VariationGroup(id=20, product_id=100, name="Features", selection_type="multi_choice", is_required=False, options=[])
    option_gps = VariationOption(id=201, variation_group_id=20, name="GPS", additional_price=D("50"), variation_group=group_multi)
    option_wifi = VariationOption(id=202, variation_group_id=20, name="WiFi", additional_price=D("30"), variation_group=group_multi)
    group_multi.options = [option_gps, option_wifi]

    product.variation_groups = [group_single, group_multi]
    entry.product = product 
    entry.selected_variations = [] 

    original_get_side_effect = mock_session.get.side_effect

    def get_side_effect(model, pk):
        if model == QuoteProductEntry and pk == entry.id: return entry
        if model == Product and pk == product.id: return product
        if model == VariationOption and pk == option_red.id: return option_red
        if model == VariationOption and pk == option_blue.id: return option_blue
        if model == VariationOption and pk == option_gps.id: return option_gps
        if model == VariationOption and pk == option_wifi.id: return option_wifi
        if model == VariationGroup and pk == group_single.id: return group_single
        if model == VariationGroup and pk == group_multi.id: return group_multi
        if original_get_side_effect: return original_get_side_effect(model, pk)
        return MagicMock()
    mock_session.get.side_effect = get_side_effect
    
    original_refresh_side_effect = mock_session.refresh.side_effect
    def refresh_side_effect(obj_to_refresh):
        if isinstance(obj_to_refresh, QuoteProductEntry):
            pass 
        if original_refresh_side_effect:
            original_refresh_side_effect(obj_to_refresh)

    mock_session.refresh.side_effect = refresh_side_effect

    return entry, product, group_single, option_red, option_blue, group_multi, option_gps, option_wifi


class TestQuoteProcessService:
    def test_create_quote_success(self, quote_process_service: QuoteProcessService, mock_session: MagicMock, D_fixture):
        D = D_fixture
        test_name = "Test Project Alpha"
        test_description = "A test quote for Project Alpha"
        test_quote_type = QuoteType.FENCE_PROJECT
        test_config_id = 1
        
        expected_quote_config = QuoteConfig(
            id=test_config_id, name="Default Config", sales_commission_rate=D("0.1"), 
            franchise_fee_rate=D("0.05"), margin_rate=D("0.2"), tax_rate=D("0.08"), 
            additional_fixed_fees=D("100")
        )
        mock_session.get.side_effect = lambda model, pk: expected_quote_config if model == QuoteConfig and pk == test_config_id else None

        new_quote = quote_process_service.create_quote(
            name=test_name, description=test_description,
            quote_type=test_quote_type, config_id=test_config_id
        )

        assert new_quote is not None
        assert new_quote.name == test_name
        assert new_quote.description == test_description
        assert new_quote.quote_type == test_quote_type
        assert new_quote.quote_config_id == test_config_id
        assert new_quote.quote_config is not None
        assert new_quote.quote_config.id == expected_quote_config.id
        assert new_quote.quote_config.name == expected_quote_config.name
        assert new_quote.status == "draft"

        mock_session.add.assert_called_once_with(new_quote)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(new_quote)

    def test_get_quotes_no_filter(self, quote_process_service: QuoteProcessService, mock_session: MagicMock):
        mock_quote_1 = Quote(id=1, name="Quote 1", status="draft", quote_type=QuoteType.FENCE_PROJECT, updated_at=datetime.now(timezone.utc))
        mock_quote_2 = Quote(id=2, name="Quote 2", status="approved", quote_type=QuoteType.DECK_PROJECT, updated_at=datetime.now(timezone.utc))
        
        mock_exec_result = MagicMock()
        mock_exec_result.all.return_value = [mock_quote_1, mock_quote_2]
        mock_session.exec.side_effect = [mock_exec_result]

        result = quote_process_service.get_quotes()

        assert len(result) == 2
        assert isinstance(result[0], QuotePreview)
        assert result[0].id == mock_quote_1.id
        assert result[1].name == mock_quote_2.name
        mock_session.exec.assert_called_once()
        assert "WHERE" not in str(mock_session.exec.call_args[0][0]).upper()

    def test_create_quote_config_not_found(self, quote_process_service: QuoteProcessService, mock_session: MagicMock):
        mock_session.get.return_value = None
        
        with pytest.raises(ValueError, match="QuoteConfig with id 99 not found"):
            quote_process_service.create_quote("Test", "Desc", QuoteType.FENCE_PROJECT, config_id=99)
        
        mock_session.get.assert_called_once_with(QuoteConfig, 99)

    def test_get_quotes_with_filter(self, quote_process_service: QuoteProcessService, mock_session: MagicMock):
        mock_fence_quote = Quote(id=1, name="Fence Quote", status="draft", quote_type=QuoteType.FENCE_PROJECT, updated_at=datetime.now(timezone.utc))
        
        mock_exec_result = MagicMock()
        mock_exec_result.all.return_value = [mock_fence_quote]
        mock_session.exec.side_effect = [mock_exec_result]

        result = quote_process_service.get_quotes(quote_type=QuoteType.FENCE_PROJECT)

        assert len(result) == 1
        assert result[0].id == mock_fence_quote.id
        assert result[0].quote_type == QuoteType.FENCE_PROJECT
        mock_session.exec.assert_called_once()
        sql_query_str = str(mock_session.exec.call_args[0][0]).upper()
        assert "WHERE" in sql_query_str
        assert "QUOTE.QUOTE_TYPE" in sql_query_str

    def test_get_categories_previews(self, quote_process_service: QuoteProcessService, mock_session: MagicMock):
        mock_cat_1 = ProductCategory(id=1, name="Fencing", image_url="fence.jpg")
        mock_cat_2 = ProductCategory(id=2, name="Decking")
        
        mock_exec_result = MagicMock()
        mock_exec_result.all.return_value = [mock_cat_1, mock_cat_2]
        mock_session.exec.side_effect = [mock_exec_result]

        result = quote_process_service.get_categories_previews()

        assert len(result) == 2
        assert isinstance(result[0], CategoryPreview)
        assert result[0].name == mock_cat_1.name
        assert result[0].image_url == mock_cat_1.image_url
        assert result[1].name == mock_cat_2.name
        assert result[1].image_url is None
        mock_session.exec.assert_called_once()

    def test_get_categories_previews_with_type_filter(self, quote_process_service: QuoteProcessService, mock_session: MagicMock):
        mock_fence_cat = ProductCategory(id=1, name="Fencing", type="fence_material", image_url="fence.jpg")
        
        mock_exec_result = MagicMock()
        mock_exec_result.all.return_value = [mock_fence_cat]
        mock_session.exec.side_effect = [mock_exec_result]

        category_type_filter = "fence_material"
        result = quote_process_service.get_categories_previews(category_type=category_type_filter, offset=0, limit=10)

        assert len(result) == 1
        assert result[0].name == mock_fence_cat.name
        mock_session.exec.assert_called_once()
        called_statement = mock_session.exec.call_args[0][0]
        sql_query_str = str(called_statement).upper()
        assert "WHERE PRODUCT_CATEGORY.TYPE = " in sql_query_str
        assert called_statement._offset_clause is not None
        assert called_statement._limit_clause is not None

    def test_get_products_previews(self, quote_process_service: QuoteProcessService, mock_session: MagicMock):
        category_name = "Fencing"
        mock_category = ProductCategory(id=1, name=category_name)
        mock_prod_1 = Product(id=1, name="Wood Panel", description="Standard wood panel", product_unit_type_id=1)
        mock_prod_2 = Product(id=2, name="Metal Post", description="Strong metal post", product_unit_type_id=1)

        mock_category_exec_result = MagicMock()
        mock_category_exec_result.first.return_value = mock_category
        
        mock_products_exec_result = MagicMock()
        mock_products_exec_result.all.return_value = [mock_prod_1, mock_prod_2]
        
        mock_session.exec.side_effect = [mock_category_exec_result, mock_products_exec_result]

        result = quote_process_service.get_products_previews(category_name=category_name)

        assert len(result) == 2
        assert isinstance(result[0], ProductPreview)
        assert result[0].name == mock_prod_1.name
        assert result[0].image_url is None
        assert result[1].description == mock_prod_2.description
        assert result[1].image_url is None
        assert mock_session.exec.call_count == 2
        cat_fetch_sql_str = str(mock_session.exec.call_args_list[0][0][0]).upper()
        assert "SELECT PRODUCT_CATEGORY.ID, PRODUCT_CATEGORY.NAME, PRODUCT_CATEGORY.TYPE, PRODUCT_CATEGORY.IMAGE_URL" in cat_fetch_sql_str
        assert f"WHERE PRODUCT_CATEGORY.NAME = :NAME_1" in cat_fetch_sql_str

        prod_fetch_sql_str = str(mock_session.exec.call_args_list[1][0][0]).upper()
        assert "JOIN PRODUCT_PRODUCT_CATEGORY_LINK" in prod_fetch_sql_str
        assert "PRODUCT_PRODUCT_CATEGORY_LINK.PRODUCT_CATEGORY_ID" in prod_fetch_sql_str

    def test_get_products_previews_pagination_and_filter(self, quote_process_service: QuoteProcessService, mock_session: MagicMock):
        category_name = "Wood Fences"
        mock_category = ProductCategory(id=5, name=category_name, type="fence")
        mock_product_1 = Product(id=101, name="Pine Fence Panel", product_unit_type_id=1)
        mock_product_2 = Product(id=102, name="Cedar Fence Panel", product_unit_type_id=1)
        
        mock_category_exec_result = MagicMock()
        mock_category_exec_result.first.return_value = mock_category
        mock_products_exec_result = MagicMock()
        mock_products_exec_result.all.return_value = [mock_product_1, mock_product_2]
        
        mock_session.exec.side_effect = [mock_category_exec_result, mock_products_exec_result]

        offset = 0
        limit = 5
        results = quote_process_service.get_products_previews(category_name=category_name, offset=offset, limit=limit)

        assert len(results) == 2
        assert results[0].name == mock_product_1.name
        assert results[1].name == mock_product_2.name
        
        assert mock_session.exec.call_count == 2
        cat_fetch_statement = str(mock_session.exec.call_args_list[0][0][0]).upper()
        assert f"WHERE PRODUCT_CATEGORY.NAME = " in cat_fetch_statement

        prod_fetch_statement = mock_session.exec.call_args_list[1][0][0]
        prod_fetch_sql_str = str(prod_fetch_statement).upper()
        assert "JOIN PRODUCT_PRODUCT_CATEGORY_LINK" in prod_fetch_sql_str
        assert "WHERE PRODUCT_PRODUCT_CATEGORY_LINK.PRODUCT_CATEGORY_ID = " in prod_fetch_sql_str
        assert prod_fetch_statement._offset_clause is not None
        assert prod_fetch_statement._limit_clause is not None

    def test_add_quote_product_entry_success(self, quote_process_service: QuoteProcessService, mock_session: MagicMock, D_fixture):
        D = D_fixture
        quote_id = 1
        product_id = 10
        quantity = D("10.5")
        role = ProductRole.MAIN

        mock_quote = Quote(id=quote_id, name="Test Quote") 
        mock_product = Product(id=product_id, name="Test Product", product_unit_type_id=1, variation_groups=[]) 
        
        original_get_side_effect = mock_session.get.side_effect

        def get_side_effect(model, pk):
            if model == Quote and pk == quote_id: return mock_quote
            if model == Product and pk == product_id: return mock_product
            if original_get_side_effect: return original_get_side_effect(model, pk)
            return MagicMock() 
        mock_session.get.side_effect = get_side_effect
        
        mock_main_check_exec = MagicMock()
        mock_main_check_exec.first.return_value = None
        
        mock_materialize_vg_exec = MagicMock()
        mock_materialize_vg_exec.all.return_value = []
        
        mock_session.exec.side_effect = [mock_main_check_exec, mock_materialize_vg_exec]

        original_refresh_side_effect = mock_session.refresh.side_effect
        def refresh_side_effect(obj_to_refresh):
            if isinstance(obj_to_refresh, QuoteProductEntry):
                obj_to_refresh.id = 123 
                obj_to_refresh.selected_variations = [] 
            if original_refresh_side_effect:
                original_refresh_side_effect(obj_to_refresh)
        mock_session.refresh.side_effect = refresh_side_effect

        result_entry = quote_process_service.add_quote_product_entry(quote_id, product_id, quantity, role)

        assert isinstance(result_entry, MaterializedProductEntry)
        assert result_entry.product_id == product_id
        assert result_entry.quantity_of_product_units == quantity
        assert result_entry.role == role
        assert result_entry.product_name == mock_product.name
        assert result_entry.id == 123

        mock_session.add.assert_called_once()
        new_entry_arg = mock_session.add.call_args[0][0]
        assert isinstance(new_entry_arg, QuoteProductEntry)
        assert new_entry_arg.quote_id == quote_id
        assert new_entry_arg.product_id == product_id
        assert new_entry_arg.quantity_of_product_units == quantity
        assert new_entry_arg.role == role
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(new_entry_arg)
        assert new_entry_arg.id == 123

    def test_add_quote_product_entry_quote_not_found(self, quote_process_service: QuoteProcessService, mock_session: MagicMock, D_fixture):
        D = D_fixture
        mock_session.get.return_value = None

        with pytest.raises(ValueError, match="Quote with id 99 not found"):
            quote_process_service.add_quote_product_entry(99, 10, D("1"), ProductRole.MAIN)
        mock_session.get.assert_called_once_with(Quote, 99)
        mock_session.add.assert_not_called()

    def test_add_quote_product_entry_main_product_exists(self, quote_process_service: QuoteProcessService, mock_session: MagicMock, D_fixture):
        D = D_fixture
        quote_id = 1
        mock_quote = Quote(id=quote_id, name="Test Quote")
        existing_main_entry = QuoteProductEntry(id=50, quote_id=quote_id, product_id=5, quantity_of_product_units=D("1"), role=ProductRole.MAIN)

        mock_session.get.return_value = mock_quote
        
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = existing_main_entry
        mock_session.exec.side_effect = [mock_exec_result]

        with pytest.raises(ValueError, match="A main product already exists for this quote"):
            quote_process_service.add_quote_product_entry(quote_id, 10, D("1"), ProductRole.MAIN)
        
        mock_session.get.assert_called_once_with(Quote, quote_id)

    def test_get_quote_product_entries_no_role_filter(self, quote_process_service: QuoteProcessService, mock_session: MagicMock, D_fixture):
        D = D_fixture
        quote_id = 1
        mock_product_1 = Product(id=101, name="Main Product", product_unit_type_id=1, variation_groups=[])
        mock_product_2 = Product(id=102, name="Secondary Product", product_unit_type_id=1, variation_groups=[])
        mock_entry_1 = QuoteProductEntry(id=1, quote_id=quote_id, product_id=101, product=mock_product_1, quantity_of_product_units=D("2"), role=ProductRole.MAIN, selected_variations=[])
        mock_entry_2 = QuoteProductEntry(id=2, quote_id=quote_id, product_id=102, product=mock_product_2, quantity_of_product_units=D("5"), role=ProductRole.SECONDARY, selected_variations=[])

        mock_get_entries_exec = MagicMock()
        mock_get_entries_exec.all.return_value = [mock_entry_1, mock_entry_2]
        
        mock_materialize_vg_entry1_exec = MagicMock()
        mock_materialize_vg_entry1_exec.all.return_value = []
        mock_materialize_vg_entry2_exec = MagicMock()
        mock_materialize_vg_entry2_exec.all.return_value = []

        mock_session.exec.side_effect = [mock_get_entries_exec, mock_materialize_vg_entry1_exec, mock_materialize_vg_entry2_exec]
        
        original_get_side_effect = mock_session.get.side_effect

        def get_side_effect(model, pk):
            if model == Product and pk == 101: return mock_product_1
            if model == Product and pk == 102: return mock_product_2
            if original_get_side_effect: return original_get_side_effect(model, pk)
            return MagicMock()
        mock_session.get.side_effect = get_side_effect

        results = quote_process_service.get_quote_product_entries(quote_id)

        assert len(results) == 2
        assert results[0].id == mock_entry_1.id
        assert results[1].product_name == mock_product_2.name
        assert "ROLE = " not in str(mock_session.exec.call_args_list[0][0][0]).upper()

    def test_get_quote_product_entries_with_role_filter(self, quote_process_service: QuoteProcessService, mock_session: MagicMock, D_fixture):
        D = D_fixture
        quote_id = 1
        mock_product_1 = Product(id=101, name="Main Product", product_unit_type_id=1, variation_groups=[])
        mock_main_entry = QuoteProductEntry(id=1, quote_id=quote_id, product_id=101, product=mock_product_1, quantity_of_product_units=D("1"), role=ProductRole.MAIN, selected_variations=[])
        
        mock_get_entries_exec = MagicMock()
        mock_get_entries_exec.all.return_value = [mock_main_entry]
        mock_materialize_vg_exec = MagicMock()
        mock_materialize_vg_exec.all.return_value = []
        mock_session.exec.side_effect = [mock_get_entries_exec, mock_materialize_vg_exec]

        original_get_side_effect = mock_session.get.side_effect
        def get_side_effect(model, pk):
            if model == Product and pk == 101: return mock_product_1
            original_get_side_effect(model, pk)
        mock_session.get.side_effect = get_side_effect

        results = quote_process_service.get_quote_product_entries(quote_id, role=ProductRole.MAIN)

        assert len(results) == 1
        assert results[0].id == mock_main_entry.id
        assert results[0].role == ProductRole.MAIN
        assert results[0].product_name == mock_product_1.name
        
        sql_query_str = str(mock_session.exec.call_args_list[0][0][0]).upper()
        assert "ROLE = " in sql_query_str

    def test_delete_quote_product_entry_success(self, quote_process_service: QuoteProcessService, mock_session: MagicMock, D_fixture):
        D = D_fixture
        quote_id = 1
        entry_id = 10
        mock_entry = QuoteProductEntry(id=entry_id, quote_id=quote_id, product_id=101, quantity_of_product_units=D("1"), role=ProductRole.MAIN)
        mock_session.get.return_value = mock_entry

        quote_process_service.delete_quote_product_entry(quote_id, entry_id)

        mock_session.get.assert_called_once_with(QuoteProductEntry, entry_id)
        mock_session.delete.assert_called_once_with(mock_entry)
        mock_session.commit.assert_called_once()

    def test_delete_quote_product_entry_not_found(self, quote_process_service: QuoteProcessService, mock_session: MagicMock):
        entry_id = 10
        mock_session.get.return_value = None

        with pytest.raises(HTTPException, match=f"QuoteProductEntry with id {entry_id} not found"):
            quote_process_service.delete_quote_product_entry(1, entry_id)
        
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_delete_quote_product_entry_quote_mismatch(self, quote_process_service: QuoteProcessService, mock_session: MagicMock, D_fixture):
        D = D_fixture
        quote_id = 1
        wrong_quote_id = 2
        entry_id = 10
        mock_entry = QuoteProductEntry(id=entry_id, quote_id=wrong_quote_id, product_id=101, quantity_of_product_units=D("1"), role=ProductRole.MAIN)
        mock_session.get.return_value = mock_entry

        with pytest.raises(HTTPException, match=f"QuoteProductEntry with id {entry_id} does not belong to quote {quote_id}"):
            quote_process_service.delete_quote_product_entry(quote_id, entry_id)
        
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_get_quote_product_entry_success(self, quote_process_service: QuoteProcessService, mock_session: MagicMock, mock_product_entry_with_variations):
        entry, product, variation_group, _, _, _, _, _ = mock_product_entry_with_variations
        product_entry_id = entry.id

        mock_entry_fetch_exec = MagicMock()
        mock_entry_fetch_exec.first.return_value = entry
        mock_materialize_vg_exec = MagicMock()
        mock_materialize_vg_exec.all.return_value = product.variation_groups
        
        mock_session.exec.side_effect = [mock_entry_fetch_exec, mock_materialize_vg_exec]

        result = quote_process_service.get_quote_product_entry(product_entry_id)

        assert isinstance(result, MaterializedProductEntry)
        assert result.id == product_entry_id
        assert result.product_name == product.name
        assert len(result.variation_groups) > 0
        assert result.variation_groups[0].name == variation_group.name

    def test_get_quote_product_entry_not_found(self, quote_process_service: QuoteProcessService, mock_session: MagicMock):
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = None
        mock_session.exec.side_effect = [mock_exec_result]
        
        with pytest.raises(HTTPException, match="QuoteProductEntry with id 99 not found"):
            quote_process_service.get_quote_product_entry(99)

    @pytest.mark.skip(reason="Incomplete test, needs proper implementation")
    def test_set_quote_product_variation_option_single_choice_new_selection(
        self, quote_process_service: QuoteProcessService, mock_session: MagicMock, 
        mock_product_entry_with_variations
    ):
        entry, product, group_single, option_red, _, _, _, _ = mock_product_entry_with_variations
        product_entry_id = entry.id
        variation_option_id_to_set = option_red.id

        entry.selected_variations = []

        mock_exec_existing_selection = MagicMock()
        mock_exec_existing_selection.all.return_value = [] 
        mock_exec_materialize_groups = MagicMock()
        mock_exec_materialize_groups.all.return_value = product.variation_groups
        
        mock_exec_refresh_entry = MagicMock()
        mock_exec_refresh_entry.one.return_value = entry

        mock_session.exec.side_effect = [mock_exec_existing_selection, mock_exec_materialize_groups]

        result = quote_process_service.set_quote_product_variation_option(product_entry_id, variation_option_id_to_set)

        assert isinstance(result, MaterializedProductEntry)
        mock_session.add.assert_called_once()
        new_selection = mock_session.add.call_args[0][0]
        assert isinstance(new_selection, QuoteProductEntryVariation)
        assert new_selection.quote_product_entry_id == product_entry_id
        assert new_selection.variation_option_id == variation_option_id_to_set
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_with(entry)

    @pytest.mark.skip(reason="Incomplete test, needs proper implementation")
    def test_set_quote_product_variation_option_single_choice_replace_existing(self, quote_process_service: QuoteProcessService, mock_session: MagicMock, mock_product_entry_with_variations):
        entry, product, group_single, option_red, option_blue, _, _, _ = mock_product_entry_with_variations
        product_entry_id = entry.id
        variation_option_id_to_set = option_blue.id

        existing_selection = QuoteProductEntryVariation(quote_product_entry_id=entry.id, variation_option_id=option_red.id, variation_option=option_red)
        entry.selected_variations = [existing_selection]

        mock_exec_existing_selection = MagicMock()
        mock_exec_existing_selection.all.return_value = [existing_selection]

        mock_exec_for_refresh = MagicMock()
        mock_exec_for_refresh.one.return_value = entry

        mock_exec_materialize_groups = MagicMock()
        mock_exec_materialize_groups.all.return_value = product.variation_groups

        mock_session.exec.side_effect = [mock_exec_existing_selection, mock_exec_materialize_groups]

        result = quote_process_service.set_quote_product_variation_option(product_entry_id, variation_option_id_to_set)

        mock_session.delete.assert_called_once_with(existing_selection)
        mock_session.add.assert_called_once()
        new_selection_added = mock_session.add.call_args[0][0]
        assert isinstance(new_selection_added, QuoteProductEntryVariation)
        assert new_selection_added.quote_product_entry_id == product_entry_id
        assert new_selection_added.variation_option_id == variation_option_id_to_set
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_with(entry)

    def test_set_quote_product_variation_option_multi_choice_deselect_option(self, quote_process_service: QuoteProcessService, mock_session: MagicMock, mock_product_entry_with_variations):
        entry, product, _, _, _, group_multi, option_gps, _ = mock_product_entry_with_variations
        product_entry_id = entry.id
        variation_option_id_to_deselect = option_gps.id

        initial_selection_gps = QuoteProductEntryVariation(id=301, quote_product_entry_id=product_entry_id, variation_option_id=option_gps.id, variation_option=option_gps)
        entry.selected_variations = [initial_selection_gps]

        mock_exec_specific_selection = MagicMock()
        mock_exec_specific_selection.first.return_value = initial_selection_gps
        mock_exec_materialize_groups = MagicMock()
        mock_exec_materialize_groups.all.return_value = product.variation_groups
        
        mock_exec_refresh_entry = MagicMock()
        mock_exec_refresh_entry.one.return_value = entry
        
        mock_session.exec.side_effect = [mock_exec_specific_selection, mock_exec_materialize_groups]

        result = quote_process_service.set_quote_product_variation_option(product_entry_id, variation_option_id_to_deselect)

        mock_session.delete.assert_called_once_with(initial_selection_gps)
        
        entry.selected_variations = []
        mock_session.exec.side_effect = [mock_exec_materialize_groups]
        refreshed_materialized_result = quote_process_service._materialize_product_entry(entry)
        assert not any(opt.id == option_gps.id and opt.is_selected for grp in refreshed_materialized_result.variation_groups if grp.id == group_multi.id for opt in grp.options)

    def test_set_quote_product_variation_option_multi_choice_select_second_option(
        self, quote_process_service: QuoteProcessService, mock_session: MagicMock,
        mock_product_entry_with_variations
    ):
        entry, product, _, _, _, group_multi, option_gps, option_wifi = mock_product_entry_with_variations
        product_entry_id = entry.id
        
        initial_selection_gps = QuoteProductEntryVariation(id=301, quote_product_entry_id=product_entry_id, variation_option_id=option_gps.id, variation_option=option_gps)
        entry.selected_variations = [initial_selection_gps]
        variation_option_id_to_add = option_wifi.id

        mock_exec_specific_selection = MagicMock()
        mock_exec_specific_selection.first.return_value = None
        mock_exec_materialize_groups = MagicMock()
        mock_exec_materialize_groups.all.return_value = product.variation_groups
        
        mock_exec_refresh_entry = MagicMock()
        mock_exec_refresh_entry.one.return_value = entry
        
        mock_session.exec.side_effect = [mock_exec_specific_selection, mock_exec_materialize_groups]
        
        result = quote_process_service.set_quote_product_variation_option(product_entry_id, variation_option_id_to_add)

        mock_session.add.assert_called_once()
        new_selection_wifi = mock_session.add.call_args[0][0]
        assert new_selection_wifi.variation_option_id == variation_option_id_to_add
        
        entry.selected_variations.append(new_selection_wifi)
        mock_session.exec.side_effect = [mock_exec_materialize_groups]
        refreshed_materialized_result = quote_process_service._materialize_product_entry(entry)
        
        gps_selected = any(opt.id == option_gps.id and opt.is_selected for grp in refreshed_materialized_result.variation_groups if grp.id == group_multi.id for opt in grp.options)
        wifi_selected = any(opt.id == option_wifi.id and opt.is_selected for grp in refreshed_materialized_result.variation_groups if grp.id == group_multi.id for opt in grp.options)
        
        assert gps_selected, "GPS option should be selected"
        assert wifi_selected, "WiFi option should be selected"

    def test_update_quote_ui_state_success(self, quote_process_service: QuoteProcessService, mock_session: MagicMock, D_fixture):
        D = D_fixture
        quote_id = 1
        new_ui_state = "pick_main_product"
        mock_quote = Quote(id=quote_id, name="Test Quote", ui_state="initial_state", quote_config_id=1, quote_type=QuoteType.FENCE_PROJECT, status="draft")
        
        original_get_side_effect = mock_session.get.side_effect
        def get_side_effect_for_quote(model, pk):
            if model == Quote and pk == quote_id: return mock_quote
            if model == QuoteConfig and pk == 1: 
                return QuoteConfig(id=1, name="Default Config", sales_commission_rate=D("0.1"), franchise_fee_rate=D("0.05"), margin_rate=D("0.2"), tax_rate=D("0.08"), additional_fixed_fees=D("100"))
            if original_get_side_effect: return original_get_side_effect(model, pk)
            return None
        mock_session.get.side_effect = get_side_effect_for_quote
    
        updated_quote = quote_process_service.update_quote_ui_state(quote_id, new_ui_state)

        assert updated_quote.ui_state == new_ui_state
        mock_session.add.assert_called_with(mock_quote)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_with(mock_quote)
        assert mock_quote.ui_state == new_ui_state

    def test_update_quote_ui_state_quote_not_found(self, quote_process_service: QuoteProcessService, mock_session: MagicMock):
        mock_session.get.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            quote_process_service.update_quote_ui_state(99, "some_state")
        assert exc_info.value.status_code == 404

    def test_set_quote_status_success(self, quote_process_service: QuoteProcessService, mock_session: MagicMock, D_fixture):
        D = D_fixture
        quote_id = 1
        new_status = "finalized"
        mock_quote = Quote(id=quote_id, name="Test Quote", status="calculated", quote_config_id=1, quote_type=QuoteType.FENCE_PROJECT)

        original_get_side_effect = mock_session.get.side_effect
        def get_side_effect_for_quote(model, pk):
            if model == Quote and pk == quote_id: return mock_quote
            if model == QuoteConfig and pk == 1: 
                return QuoteConfig(id=1, name="Default Config", sales_commission_rate=D("0.1"), franchise_fee_rate=D("0.05"), margin_rate=D("0.2"), tax_rate=D("0.08"), additional_fixed_fees=D("100"))
            if original_get_side_effect: return original_get_side_effect(model, pk)
            return None
        mock_session.get.side_effect = get_side_effect_for_quote

        updated_quote = quote_process_service.set_quote_status(quote_id, new_status)
        
        assert updated_quote.status == new_status
        mock_session.add.assert_called_with(mock_quote)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_with(mock_quote)
        assert mock_quote.status == new_status

    def test_set_quote_status_quote_not_found(self, quote_process_service: QuoteProcessService, mock_session: MagicMock):
        mock_session.get.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            quote_process_service.set_quote_status(99, "finalized")
        assert exc_info.value.status_code == 404

    def test_get_quotes_pagination(self, quote_process_service: QuoteProcessService, mock_session: MagicMock):
        mock_quotes_page = [
            Quote(id=1, name="Quote 1", status="draft", quote_type=QuoteType.FENCE_PROJECT, updated_at=datetime.now(timezone.utc), quote_config_id=1),
            Quote(id=2, name="Quote 2", status="draft", quote_type=QuoteType.FENCE_PROJECT, updated_at=datetime.now(timezone.utc), quote_config_id=1)
        ]
        
        mock_exec_result = MagicMock()
        mock_exec_result.all.return_value = mock_quotes_page
        mock_session.exec.side_effect = [mock_exec_result]

        offset = 10
        limit = 2
        result = quote_process_service.get_quotes(offset=offset, limit=limit)

        assert len(result) == 2
        mock_session.exec.assert_called_once()
        called_statement = mock_session.exec.call_args[0][0]
        assert called_statement._offset_clause is not None
        assert called_statement._limit_clause is not None
